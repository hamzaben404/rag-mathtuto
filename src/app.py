# src/app.py
from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from .retrieval_service import HybridRetriever, RetrievedChunk
from .llm_service import LLMService


# ------------------------------------------------------------
# Pydantic models (request / response)
# ------------------------------------------------------------
class ExplainRequest(BaseModel):
    question: str
    level: str | None = "1BAC"
    track: str | None = "SM"
    max_chunks: int | None = 4


class UsedChunk(BaseModel):
    id: str
    title: str
    kind: str | None = None
    subchapter: str | None = None
    concept: str | None = None


class ExplainResponse(BaseModel):
    answer: str
    used_chunks: List[UsedChunk]


# ------------------------------------------------------------
# Initialize services (retriever + LLM)
# ------------------------------------------------------------
MEILI_HOST = os.getenv("MEILI_HOST", "http://localhost:7700")
MEILI_API_KEY = os.getenv("MEILI_API_KEY", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# This should match your collection/index name
INDEX_NAME = "mathtuto_math_chunks_v1"

retriever = HybridRetriever(
    meili_host=MEILI_HOST,
    meili_api_key=MEILI_API_KEY,
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    index_name=INDEX_NAME,
)

llm_service = LLMService()  # uses GEMINI_API_KEY from env


# ------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------
app = FastAPI(
    title="MathTuto RAG API",
    description="RAG-powered explanation service for 1BAC Science Math (logic, etc.)",
    version="0.1.0",
)


# Healthcheck
@app.get("/health")
def health():
    return {"status": "ok"}


# Main endpoint
@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest) -> ExplainResponse:
    # 1) Retrieve relevant chunks
    top_k = req.max_chunks or 4
    chunks: list[RetrievedChunk] = retriever.retrieve(req.question, top_k=top_k)

    # 2) Generate explanation with Gemini
    answer = llm_service.generate_explanation(
        question=req.question,
        chunks=chunks,
        level=req.level or "1BAC",
        track=req.track or "SM",
    )

    # 3) Build used_chunks for the response
    used = [
        UsedChunk(
            id=c.id,
            title=c.title,
            kind=c.kind,
            subchapter=c.subchapter,
            concept=c.concept,
        )
        for c in chunks
    ]

    return ExplainResponse(answer=answer, used_chunks=used)
