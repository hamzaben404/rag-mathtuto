import json
from pathlib import Path
from typing import List, Dict

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer


# ------------- CONFIG ------------- #

QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = None  # or "your_key" if you enable auth
QDRANT_COLLECTION = "mathtuto_math_chunks_v1"

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
BATCH_SIZE = 16


# ------------- IO HELPERS ------------- #

def load_chunks(jsonl_path: Path) -> List[Dict]:
    chunks: List[Dict] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


# ------------- QDRANT SETUP ------------- #

def ensure_collection(client: QdrantClient, collection_name: str, dim: int):
    """
    Create the collection if it doesn't exist yet.
    """
    collections = client.get_collections()
    existing = {c.name for c in collections.collections}
    if collection_name in existing:
        print(f"[Qdrant] Collection '{collection_name}' already exists.")
        return

    print(f"[Qdrant] Creating collection '{collection_name}' with dim={dim}...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(
            size=dim,
            distance=qmodels.Distance.COSINE,
        ),
    )
    print("[Qdrant] Collection created.")


# ------------- EMBEDDING + UPSERT ------------- #

def build_passage_text(chunk: Dict) -> str:
    """
    Build the text to embed for a chunk, using E5 'passage: ' prefix.
    """
    title = chunk.get("title", "").strip()
    body = chunk.get("body", "").strip()
    text = (title + ". " + body).strip()
    if not text:
        text = "Empty chunk."
    # E5 expects 'passage: ' for document embeddings
    return "passage: " + text


def embed_and_upsert(chunks: List[Dict]):
    # Load embedding model
    print(f"[Embed] Loading model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Inspect output dimension
    test_vec = model.encode(["passage: test"], convert_to_numpy=True)[0]
    dim = test_vec.shape[0]
    print(f"[Embed] Embedding dimension = {dim}")

    # Connect Qdrant
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    ensure_collection(client, QDRANT_COLLECTION, dim)

    # Prepare batched upload
    total = len(chunks)
    print(f"[Embed] Total chunks to embed: {total}")


    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = chunks[start:end]
        texts = [build_passage_text(ch) for ch in batch]

        # Embed
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        # Qdrant IDs must be int or UUID → use numeric IDs
        numeric_ids = list(range(start, end))

        payloads = []
        for ch in batch:
            # Preserve your original string ID in payload
            # (Qdrant will use numeric_ids as the real point IDs)
            payload = dict(ch)  # shallow copy
            payload["chunk_id"] = ch["id"]  # original id kept here
            payloads.append(payload)

        print(f"[Qdrant] Upserting points {start}–{end - 1}...")
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=qmodels.Batch(
                ids=numeric_ids,
                vectors=embeddings.tolist(),
                payloads=payloads,
            ),
        )

    print("[Embed] Done. All chunks upserted to Qdrant.")


# ------------- MAIN ------------- #

def main():
    project_root = Path(__file__).resolve().parents[1]
    chunks_path = project_root / "data" / "logic" / "logic_chunks_v1.jsonl"

    if not chunks_path.exists():
        raise SystemExit(f"Chunks file not found: {chunks_path}")

    chunks = load_chunks(chunks_path)
    print(f"[Main] Loaded {len(chunks)} chunks from {chunks_path}")

    embed_and_upsert(chunks)


if __name__ == "__main__":
    main()
