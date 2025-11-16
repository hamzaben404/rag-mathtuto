import json
import os
from pathlib import Path
from typing import List, Dict

from meilisearch import Client


MEILI_HOST = os.environ.get("MEILI_HOST", "http://localhost:7700")
MEILI_API_KEY = os.environ.get("MEILI_API_KEY")  # must be set
MEILI_INDEX = "mathtuto_math_chunks_v1"


def load_chunks(jsonl_path: Path) -> List[Dict]:
    chunks: List[Dict] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def ensure_index(client: Client, index_name: str):
    """
    Make sure the index exists, then configure its settings.
    Compatible with newer Meilisearch Python client.
    """
    index = client.index(index_name)

    # Try to create the index; if it already exists, ignore the error.
    try:
        print(f"[Meili] Creating index '{index_name}' with primaryKey='id' (if not exists)...")
        client.create_index(uid=index_name, options={"primaryKey": "id"})
    except Exception:
        print(f"[Meili] Index '{index_name}' probably already exists.")

    # Now configure settings on the index
    print("[Meili] Updating index settings...")
    index.update_settings({
        "searchableAttributes": [
            "title",
            "summary",
            "body",
        ],
        "filterableAttributes": [
            "chapter",
            "part",
            "subchapter",
            "concept",
            "content_kind",
            "level",
            "track",
            "lang",
            "tags",
            "has_formula",
        ],
        "sortableAttributes": [
            "order_in_section",
        ],
        "synonyms": {
            "derivee": ["dérivée", "derivees", "dérivées"],
            "dérivée": ["derivee", "derivees", "dérivées"],
            "limite": ["limites"],
            "limites": ["limite"],
            "negation": ["négation"],
            "négation": ["negation"],
            "equivalence": ["équivalence"],
            "équivalence": ["equivalence"],
            "propostion": ["proposition"],
            "proposition": ["propostion"],
        }
    })
    print("[Meili] Settings updated.")
    return index


def prepare_documents(chunks: List[Dict]) -> List[Dict]:
    docs: List[Dict] = []
    for ch in chunks:
        doc = {
            # primary key
            "id": ch["id"],

            # text fields
            "title": ch.get("title", ""),
            "summary": ch.get("summary", ""),
            "body": ch.get("body", ""),

            # core metadata
            "chapter": ch.get("chapter"),
            "part": ch.get("part"),
            "subchapter": ch.get("subchapter"),
            "concept": ch.get("concept"),
            "content_kind": ch.get("content_kind"),
            "level": ch.get("level"),
            "track": ch.get("track"),
            "lang": ch.get("lang"),
            "tags": ch.get("tags", []),

            # extra metadata (optional but useful)
            "has_formula": ch.get("has_formula", False),
            "source_file": ch.get("source_file"),
            "section_number": ch.get("section_number"),
            "subsection_code": ch.get("subsection_code"),
            "order_in_section": ch.get("order_in_section", 0),
        }
        docs.append(doc)
    return docs


def ingest_meilisearch():
    if MEILI_API_KEY is None:
        raise SystemExit("MEILI_API_KEY not set in environment. Export it before running.")

    project_root = Path(__file__).resolve().parents[1]
    chunks_path = project_root / "data" / "logic" / "logic_chunks_v1.jsonl"

    if not chunks_path.exists():
        raise SystemExit(f"Chunks file not found: {chunks_path}")

    chunks = load_chunks(chunks_path)
    print(f"[Main] Loaded {len(chunks)} chunks from {chunks_path}")

    docs = prepare_documents(chunks)
    print(f"[Main] Prepared {len(docs)} documents for Meilisearch.")

    client = Client(MEILI_HOST, MEILI_API_KEY)
    index = ensure_index(client, MEILI_INDEX)

    print("[Meili] Adding documents...")
    task = index.add_documents(docs)
    # TaskInfo object → use attribute, not dict
    print(f"[Meili] Add documents task UID: {task.task_uid}")

    # Wait until indexed before searching
    client.wait_for_task(task.task_uid)
    print("[Meili] Documents indexed.")


def quick_test_search():
    """
    Simple lexical search test:
    'C'est quoi une proposition logique ?'
    Only on cours (no exercises).
    """
    if MEILI_API_KEY is None:
        raise SystemExit("MEILI_API_KEY not set in environment.")

    client = Client(MEILI_HOST, MEILI_API_KEY)
    index = client.index(MEILI_INDEX)

    query = "C'est quoi une proposition logique ?"
    print(f"[Test] Query: {query}")

    res = index.search(
        query,
        {
            "limit": 5,
            "filter": [
                'level = "1BAC"',
                'track = "SM"',
                'chapter = "Notion de logique"',
                'content_kind != "exercise"',
            ],
        },
    )

    hits = res.get("hits", [])
    print(f"[Test] Got {len(hits)} hits.")
    for i, doc in enumerate(hits, start=1):
        print(f"\n--- Hit #{i} ---")
        print("id:   ", doc.get("id"))
        print("title:", doc.get("title"))
        print("kind: ", doc.get("content_kind"))
        body_preview = (doc.get("body") or "").replace("\n", " ")
        if len(body_preview) > 200:
            body_preview = body_preview[:200] + "..."
        print("body:", body_preview)


def main():
    ingest_meilisearch()
    quick_test_search()



if __name__ == "__main__":
    main()
