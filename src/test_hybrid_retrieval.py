import os
from typing import Dict, List, Tuple

from meilisearch import Client as MeiliClient
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ---------- CONFIG ----------

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")  # usually None locally
QDRANT_COLLECTION = "mathtuto_math_chunks_v1"

MEILI_HOST = os.environ.get("MEILI_HOST", "http://localhost:7700")
MEILI_API_KEY = os.environ.get("MEILI_API_KEY")

MEILI_INDEX = "mathtuto_math_chunks_v1"

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
RERANKER_NAME = "BAAI/bge-reranker-v2-m3"

K_LEX = 20
K_VEC = 20
RRF_K = 60  # Reciprocal Rank Fusion hyperparam
RERANK_TOP_K = 10  # how many fused candidates to rerank


# ---------- EMBEDDING MODEL ----------

def load_embed_model() -> SentenceTransformer:
    print(f"[Hybrid] Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return model


# ---------- RERANKER MODEL ----------

class Reranker:
    def __init__(self, model_name: str):
        print(f"[Reranker] Loading reranker: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        # device: use MPS on Mac if available, else CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        self.model.to(self.device)
        self.model.eval()

    def score(self, query: str, documents: List[str]) -> List[float]:
        """
        Score a list of documents for a single query.
        Higher = more relevant.
        """
        # bge-reranker expects pairs (query, doc)
        pairs = [(query, doc) for doc in documents]

        with torch.no_grad():
            encoded = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            outputs = self.model(**encoded)
            # shape: [batch_size, 1]
            scores = outputs.logits.squeeze(-1).detach().cpu().tolist()

        if isinstance(scores, float):
            scores = [scores]
        return scores


# ---------- FUSION ----------

def rrf_fusion(
    meili_hits: List[Dict],
    qdrant_hits: List[qmodels.ScoredPoint],
) -> List[Tuple[str, float, Dict]]:
    """
    Reciprocal Rank Fusion over Meili + Qdrant results.
    Returns list of (chunk_id, fused_score, payload) sorted by fused_score desc.
    """
    scores: Dict[str, float] = {}
    payloads: Dict[str, Dict] = {}

    # Meili: id field is our logical chunk_id
    for rank, doc in enumerate(meili_hits, start=1):
        cid = doc.get("id")
        if cid is None:
            continue
        payloads.setdefault(cid, {})
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)

    # Qdrant: we stored original id in payload["chunk_id"]
    for rank, sp in enumerate(qdrant_hits, start=1):
        pl = sp.payload or {}
        cid = pl.get("chunk_id")
        if cid is None:
            continue
        payloads[cid] = pl
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)

    fused = [(cid, scores[cid], payloads[cid]) for cid in scores.keys()]
    fused.sort(key=lambda x: x[1], reverse=True)
    return fused


# ---------- RETRIEVAL FROM EACH ENGINE ----------

def search_meili(query: str) -> List[Dict]:
    if MEILI_API_KEY is None:
        raise SystemExit("MEILI_API_KEY not set.")

    client = MeiliClient(MEILI_HOST, MEILI_API_KEY)
    index = client.index(MEILI_INDEX)

    res = index.search(
        query,
        {
            "limit": K_LEX,
            "filter": [
                'level = "1BAC"',
                'track = "SM"',
                'chapter = "Notion de logique"',
                'content_kind != "exercise"',
            ],
        },
    )
    hits = res.get("hits", [])
    print(f"[Meili] Got {len(hits)} hits.")
    return hits


def search_qdrant(model: SentenceTransformer, query: str) -> List[qmodels.ScoredPoint]:
    text = "query: " + query
    vec = model.encode([text], convert_to_numpy=True)[0]

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    flt = qmodels.Filter(
        must=[
            qmodels.FieldCondition(
                key="level",
                match=qmodels.MatchValue(value="1BAC"),
            ),
            qmodels.FieldCondition(
                key="track",
                match=qmodels.MatchValue(value="SM"),
            ),
            qmodels.FieldCondition(
                key="chapter",
                match=qmodels.MatchValue(value="Notion de logique"),
            ),
        ],
        must_not=[
            qmodels.FieldCondition(
                key="content_kind",
                match=qmodels.MatchValue(value="exercise"),
            )
        ],
    )

    res = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vec.tolist(),
        limit=K_VEC,
        query_filter=flt,
        with_payload=True,
    )
    print(f"[Qdrant] Got {len(res)} hits.")
    return res


# ---------- PIPELINE: HYBRID + RERANK ----------

def run_query(query: str, top_n: int = 5):
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    if MEILI_API_KEY is None:
        raise SystemExit("MEILI_API_KEY not set. Export MEILI_API_KEY before running.")

    embed_model = load_embed_model()
    reranker = Reranker(RERANKER_NAME)

    meili_hits = search_meili(query)
    qdrant_hits = search_qdrant(embed_model, query)

    fused = rrf_fusion(meili_hits, qdrant_hits)
    print(f"[Hybrid] Fused results: {len(fused)} unique chunks.")

    # Take top RERANK_TOP_K fused candidates and rerank them
    candidates = fused[:RERANK_TOP_K]
    docs_text = [
        (payload.get("body") or "") for (_, _, payload) in candidates
    ]
    rerank_scores = reranker.score(query, docs_text)

    # attach rerank scores and sort
    scored_final = []
    for (cid, fused_score, payload), rscore in zip(candidates, rerank_scores):
        scored_final.append((cid, fused_score, rscore, payload))

    scored_final.sort(key=lambda x: x[2], reverse=True)  # sort by reranker score desc

    for i, (cid, fused_score, rscore, payload) in enumerate(scored_final[:top_n], start=1):
        title = payload.get("title") or ""
        content_kind = payload.get("content_kind")
        subchapter = payload.get("subchapter")
        concept = payload.get("concept")
        body = (payload.get("body") or "").replace("\n", " ")
        if len(body) > 260:
            body = body[:260] + "..."

        print(f"\n--- Result #{i} ---")
        print(f"id:          {cid}")
        print(f"fused_score: {fused_score:.6f}")
        print(f"rerank:      {rscore:.6f}")
        print(f"kind:        {content_kind}")
        print(f"subchapter:  {subchapter}")
        print(f"concept:     {concept}")
        print(f"title:       {title}")
        print(f"body:        {body}")


def main():
    queries = [
        "C'est quoi une proposition logique ?",
        "Explique le rôle du quantificateur ∀.",
        "C'est quoi une loi de Morgan ?",
        "Explique le raisonnement par contraposée.",
        "Explique le principe du raisonnement par récurrence.",
    ]

    for q in queries:
        run_query(q, top_n=5)


if __name__ == "__main__":
    main()
