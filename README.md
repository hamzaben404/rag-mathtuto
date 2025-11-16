# MathTutor RAG – 1BAC Science Math (Maroc)

Backend RAG service for a Math Tutor SAAS focused on **1ère année Bac Science Math (Maroc)**.
This microservice provides **guided explanations of the official math course**, starting with the chapter *Notion de logique*.

It uses **hybrid retrieval** (Meilisearch + Qdrant + reranker) and **LLM generation** (Gemini) to produce accurate, grounded explanations.

---

## Features

* **Hybrid Retrieval**

  * Lexical search (Meilisearch – BM25)
  * Dense semantic search (Qdrant + `intfloat/multilingual-e5-large`)
  * Fusion + Reranking (`BAAI/bge-reranker-v2-m3`)
* **RAG Generation**

  * LLM: **Gemini 2.5 Flash**
  * Custom system prompt: *prof de maths marocain, niveau 1BAC SM*
  * Always grounded in course chunks (no hallucinations)
* **FastAPI Microservice**

  * `/health` – health check
  * `/explain` – full RAG pipeline
* **Dockerized**

  * API container (`mathtuto-api`)
  * Infra: Meilisearch + Qdrant (docker-compose)

---

## Project Structure

```
rag-math-mathtuto/
├── src/
│   ├── app.py               # FastAPI entrypoint
│   ├── retrieval_service.py # Hybrid search logic
│   ├── llm_service.py       # Gemini wrapper
│   └── ...
│
├── data/
│   └── logic/
│       ├── *.md             # Markdown course files
│       └── logic_chunks_v1.jsonl
│
├── infra/
│   └── docker-compose.yml   # Meilisearch + Qdrant
│
├── docs/
│   └── DOCKER.md            # Full Docker instructions
│
├── requirements.txt
├── Dockerfile
├── .gitignore
└── LICENSE
```

---

## Quickstart (Local, No Docker)

### 1) Install environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start Meilisearch + Qdrant

```bash
cd infra
docker compose up -d
cd ..
```

### 3) Set environment variables

```bash
export GEMINI_API_KEY="YOUR_REAL_KEY"
export GEMINI_MODEL="gemini-2.5-flash"
export MEILI_HOST="http://localhost:7700"
export MEILI_API_KEY="CHANGE_ME_STRONG_KEY"
export QDRANT_URL="http://localhost:6333"
```

### 4) Run FastAPI

```bash
uvicorn src.app:app --reload --port 8000
```

### 5) Test

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST "http://127.0.0.1:8000/explain" \
  -H "Content-Type: application/json" \
  -d '{"question":"C\"est quoi une proposition logique ?","level":"1BAC","track":"SM","max_chunks":4}'
```

---

## Docker Usage

See **`docs/DOCKER.md`** for the full guide.

Short version:

```bash
# Start Meili + Qdrant
cd infra
docker compose up -d
cd ..

# Build API container
docker build -t mathtuto-api .

# Run API
docker run \
  --rm \
  -p 8000:8000 \
  --env-file .env \
  mathtuto-api
```

---

## Roadmap

* Add more chapters (fonctions, suites, géométrie…)
* Improve retrieval quality (query rewriting, filters)
* Add evaluation set (questions + ground truth)
* Integrate FastAPI backend with Next.js frontend (MathTutor SAAS)
* Add error handling + analytics
* Deploy API + Meili + Qdrant on cloud (Railway / Render / GCP)

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file.
