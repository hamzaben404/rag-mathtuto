import os
import json
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path("data/logic")
OUTPUT_JSONL = DATA_DIR / "logic_chunks_v3.jsonl"


def detect_kind(filename: str) -> Dict[str, str]:
    """Assign layer type based on filename."""
    fn = filename.lower()
    if "cours" in fn:
        return {"kind": "official", "source_tag": "[OFFICIEL]"}
    if "intuition" in fn:
        return {"kind": "intuition", "source_tag": "[COACH]"}
    return {"kind": "unknown", "source_tag": "[SOURCE]"}


def load_markdown(path: Path) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def chunk_markdown(lines: List[str], filename: str, kind: str, source_tag: str) -> List[Dict]:
    chunks = []
    current_title = None
    current_body = []
    chunk_index = 0

    def save_chunk():
        nonlocal chunk_index, current_body, current_title
        if current_title and current_body:
            chunk_index += 1
            chunk = {
                "id": f"{filename.replace('.md','')}_chunk_{chunk_index}",
                "title": current_title.strip(),
                "body": "\n".join(current_body).strip(),
                "kind": kind,             # official OR intuition
                "source_tag": source_tag, # [OFFICIEL] or [COACH]
                "level": "1BAC",
                "track": "SM",
                "source_file": filename,
            }
            chunks.append(chunk)

    for line in lines:
        if line.startswith("#"):
            # New section starts → save previous chunk
            save_chunk()
            current_title = line.lstrip("# ").strip()
            current_body = []
        else:
            current_body.append(line)

    # Save last chunk
    save_chunk()

    return chunks


def build_all_chunks():
    all_chunks = []

    for file in sorted(DATA_DIR.glob("*.md")):
        meta = detect_kind(file.name)
        print(f"Processing {file.name}  ->  kind={meta['kind']}")

        lines = load_markdown(file)
        chunks = chunk_markdown(
            lines=lines,
            filename=file.name,
            kind=meta["kind"],
            source_tag=meta["source_tag"],
        )

        print(f"  → {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"Total: {len(all_chunks)} chunks")

    # Write JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
        for ch in all_chunks:
            out.write(json.dumps(ch, ensure_ascii=False) + "\n")

    print(f"Saved → {OUTPUT_JSONL}")


if __name__ == "__main__":
    build_all_chunks()
