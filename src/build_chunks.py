import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional


# --------- Small helpers ---------

def slugify(text: str) -> str:
    """
    Turn a label into a filesystem/db-friendly slug.
    """
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "na"


def normalize_heading(h: str) -> str:
    """
    Lowercase heading and strip spaces, keep accents.
    """
    return h.strip().lower()


# --------- Core parser for one file ---------

def parse_markdown_file(path: Path) -> List[Dict]:
    """
    Read one .md file and produce a list of chunk dicts
    following our design.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Static info (for now)
    level = "1BAC"
    track = "SM"
    chapter = "Notion de logique"
    lang = "fr"

    # Infer part from filename or from content
    part = "Partie 1"
    if "partie-2" in path.name.lower() or "partie 2" in text.lower():
        part = "Partie 2"

    current_section_number: Optional[str] = None   # I, II, III, V...
    current_subchapter: Optional[str] = None       # "Proposition - fonction propositionnelle"
    current_concept: Optional[str] = None          # "Négation d'une proposition", etc.
    subsection_code: Optional[str] = None          # "3-1", "5-3", ...

    chunks: List[Dict] = []
    current_chunk: Optional[Dict] = None
    chunk_counter = 0

    def flush_chunk():
        """
        Save the current chunk dict if it has non-empty body.
        """
        nonlocal current_chunk, chunk_counter, chunks

        if current_chunk is None:
            return

        body_text = current_chunk.get("body", "").strip()
        if not body_text:
            current_chunk = None
            return

        chunk_counter += 1

        # Build stable-ish ID
        chap_code = "logic"
        sec_code = current_section_number or "na"
        concept_name = current_chunk.get("concept") or current_concept or current_subchapter or "Notion de logique"
        conc_code = slugify(concept_name)
        cid = f"math_1bac_sm_{chap_code}_{sec_code}_{conc_code}_{chunk_counter:02d}"
        current_chunk["id"] = cid

        # Simple summary (first ~200 chars)
        if not current_chunk.get("summary"):
            snippet = body_text.replace("\n", " ")
            current_chunk["summary"] = (snippet[:200] + "...") if len(snippet) > 200 else snippet

        # has_formula: any math-ish symbol or $
        if any(sym in body_text for sym in ["¬", "∧", "∨", "⇒", "⇔", "∀", "∃", "$"]):
            current_chunk["has_formula"] = True
        else:
            current_chunk["has_formula"] = False

        chunks.append(current_chunk)
        current_chunk = None

    def start_chunk(kind: str, heading_text: str):
        """
        Start a new chunk given a content_kind and heading text.
        Flush the previous one if needed.
        """
        nonlocal current_chunk, current_subchapter, current_concept, current_section_number, subsection_code

        flush_chunk()

        title = heading_text.strip()
        lower = normalize_heading(title)

        # Enrich very generic headings with the concept or subchapter
        concept_title = current_concept or current_subchapter or "Notion de logique"

        if "définition" in lower and ":" not in lower:
            title = f"Définition : {concept_title}"
        elif "applications" in lower:
            title = f"Applications : {concept_title}"
        elif "remarques" in lower:
            title = f"Remarques : {concept_title}"

        tags = ["logique"]
        if current_concept:
            tags.append(slugify(current_concept))

        current_chunk = {
            "title": title,
            "body": "",
            "content_kind": kind,               # definition / remark / proposition / exercise / course_example / reasoning_pattern
            "level": level,
            "track": track,
            "chapter": chapter,
            "part": part,
            "subchapter": current_subchapter,
            "concept": current_concept,
            "section_number": current_section_number,
            "subsection_code": subsection_code,
            "lang": lang,
            "source_file": path.name,
            "order_in_section": 0,             # filled latter
            "tags": tags,
        }

    # ---- main scan ----
    for line in lines:
        stripped = line.strip()

        # Ignore global empty lines (just preserve some spacing inside chunk)
        if not stripped:
            if current_chunk is not None:
                current_chunk["body"] += "\n"
            continue

        # Headings: start with "# "
        if stripped.startswith("# "):
            heading = stripped[2:].strip()
            lower_h = normalize_heading(heading)

            # Ignore very top-level non-course headings
            if any(kw in lower_h for kw in ["alloschool", "mathématiques", "sommaire"]):
                continue

            # 1) Section detection: I- ..., II- ..., III- ..., V- ...
            m_sec = re.match(r"([IVX]+)\s*-\s*(.+)", heading)
            if m_sec:
                flush_chunk()
                current_section_number = m_sec.group(1)
                current_subchapter = m_sec.group(2).strip()
                current_concept = None
                subsection_code = None
                continue

            # 2) Concept detection: "3-1/ Négation ...", "5-3/ Raisonnement par contraposée"
            m_sub = re.match(r"(\d+-\d+)\s*/\s*(.+)", heading)
            if m_sub:
                flush_chunk()
                subsection_code = m_sub.group(1)
                current_concept = m_sub.group(2).strip()
                continue

            # 3) Chunk-type headings
            if "définition" in lower_h:
                start_chunk("definition", heading)
                continue
            if "applications" in lower_h:
                # All "Applications" are exercises for now
                start_chunk("exercise", heading)
                continue
            if "remarques" in lower_h:
                start_chunk("remark", heading)
                continue
            if "proposition" in lower_h:
                start_chunk("proposition", heading)
                continue
            if "raisonnement" in lower_h:
                start_chunk("reasoning_pattern", heading)
                continue

            # 4) fallback: any other heading → treat as course_example
            start_chunk("course_example", heading)
            continue

        # Non-heading text
        if current_chunk is None:
            # If we already know the subchapter or concept, start a generic course_example chunk
            if current_subchapter or current_concept:
                start_chunk("course_example", current_concept or current_subchapter or "Notion de logique")
            else:
                # Still in preface / useless area
                continue

        # Append line to the current chunk body
        current_chunk["body"] += stripped + "\n"

    # End of file: flush last chunk
    flush_chunk()

    # Assign order_in_section (simple increasing order per file)
    for idx, ch in enumerate(chunks, start=1):
        ch["order_in_section"] = idx

    return chunks


# --------- Entry point: gather all .md in data/logic and write JSONL ---------

def main():
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data" / "logic"

    if not data_dir.exists():
        raise SystemExit(f"data/logic directory not found at: {data_dir}")

    md_files = sorted(data_dir.glob("*.md"))
    if not md_files:
        raise SystemExit(f"No .md files found in {data_dir}")

    all_chunks: List[Dict] = []

    for path in md_files:
        print(f"Parsing: {path.name}")
        chunks = parse_markdown_file(path)
        print(f"  -> {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"Total chunks: {len(all_chunks)}")

    # Output JSONL
    out_path = data_dir / "logic_chunks_v1.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")

    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
