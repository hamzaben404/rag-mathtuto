# src/retrieval_service.py

import os
import time
from typing import List, Dict, Any

import numpy as np
from meilisearch import Client as MeiliClient
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

import google.generativeai as genai
import cohere

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

# Gemini embedding
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_MODEL = os.getenv(
    "GEMINI_EMBED_MODEL", "models/text-embedding-004"
)

# Cohere reranker
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_RERANK_MODEL = os.getenv(
    "COHERE_RERANK_MODEL", "rerank-multilingual-v3.0"
)

# Meilisearch
MEILI_HOST = os.getenv("MEILI_HOST", "http://localhost:7700")
MEILI_API_KEY = os.getenv("MEILI_API_KEY", "CHANGE_ME_STRONG_KEY")
MEILI_INDEX = "mathtuto_math_chunks_v3"

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "mathtuto_math_chunks_v3"

# Retrieval sizes
MEILI_LIMIT = 10
QDRANT_LIMIT = 20

# ---------------------------------------------------------
# GLOBAL SINGLETONS (lazy loaded)
# ---------------------------------------------------------

_meili_client: MeiliClient | None = None
_qdrant_client: QdrantClient | None = None
_gemini_configured = False
_cohere_client: cohere.Client | None = None


def _configure_gemini():
    global _gemini_configured
    if _gemini_configured:
        return
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=GEMINI_API_KEY)
    _gemini_configured = True
    print("[Hybrid] Gemini configured for embeddings.")


def _get_query_embedding(question: str) -> np.ndarray:
    """
    Use Gemini embedding model to encode the user question.
    """
    _configure_gemini()
    # Prefix as query to align with passage embeddings
    content = f"query: {question}"
    resp = genai.embed_content(
        model=GEMINI_EMBED_MODEL,
        content=content,
    )
    emb = resp["embedding"]
    return np.array(emb, dtype=np.float32)


def get_meili_client() -> MeiliClient:
    global _meili_client
    if _meili_client is None:
        _meili_client = MeiliClient(MEILI_HOST, MEILI_API_KEY)
    return _meili_client


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _qdrant_client


def get_cohere_client() -> cohere.Client:
    global _cohere_client
    if _cohere_client is None:
        if not COHERE_API_KEY:
            raise RuntimeError("COHERE_API_KEY is not set.")
        _cohere_client = cohere.Client(api_key=COHERE_API_KEY)
        print("[Rerank] Cohere client initialized.")
    return _cohere_client


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _normalize_tag(ch: Dict[str, Any]) -> str:
    """
    Decide tag for the chunk: [OFFICIEL] or [COACH] or [SOURCE].
    Uses source_tag if present; falls back to kind.
    """
    tag = ch.get("source_tag")
    kind = ch.get("kind")
    if tag in ("[OFFICIEL]", "[COACH]"):
        return tag
    if kind == "official":
        return "[OFFICIEL]"
    if kind == "intuition":
        return "[COACH]"
    return "[SOURCE]"


def _build_candidate_from_meili(hit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": hit.get("id"),
        "title": hit.get("title"),
        "body": hit.get("body"),
        "kind": hit.get("kind"),
        "source_tag": hit.get("source_tag"),
        "level": hit.get("level"),
        "track": hit.get("track"),
        "source_file": hit.get("source_file"),
        "chapter": hit.get("chapter"),
        "subchapter": hit.get("subchapter"),
        "concept": hit.get("concept"),
    }


def _build_candidate_from_qdrant(res: qmodels.ScoredPoint) -> Dict[str, Any]:
    p = res.payload or {}
    return {
        "id": p.get("chunk_id"),
        "title": p.get("title"),
        "body": p.get("body"),
        "kind": p.get("kind"),
        "source_tag": p.get("source_tag"),
        "level": p.get("level"),
        "track": p.get("track"),
        "source_file": p.get("source_file"),
        "chapter": p.get("chapter"),
        "subchapter": p.get("subchapter"),
        "concept": p.get("concept"),
    }


# ---------------------------------------------------------
# CORE HYBRID + RERANKING
# ---------------------------------------------------------

def hybrid_retrieve(
    question: str,
    level: str = "1BAC",
    track: str = "SM",
    max_chunks: int = 6,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval:
    - Meilisearch keyword search
    - Qdrant vector search (Gemini embeddings)
    - Cohere rerank over fused candidates
    """
    total_start = time.time()
    print(f"\n⏱️ [Start] Hybrid Retrieval for: '{question}'")

    # ------------------------
    # 1) Meilisearch (keyword)
    # ------------------------
    t_start = time.time()
    meili_client = get_meili_client()
    index = meili_client.index(MEILI_INDEX)

    meili_res = index.search(
        question,
        {
            "limit": MEILI_LIMIT,
        },
    )
    meili_hits = meili_res.get("hits", [])
    print(
        f"⏱️ [Meili] Search took {time.time() - t_start:.4f}s "
        f"(Hits: {len(meili_hits)})"
    )

    # ------------------------
    # 2) Query Embedding (Gemini)
    # ------------------------
    t_start = time.time()
    query_vec = _get_query_embedding(question)
    print(
        f"⏱️ [Embedding] Gemini encoding took {time.time() - t_start:.4f}s"
    )

    # ------------------------
    # 3) Qdrant (vector search)
    # ------------------------
    t_start = time.time()
    q_client = get_qdrant_client()

    q_search_result = q_client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vec.tolist(),
        limit=QDRANT_LIMIT,
        with_payload=True,
    )
    q_res = q_search_result.points
    print(
        f"⏱️ [Qdrant] Search took {time.time() - t_start:.4f}s "
        f"(Hits: {len(q_res)})"
    )

    # ------------------------
    # 4) Fusion (simple score fusion)
    # ------------------------
    candidates: Dict[str, Dict[str, Any]] = {}

    for rank, hit in enumerate(meili_hits):
        cid = str(hit.get("id"))
        base = _build_candidate_from_meili(hit)
        base["meili_rank"] = rank
        base["meili_score"] = 1.0 / (1.0 + rank)
        candidates[cid] = base

    for rank, res in enumerate(q_res):
        payload = res.payload or {}
        cid = str(payload.get("chunk_id"))
        if cid not in candidates:
            base = _build_candidate_from_qdrant(res)
            candidates[cid] = base
        candidates[cid]["qdrant_rank"] = rank
        candidates[cid]["qdrant_score"] = 1.0 / (1.0 + rank)
        candidates[cid]["qdrant_raw"] = float(res.score)

    fused_list: List[Dict[str, Any]] = []
    for cid, cand in candidates.items():
        m = cand.get("meili_score", 0.0)
        v = cand.get("qdrant_score", 0.0)
        cand["fused_score"] = 0.5 * m + 0.5 * v
        fused_list.append(cand)

    fused_list.sort(key=lambda c: c["fused_score"], reverse=True)

    # ------------------------
    # 5) Cohere Reranking
    # ------------------------
    t_start = time.time()
    print(
        f"⏱️ [Rerank] Using Cohere model '{COHERE_RERANK_MODEL}' "
        "to rerank fused candidates..."
    )

    rerank_top_n = min(len(fused_list), max_chunks * 4)
    initial_candidates = fused_list[:rerank_top_n]

    if initial_candidates:
        co = get_cohere_client()

        documents = []
        for cand in initial_candidates:
            title = cand.get("title") or ""
            body = cand.get("body") or ""
            text = (title + "\n\n" + body).strip()
            documents.append(text if text else "(vide)")

        # Cohere rerank call
        rerank_resp = co.rerank(
            model=COHERE_RERANK_MODEL,
            query=question,
            documents=documents,
            top_n=rerank_top_n,
        )

        # Build index -> score map
        idx_to_score: Dict[int, float] = {}
        for r in rerank_resp.results:
            idx_to_score[r.index] = float(r.relevance_score)

        for idx, cand in enumerate(initial_candidates):
            cand["rerank_score"] = idx_to_score.get(idx, 0.0)

        # Sort by rerank_score
        initial_candidates.sort(
            key=lambda c: c.get("rerank_score", 0.0), reverse=True
        )

    print(f"⏱️ [Rerank] Process took {time.time() - t_start:.4f}s")
    print(f"⏱️ [Total] Hybrid Retrieval took {time.time() - total_start:.4f}s\n")

    return initial_candidates[:max_chunks]


# ---------------------------------------------------------
# CONTEXT BUILDER FOR THE PROMPT
# ---------------------------------------------------------

def build_context_text(chunks: List[Dict[str, Any]]) -> str:
    """
    Build the context text to inject into the LLM prompt.
    Each chunk is clearly labeled as [OFFICIEL] or [COACH].
    """
    parts = []
    for i, ch in enumerate(chunks, start=1):
        tag = _normalize_tag(ch)
        title = ch.get("title") or ""
        body = ch.get("body") or ""
        header = f"Source {i} {tag} — {title}".strip()
        block = f"{header}\n{body}".strip()
        parts.append(block)

    return "\n\n---\n\n".join(parts)


def simplify_chunks_for_api(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return a light version of chunks to send back via FastAPI.
    """
    out = []
    for ch in chunks:
        out.append(
            {
                "id": ch.get("id"),
                "title": ch.get("title"),
                "kind": ch.get("kind"),
                "source_tag": _normalize_tag(ch),
                "subchapter": ch.get("subchapter"),
                "concept": ch.get("concept"),
            }
        )
    return out
