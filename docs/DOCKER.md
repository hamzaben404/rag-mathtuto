## Docker setup – RAG MathTutor backend (v3)

Backend RAG pour le tuteur de maths **1ère Bac SM (Maroc)**.

Trois services principaux :

- **API** : microservice FastAPI (`mathtuto-api`)
- **Vector store** : Qdrant
- **Lexical search** : Meilisearch

Meilisearch et Qdrant tournent via `docker-compose` (dossier `infra/`).
L’API FastAPI tourne dans son propre conteneur Docker.

Le frontend (Next.js) appelle l’API sur :

`http://localhost:8000/explain`

---

### 1. Prérequis

- Docker + Docker Compose installés.
- Une clé API Google **Gemini**.
- Une clé API **Cohere** pour le reranker.

Déjà présents dans le repo :

- `infra/docker-compose.yml` (Meilisearch + Qdrant).
- `Dockerfile` (image de l’API).
- `requirements.txt`.

Structure simplifiée :

```text
rag-math-mathtuto/
│
├── src/
│   ├── app.py                 # FastAPI app (entrypoint)
│   ├── retrieval_service.py   # Hybrid retriever (Meili + Qdrant + Cohere)
│   ├── llm_service.py         # Gemini LLM wrapper
│   └── ...
│
├── data/
│   └── logic/
│       └── logic_chunks_v3.jsonl   # Chunks OFFICIEL / COACH
│
├── infra/
│   └── docker-compose.yml     # Meilisearch + Qdrant
│
├── docs/
│   └── DOCKER.md
│
├── Dockerfile                 # Image API
└── requirements.txt
```

---

### 2. Variables d’environnement

L’API a besoin des variables suivantes :

Obligatoires :

* `GEMINI_API_KEY` – clé Gemini.
* `MEILI_API_KEY` – clé Meilisearch.
* `COHERE_API_KEY` – clé Cohere.

Optionnelles (avec valeurs par défaut dans le code/Dockerfile) :

* `GEMINI_MODEL` – par défaut `gemini-2.5-flash`.
* `MEILI_HOST` – par défaut `http://host.docker.internal:7700`.
* `QDRANT_URL` – par défaut `http://host.docker.internal:6333`.
* `COHERE_RERANK_MODEL` – par défaut `rerank-multilingual-v3.0`.

Sur macOS/Windows, `host.docker.internal` permet à un conteneur
d’atteindre les services qui tournent sur la machine hôte.

---

### 3. Démarrer Meilisearch + Qdrant

Depuis la racine du projet :

```bash
cd infra
docker compose up -d
```

Cela démarre :

* Meilisearch sur `localhost:7700`
* Qdrant sur `localhost:6333`

Vérifier :

```bash
docker compose ps
```

Retourner ensuite à la racine :

```bash
cd ..
```

---

### 4. Builder l’image de l’API

```bash
docker build -t mathtuto-api .
```

Ce build :

* utilise `python:3.11-slim`,
* installe `requirements.txt`,
* copie le code dans `/app`,
* configure la commande :

  ```bash
  uvicorn src.app:app --host 0.0.0.0 --port 8000
  ```

---

### 5. Lancer le conteneur API

Assure-toi que Meilisearch et Qdrant tournent déjà (`docker compose up -d` dans `infra/`).

```bash
docker run \
  --rm \
  -p 8000:8000 \
  -e GEMINI_API_KEY="YOUR_REAL_GEMINI_KEY" \
  -e GEMINI_MODEL="gemini-2.5-flash" \
  -e MEILI_API_KEY="CHANGE_ME_STRONG_KEY" \
  -e MEILI_HOST="http://host.docker.internal:7700" \
  -e QDRANT_URL="http://host.docker.internal:6333" \
  -e COHERE_API_KEY="YOUR_COHERE_KEY" \
  -e COHERE_RERANK_MODEL="rerank-multilingual-v3.0" \
  mathtuto-api
```

Notes :

* `--rm` supprime le conteneur à l’arrêt.
* `-p 8000:8000` expose l’API sur `localhost:8000`.

---

### 6. Health check & test RAG

Health check :

```bash
curl http://127.0.0.1:8000/health
```

Attendu :

```json
{"status":"ok"}
```

Test RAG :

```bash
curl -X POST "http://127.0.0.1:8000/explain" \
  -H "Content-Type: application/json" \
  -d '{
        "question": "Explique le rôle du quantificateur universel.",
        "level": "1BAC",
        "track": "SM",
        "max_chunks": 6
      }'
```

Tu dois obtenir un JSON avec :

* `answer` – texte en markdown (Fiche Concept).
* `used_chunks` – liste de chunks utilisés (OFFICIEL / COACH).

---

### 7. Arrêter les services

Arrêter le conteneur API :

* `Ctrl+C` dans le terminal où `docker run mathtuto-api` tourne.

Arrêter Meilisearch + Qdrant :

```bash
cd infra
docker compose down
cd ..
```

---

### 8. Utiliser un fichier `.env` (optionnel)

Créer un `.env` à la racine :

```env
GEMINI_API_KEY=YOUR_REAL_GEMINI_KEY
GEMINI_MODEL=gemini-2.5-flash
MEILI_API_KEY=CHANGE_ME_STRONG_KEY
MEILI_HOST=http://host.docker.internal:7700
QDRANT_URL=http://host.docker.internal:6333
COHERE_API_KEY=YOUR_COHERE_KEY
COHERE_RERANK_MODEL=rerank-multilingual-v3.0
```

Lancer l’API :

```bash
docker run \
  --rm \
  -p 8000:8000 \
  --env-file .env \
  mathtuto-api
```

Pense à ajouter `.env` dans `.gitignore`.

---

### 9. Intégration avec le frontend

N’importe quel client (Next.js, curl, Postman…) peut appeler :

```http
POST http://localhost:8000/explain
Content-Type: application/json
```

Payload :

```json
{
  "question": "…",
  "level": "1BAC",
  "track": "SM",
  "max_chunks": 6
}
```

Réponse :

* utilisée par l’app Next.js `Full-app---AI-Math-Tutor-main` dans la page `/chat`,
* formatée en “Fiche Concept” (Définition, Intuition, Visualisation, Pièges).