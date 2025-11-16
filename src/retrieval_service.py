# src/retrieval_service.py
import os
from typing import List, Dict, Any
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from meilisearch import Client as MeiliClient
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch


# ----------------------------------------------------
# Dataclass for a retrieved chunk
# ----------------------------------------------------
@dataclass
class RetrievedChunk:
    id: str
    title: str
    body: str
    kind: str
    subchapter: str
    concept: str
    fused_score: float
    rerank_score: float


# ----------------------------------------------------
# Hybrid Retriever (Meili + Qdrant + Reranker)
# ----------------------------------------------------
class HybridRetriever:
    def __init__(
        self,
        meili_host: str,
        meili_api_key: str,
        qdrant_url: str,
        qdrant_api_key: str = None,
        index_name: str = "mathtuto_math_chunks_v1",
        embed_model: str = "intfloat/multilingual-e5-large",
        reranker_model: str = "BAAI/bge-reranker-v2-m3",
        meili_k: int = 10,
        qdrant_k: int = 10,
    ):
        self.index_name = index_name
        self.meili_k = meili_k
        self.qdrant_k = qdrant_k

        # -------------------------------
        # Load embedding model
        # -------------------------------
        print("[Hybrid] Loading embedding model:", embed_model)
        self.embedder = SentenceTransformer(embed_model)

        # -------------------------------
        # Load reranker
        # -------------------------------
        print("[Hybrid] Loading reranker:", reranker_model)
        self.reranker_tokenizer = AutoTokenizer.from_pretrained(reranker_model)
        self.reranker_model = AutoModelForSequenceClassification.from_pretrained(
            reranker_model
        )

        # -------------------------------
        # Meilisearch client
        # -------------------------------
        self.meili = MeiliClient(meili_host, meili_api_key)

        # -------------------------------
        # Qdrant client
        # -------------------------------
        self.qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    # ----------------------------------------------------
    # Lexical search: Meilisearch
    # ----------------------------------------------------
    def meili_search(self, query: str) -> List[Dict]:
        index = self.meili.index(self.index_name)

        res = index.search(
            query,
            {
                "limit": self.meili_k,
                "attributesToHighlight": [],
                "showRankingScore": True,
            },
        )

        docs = []
        for hit in res.get("hits", []):
            docs.append(
                {
                    "id": hit["id"],
                    "title": hit.get("title", ""),
                    "body": hit.get("body", ""),
                    "kind": hit.get("kind", ""),
                    "subchapter": hit.get("subchapter", ""),
                    "concept": hit.get("concept", ""),
                    "score": hit.get("_rankingScore", 1.0),
                }
            )
        return docs

    # ----------------------------------------------------
    # Vector search: Qdrant
    # ----------------------------------------------------
    def qdrant_search(self, query: str) -> List[Dict]:
        query_vec = self.embedder.encode(query).tolist()

        res = self.qdrant.search(
            collection_name=self.index_name,
            query_vector=query_vec,
            limit=self.qdrant_k,
        )

        docs = []
        for pt in res:
            payload = pt.payload or {}
            docs.append(
                {
                    "id": payload.get("id"),
                    "title": payload.get("title", ""),
                    "body": payload.get("body", ""),
                    "kind": payload.get("kind", ""),
                    "subchapter": payload.get("subchapter", ""),
                    "concept": payload.get("concept", ""),
                    "score": pt.score,
                }
            )
        return docs

    # ----------------------------------------------------
    # RRF Fusion (Reciprocal Rank Fusion)
    # ----------------------------------------------------
    def rrf_fusion(self, meili_docs: List[Dict], qdrant_docs: List[Dict]) -> List[Dict]:
        fused = {}
        k = 60  # constant

        # Meili contribution
        for rank, doc in enumerate(meili_docs, start=1):
            doc_id = doc["id"]
            fused.setdefault(doc_id, {"doc": doc, "score": 0})
            fused[doc_id]["score"] += 1 / (k + rank)

        # Qdrant contribution
        for rank, doc in enumerate(qdrant_docs, start=1):
            doc_id = doc["id"]
            fused.setdefault(doc_id, {"doc": doc, "score": 0})
            fused[doc_id]["score"] += 1 / (k + rank)

        out = []
        for doc_id, item in fused.items():
            d = item["doc"]
            d["fused_score"] = item["score"]
            out.append(d)

        # sort by fused score descending
        out = sorted(out, key=lambda x: x["fused_score"], reverse=True)
        return out

    # ----------------------------------------------------
    # Rerank with BGE-reranker
    # ----------------------------------------------------
    def rerank(self, query: str, docs: List[Dict]) -> List[RetrievedChunk]:
        pairs = [
            (query, d["title"] + "\n" + d["body"])
            for d in docs
        ]

        model_inputs = self.reranker_tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        )

        with torch.no_grad():
            outputs = self.reranker_model(**model_inputs)
            scores = outputs.logits.squeeze(-1).tolist()

        out = []
        for d, score in zip(docs, scores):
            out.append(
                RetrievedChunk(
                    id=d["id"],
                    title=d.get("title", ""),
                    body=d.get("body", ""),
                    kind=d.get("kind", ""),
                    subchapter=d.get("subchapter", ""),
                    concept=d.get("concept", ""),
                    fused_score=d.get("fused_score", 0),
                    rerank_score=float(score),
                )
            )

        # sort by rerank_score (higher = more relevant)
        out = sorted(out, key=lambda x: x.rerank_score, reverse=True)
        return out

    # ----------------------------------------------------
    # Main function: retrieve top-K results
    # ----------------------------------------------------
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        meili_docs = self.meili_search(query)
        qdrant_docs = self.qdrant_search(query)

        fused = self.rrf_fusion(meili_docs, qdrant_docs)

        reranked = self.rerank(query, fused)

        return reranked[:top_k]
