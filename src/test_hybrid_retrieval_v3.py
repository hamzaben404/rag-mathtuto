# src/test_hybrid_retrieval_v3.py

from retrieval_service import hybrid_retrieve, build_context_text, simplify_chunks_for_api

def run_one(query: str, max_chunks: int = 4):
    print("=" * 80)
    print("QUERY:", query)
    print("=" * 80)

    chunks = hybrid_retrieve(query, level="1BAC", track="SM", max_chunks=max_chunks)
    print(f"[Test] Got {len(chunks)} chunks after reranking.\n")

    for i, ch in enumerate(chunks, start=1):
        print(f"--- Result #{i} ---")
        print("id:         ", ch.get("id"))
        print("kind:       ", ch.get("kind"))
        print("source_tag: ", ch.get("source_tag"))
        print("title:      ", ch.get("title"))
        print("rerank:     ", ch.get("rerank_score", None))
        print()

    ctx = build_context_text(chunks)
    print("------------- CONTEXT TEXT -------------")
    print(ctx)
    print("------------- END CONTEXT -------------\n")

    simple = simplify_chunks_for_api(chunks)
    print("Used chunks (for API):")
    print(simple)
    print()


def main():
    queries = [
        "C'est quoi une proposition logique ?",
        "Explique le rôle du quantificateur ∀.",
        "C'est quoi une loi de Morgan ?",
        "Explique le raisonnement par contraposée.",
    ]
    for q in queries:
        run_one(q, max_chunks=4)


if __name__ == "__main__":
    main()
