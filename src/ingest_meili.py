# src/ingest_meili.py
import json
import os
from pathlib import Path
from typing import List, Dict
from meilisearch import Client

DATA_PATH = Path("data/logic/logic_chunks_v3.jsonl")
MEILI_HOST = os.getenv("MEILI_HOST", "http://localhost:7700")
MEILI_API_KEY = os.getenv("MEILI_API_KEY", "CHANGE_ME_STRONG_KEY") # Ensure this matches your docker setup
INDEX_NAME = "mathtuto_math_chunks_v3"

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
# MEILISEARCH SETUP
# ---------------------------------------------------------------------
def ensure_index(client: Client, index_name: str):
    """Create index if it doesn't exist, otherwise return it."""
    
    # --- FIX START: Handle paginated response format ---
    response = client.get_indexes()
    
    indexes = []
    if isinstance(response, dict) and "results" in response:
        # Dictionary response (newer versions)
        indexes = response["results"]
    elif hasattr(response, "results"):
        # Object response (some versions)
        indexes = response.results
    else:
        # Direct list (older versions)
        indexes = response
    # --- FIX END ---

    existing_uids = [idx.uid for idx in indexes]

    if index_name in existing_uids:
        print(f"[Meili] Index '{index_name}' already exists.")
        return client.index(index_name)

    print(f"[Meili] Creating index '{index_name}' with primaryKey='id'...")
    client.create_index(index_name, {"primaryKey": "id"})
    return client.index(index_name)

def configure_index(index):
    """Configure searchable / filterable attributes for math logic chunks."""
    print("[Meili] Updating index settings...")
    index.update_searchable_attributes(
        [
            "title",
            "body",
            "kind",
            "source_tag",
            "chapter",
            "subchapter",
            "concept",
        ]
    )
    index.update_filterable_attributes(
        [
            "kind",
            "source_tag",
            "level",
            "track",
            "source_file",
        ]
    )
    print("[Meili] Settings updated.")

# ---------------------------------------------------------------------
# INGEST
# ---------------------------------------------------------------------
def prepare_documents(chunks: List[Dict]) -> List[Dict]:
    docs = []
    for ch in chunks:
        doc = {
            "id": ch.get("id"),             # string id from JSONL
            "title": ch.get("title"),
            "body": ch.get("body"),
            "kind": ch.get("kind"),
            "source_tag": ch.get("source_tag"),
            "level": ch.get("level"),
            "track": ch.get("track"),
            "source_file": ch.get("source_file"),
            # optional extras if you add them later:
            "chapter": ch.get("chapter"),
            "subchapter": ch.get("subchapter"),
            "concept": ch.get("concept"),
        }
        docs.append(doc)
    return docs

def ingest_meilisearch():
    chunks = load_chunks(DATA_PATH)
    print(f"[Main] Loaded {len(chunks)} chunks from {DATA_PATH}")

    docs = prepare_documents(chunks)
    print(f"[Main] Prepared {len(docs)} documents for Meilisearch.")

    client = Client(MEILI_HOST, MEILI_API_KEY)
    
    # This will now work correctly
    index = ensure_index(client, INDEX_NAME)
    
    configure_index(index)

    print("[Meili] Adding documents...")
    task = index.add_documents(docs)
    print(f"[Meili] Add documents task UID: {task.task_uid}")
    
    # Optionally wait for completion (blocking):
    client.wait_for_task(task.task_uid)
    print("[Meili] Documents indexed.")

    # Quick test query
    print("[Test] Query: 'proposition logique'")
    res = index.search("proposition logique", {"limit": 3})
    
    hits = res.get("hits", []) # Safety get
    print(f"[Test] Got {len(hits)} hits.")
    for i, hit in enumerate(hits, 1):
        print(f"--- Hit #{i} ---")
        print("id:   ", hit.get("id"))
        print("kind: ", hit.get("kind"))
        print("tag:  ", hit.get("source_tag"))
        print("title:", hit.get("title"))

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
if __name__ == "__main__":
    ingest_meilisearch()