# MathTutor RAG – 1BAC Science Math (Maroc)

Backend RAG pour un tuteur de maths **1ère année Bac Science Math (SM – BIOF)**.

Ce microservice fournit des **explications guidées du cours officiel**, avec une
double couche :

- `[OFFICIEL]` – texte du cours.
- `[COACH]` – intuitions, analogies, visualisations.

Il utilise un **RAG hybride** (Meilisearch + Qdrant + reranker Cohere) et **Gemini**
pour générer des fiches d’explication.

---

## ✨ Fonctionnalités

### Hybrid Retrieval

- **Lexical** : Meilisearch (BM25, tolérant aux fautes FR).
- **Vectoriel** : Qdrant + embeddings **Gemini `text-embedding-004`**.
- **Fusion** : combinaison scores lexical / vectoriel.
- **Reranking** : Cohere `rerank-multilingual-v3.0` pour trier les meilleurs chunks.

### RAG Generation

- **LLM** : **Gemini 2.5 Flash** (`gemini-2.5-flash`).
- Rôle : prof de maths marocain (1BAC SM, français).
- Toujours **ancré dans les chunks du cours** (pas d’hallucinations volontaires).
- Forme de réponse : **Fiche Concept** :

  1. 🎯 Définition  
  2. 💡 Intuition (Coach)  
  3. 🎨 Visualisation  
  4. ⚠️ Pièges  

- Refus de résoudre directement un exercice complet (anti-triche).

### FastAPI Microservice

- `GET /health` – health check.
- `POST /explain` – exécute tout le pipeline RAG, retourne :

  ```json
  {
    "answer": "…markdown…",
    "used_chunks": [...]
  }
  ```

### Docker

* Image API : `mathtuto-api`.
* Infra : `infra/docker-compose.yml` (Meilisearch + Qdrant).
* Guide complet dans `docs/DOCKER.md`.

---

## 🗂 Structure du projet

```text
rag-math-mathtuto/
├── src/
│   ├── app.py               # FastAPI entrypoint
│   ├── retrieval_service.py # Hybrid search (Meili + Qdrant + Cohere)
│   ├── llm_service.py       # Wrapper Gemini + prompt pédagogique
│   └── ...
│
├── data/
│   └── logic/
│       ├── logique_cours_part*.md
│       ├── logique_intuition_part*.md
│       └── logic_chunks_v3.jsonl   # Chunks OFFICIEL / COACH
│
├── infra/
│   └── docker-compose.yml   # Meilisearch + Qdrant
│
├── docs/
│   └── DOCKER.md            # Instructions Docker
│
├── requirements.txt
├── Dockerfile               # Image `mathtuto-api`
├── .gitignore
└── LICENSE
```

---

## 🚀 Quickstart (local, sans Docker pour l’API)

### 1) Environnement Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Démarrer Meilisearch + Qdrant

```bash
cd infra
docker compose up -d
cd ..
```

### 3) Variables d’environnement

```bash
export GEMINI_API_KEY="YOUR_REAL_GEMINI_KEY"
export GEMINI_MODEL="gemini-2.5-flash"

export MEILI_HOST="http://localhost:7700"
export MEILI_API_KEY="CHANGE_ME_STRONG_KEY"

export QDRANT_URL="http://localhost:6333"

export COHERE_API_KEY="YOUR_COHERE_KEY"
export COHERE_RERANK_MODEL="rerank-multilingual-v3.0"
```

### 4) Lancer FastAPI

```bash
uvicorn src.app:app --reload --port 8000
```

### 5) Tester

Health check :

```bash
curl http://127.0.0.1:8000/health
```

RAG :

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

---

## 🐳 Utilisation Docker (résumé)

Pour les détails complets, voir **`docs/DOCKER.md`**.

Résumé :

```bash
# 1) Démarrer Meili + Qdrant
cd infra
docker compose up -d
cd ..

# 2) Builder l’image
docker build -t mathtuto-api .

# 3) Lancer l’API
docker run \
  --rm \
  -p 8000:8000 \
  --env-file .env \
  mathtuto-api
```

Avec un `.env` contenant les clés nécessaires (Gemini, Meili, Qdrant, Cohere).

---

## 🔗 Intégration avec le frontend MathTutor

Le frontend Next.js (`Full-app---AI-Math-Tutor-main`) :

* appelle `POST /api/chat` côté Next,
* qui proxifie vers `POST http://localhost:8000/explain`,
* et affiche la réponse dans une UI de chat (assistant-ui) pour les élèves
  **1BAC SM – BIOF**.

---

## 📌 Roadmap

* Ajouter d’autres chapitres (fonctions, dérivées, probas…).
* Mettre en place un jeu de tests RAG (questions + réponses attendues).
* Logs et métriques (pertinence des chunks, temps de réponse).
* Déploiement cloud (API + Meili + Qdrant).
