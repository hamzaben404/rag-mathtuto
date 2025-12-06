# src/app.py

from fastapi import FastAPI
from pydantic import BaseModel

from .llm_service import explain_math

app = FastAPI()


class ExplainRequest(BaseModel):
    question: str
    level: str = "1BAC"
    track: str = "SM"
    max_chunks: int = 6


class ExplainResponse(BaseModel):
    answer: str
    used_chunks: list


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    answer, used_chunks = explain_math(
        question=req.question,
        level=req.level,
        track=req.track,
        max_chunks=req.max_chunks,
    )
    return {"answer": answer, "used_chunks": used_chunks}
