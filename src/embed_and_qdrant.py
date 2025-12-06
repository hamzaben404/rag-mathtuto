# src/embed_and_qdrant.py

import json
import os
from pathlib import Path
from typing import List, Dict

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

import google.generativeai as genai

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

DATA_PATH = Path("data/logic/logic_chunks_v3.jsonl")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # None if not secured
COLLECTION_NAME = "mathtuto_math_chunks_v3"

# Gemini embedding model
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_MODEL = os.getenv(
    "GEMINI_EMBED_MODEL", "models/text-embedding-004"
)

BATCH_SIZE = 16  # how many chunks you embed per loop (API calls will still be per-text)


# ---------------------------------------------------------------------
# LOAD CHUNKS
# ---------------------------------------------------------------------

def load_chunks(path: Path) -> List[Dict]:
    chunks: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


# ---------------------------------------------------------------------
# GEMINI SETUP
# ---------------------------------------------------------------------

def configure_gemini():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")
    genai.configure(api_key=GEMINI_API_KEY)


def embed_text_gemini(text: str) -> np.ndarray:
    """
    Call Gemini embedding API for a single text.
    Returns a 1D numpy array.
    """
    # We prefix with "passage:" to be consistent with retrieval style
    content = f"passage: {text}"
    resp = genai.embed_content(
        model=GEMINI_EMBED_MODEL,
        content=content,
    )
    emb = resp["embedding"]
    return np.array(emb, dtype=np.float32)


# ---------------------------------------------------------------------
# QDRANT SETUP
# ---------------------------------------------------------------------

def recreate_collection(client: QdrantClient, dim: int):
    # Check if exists
    collections = [c.name for c in client.get_collections().collections]
    
    if COLLECTION_NAME in collections:
        print(f"[Qdrant] Collection '{COLLECTION_NAME}' exists. DELETING to update dimensions...")
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"[Qdrant] Old collection deleted.")

    print(f"[Qdrant] Creating collection '{COLLECTION_NAME}' with dim={dim}...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    print("[Qdrant] New collection created.")


# ---------------------------------------------------------------------
# EMBEDDING + UPSERT
# ---------------------------------------------------------------------

def embed_and_upsert(chunks: List[Dict]):
    configure_gemini()
    print("[Main] Using Gemini embedding model:", GEMINI_EMBED_MODEL)

    # Probe embedding dimension
    probe_vec = embed_text_gemini("test")
    dim = int(probe_vec.shape[0])
    print(f"[Embed] Embedding dimension = {dim}")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # CALL THE NEW RECREATE FUNCTION
    recreate_collection(client, dim)

    total = len(chunks)
    print(f"[Embed] Total chunks to embed: {total}")

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = chunks[start:end]

        vectors: List[np.ndarray] = []
        for ch in batch:
            title = ch.get("title", "") or ""
            body = ch.get("body", "") or ""
            full_text = f"{title}\n\n{body}".strip()
            if not full_text: full_text = "(vide)"

            vec = embed_text_gemini(full_text)
            vectors.append(vec)

        points: List[PointStruct] = []
        for i, (ch, vec) in enumerate(zip(batch, vectors)):
            point_id = start + i 
            payload = {
                "chunk_id": ch.get("id"),
                "title": ch.get("title"),
                "body": ch.get("body"),
                "kind": ch.get("kind"),
                "source_tag": ch.get("source_tag"),
                "level": ch.get("level"),
                "track": ch.get("track"),
                "source_file": ch.get("source_file"),
                "chapter": ch.get("chapter"),
                "subchapter": ch.get("subchapter"),
                "concept": ch.get("concept"),
            }
            points.append(PointStruct(id=point_id, vector=vec.tolist(), payload=payload))

        print(f"[Qdrant] Upserting points {start}–{end-1}...")
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    print("[Embed] Done. All chunks upserted to Qdrant.")

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    print(f"[Main] Loading chunks from {DATA_PATH} ...")
    chunks = load_chunks(DATA_PATH)
    print(f"[Main] Total chunks loaded: {len(chunks)}")
    embed_and_upsert(chunks)


if __name__ == "__main__":
    main()
