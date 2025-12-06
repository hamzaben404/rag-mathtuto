# Résumé complet – Backend RAG MathTutor (v3)

Je résume la **version actuelle** du backend, telle qu’elle est utilisée par
l’app Next.js `Full-app---AI-Math-Tutor-main`.

---

## A. Contexte & Scope

- Projet global : **MathTutor SAAS** pour élèves **1ère année Bac Science Math (Maroc – BIOF)**.
- Ta brique backend : un **service RAG d’explication de cours**, pas un solveur d’exercices.
- Rôle principal : agir comme **“Coach de maths”** qui explique le cours en suivant la
  pédagogie marocaine 1BAC SM.

Scope actuel du backend :

1. Chapitre couvert : **Notion de logique** (mais design extensible).
2. Tâche : produire des **explications structurées** à partir des contenus officiels
   et d’une couche d’intuition.
3. Pas de correction complète d’exercices (anti-triche).

---

## B. Architecture RAG choisie (v3)

Stack actuellle :

- **Embeddings** : `text-embedding-004` (Gemini).
- **Vector store** : **Qdrant** (Docker) – recherche sémantique.
- **Lexical search** : **Meilisearch** (Docker) – BM25, tolérant aux fautes FR.
- **Reranker** : **Cohere** `rerank-multilingual-v3.0`.
- **LLM de génération** : **Gemini 2.5 Flash** (`gemini-2.5-flash`).

Pipeline logique :

> Question → Meilisearch + Qdrant → Fusion → Cohere Rerank  
> → Top chunks (OFFICIEL + COACH) → Gemini → Réponse "Fiche Concept"

---

## C. Données & Chunking

### C.1. Double couche de contenu

Dans `data/logic/` :

- `logique_cours_part1.md`, `logique_cours_part2.md`  
  → contenu **officiel** du cours.
- `logique_intuition_part1.md`, `logique_intuition_part2.md`  
  → couche **COACH** (analogies, intuitions, visualisations).

Chaque chunk porte des métadonnées :

```json
{
  "id": "logic_v3_001",
  "title": "...",
  "body": "...",
  "kind": "official | intuition",
  "source_tag": "[OFFICIEL] | [COACH]",
  "level": "1BAC",
  "track": "SM",
  "chapter": "logique",
  "source_file": "..."
}
```

Le script **`build_chunks.py`** :

* Parse les 4 fichiers `.md`.
* Découpe par `#` / `##` pour garder des unités pédagogiques cohérentes.
* Aligne OFFICIEL et COACH sur les mêmes concepts.
* Sauvegarde dans **`data/logic/logic_chunks_v3.jsonl`**.

---

## D. Ingestion dans Qdrant (embeddings Gemini)

Script : **`embed_and_qdrant.py`**

1. Charge `logic_chunks_v3.jsonl`.
2. Appelle l’API Gemini **`text-embedding-004`** pour encoder `body`.
3. Crée / met à jour la collection Qdrant :

   * Nom : `mathtuto_math_chunks_v3`
   * Distance : cosinus
   * Vecteurs : dimension de `text-embedding-004`.
4. Upsert :

   * `point_id` numérique,
   * vecteur d’embedding,
   * payload = toutes les métadonnées du chunk.

Résultat : Qdrant peut répondre à des requêtes sémantiques en FR avec
les métadonnées (OFFICIEL / COACH, niveau, chapitre…).

---

## E. Ingestion dans Meilisearch (BM25)

Script : **`ingest_meili.py`**

1. Recharge `logic_chunks_v3.jsonl`.
2. Crée l’index :

   * Nom : `mathtuto_math_chunks_v3`.
   * Clé primaire : `id`.
3. Configure les settings :

   * `searchableAttributes`: `title`, `body`.
   * `filterableAttributes`: `level`, `track`, `kind`, `chapter`.
4. Insère tous les documents.

Résultat : Meilisearch gère la **recherche plein texte**, y compris fautes
de frappe et vocabulaire FR scolaire.

---

## F. Retrieval hybride + Rerank Cohere

Implémenté dans **`src/retrieval_service.py`** :

* Classe `HybridRetriever` :

  * connexions à Meilisearch + Qdrant,
  * accès à Cohere via `COHERE_API_KEY`.

Méthode principale : `retrieve(question: str, top_k: int)`.

Étapes :

1. **Lexical** : Meilisearch retourne les meilleurs documents.
2. **Vectoriel** : Qdrant retourne les voisins sémantiques de la question
   (embedding Gemini de la question).
3. **Fusion** : on combine les scores (lexical + vectoriel) pour garder un
   set candidat.
4. **Rerank Cohere** :

   * on envoie `(question, chunks)` au modèle
     `rerank-multilingual-v3.0`,
   * on récupère les `top_k` chunks les plus pertinents.

Retour : une liste de dataclasses `RetrievedChunk` avec :

* `id`, `title`, `body`,
* `kind` (`official` / `intuition`),
* scores de reranking.

---

## G. Prompt pédagogique & LLM Gemini

Implémenté dans **`src/llm_service.py`**.

### G.1. Rôle & contraintes

* Rôle : **prof de maths marocain** pour **1BAC SM**, en français.
* Travaille **uniquement** à partir des chunks fournis (RAG) :

  * si l’info manque → le dire explicitement,
  * pas de théorèmes nouveaux,
  * pas de solutions complètes d’exercices (anti-triche).

### G.2. Format de réponse : “Fiche Concept”

La réponse suit un format fixe :

1. 🎯 **Définition**
2. 💡 **Intuition (Coach)** – analogies, métaphores, exemples du quotidien.
3. 🎨 **Visualisation** – texte + éventuels blocs `[Image of ...]`.
4. ⚠️ **Pièges** – erreurs classiques des élèves 1BAC SM.

Le service `generate_explanation(question, chunks, level, track)` :

* construit un prompt structuré,
* insère les chunks OFFICIEL + COACH,
* appelle `gemini-2.5-flash`,
* renvoie `answer` (markdown) + infos sur les chunks utilisés.

---

## H. FastAPI – Microservice RAG

Implémenté dans **`src/app.py`**.

Composition :

* `retriever = HybridRetriever(...)`
* `llm_service = LLMService(...)`

Routes :

* `GET /health`
  → `{"status": "ok"}`
* `POST /explain`
  Payload :

  ```json
  {
    "question": "Explique le rôle du quantificateur universel.",
    "level": "1BAC",
    "track": "SM",
    "max_chunks": 6
  }
  ```

  Pipeline :

  1. `retriever.retrieve(...)`
  2. `llm_service.generate_explanation(...)`
  3. Retour :

     ```json
     {
       "answer": "...markdown Fiche Concept...",
       "used_chunks": [
         { "id": "...", "kind": "official", ... },
         { "id": "...", "kind": "intuition", ... }
       ]
     }
     ```

---

## I. Dockerisation du backend

Fichiers :

* `infra/docker-compose.yml` → Meilisearch + Qdrant.
* `Dockerfile` → image `mathtuto-api`.

Points clés :

* L’API tourne sur `uvicorn src.app:app --host 0.0.0.0 --port 8000`.
* Accès à Meilisearch / Qdrant via `host.docker.internal` (macOS/Windows).
* Variables d’environnement importantes :

  * `GEMINI_API_KEY`, `GEMINI_MODEL`
  * `MEILI_HOST`, `MEILI_API_KEY`
  * `QDRANT_URL`
  * `COHERE_API_KEY`, `COHERE_RERANK_MODEL` (par défaut : `rerank-multilingual-v3.0`).

Pour les détails : voir `docs/DOCKER.md`.

---

## J. Intégration avec le frontend Next.js (Math Coach)

Dans le projet `Full-app---AI-Math-Tutor-main` :

* La page **`/chat`** expose une UI de chat (assistant-ui).

* Next.js appelle un route handler **`app/api/chat/route.ts`**.

* Ce handler proxy vers notre backend :

  * `POST http://127.0.0.1:8000/explain`
  * transmet `question, level, track`
  * récupère `{answer, used_chunks}`.

* La réponse est streamée dans l’UI :

  * rendu Markdown + KaTeX,
  * affichage des sections Définition / Intuition / Visualisation / Pièges.

Résultat : le backend RAG est maintenant **pleinement intégré** à la
plateforme MathTutor.

---

## K. Roadmap backend

* Ajouter d’autres chapitres : fonctions, dérivées, barycentre, probas…
* Ajouter un dataset d’évaluation (questions + “bonne fiche concept”).
* Raffiner le retrieval (query rewriting, filtres par chapitre).
* Ajouter des logs + métriques (taux de réutilisation de chunks, temps de réponse).
* Préparer un déploiement cloud (API + Meili + Qdrant).