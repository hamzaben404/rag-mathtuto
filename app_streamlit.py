import os
import requests
import streamlit as st

# ---------------------------------------------------------
# Basic configuration
# ---------------------------------------------------------
DEFAULT_BACKEND_URL = os.getenv("MATHTUTO_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MathTutor – Apprentissage guidé",
    page_icon="📚",
    layout="wide",
)

st.title("📚 MathTutor – Apprentissage guidé (1BAC SM)")
st.markdown(
    """
Interface de démonstration pour le **tuteur RAG** :
- Explique le cours de logique 1BAC SM à partir du support officiel.
- Utilise Meilisearch + Qdrant + Gemini pour générer la réponse.
"""
)

# ---------------------------------------------------------
# Sidebar: settings
# ---------------------------------------------------------
st.sidebar.header("⚙️ Paramètres")

backend_url = st.sidebar.text_input(
    "Backend API URL",
    value=DEFAULT_BACKEND_URL,
    help="URL de l’API FastAPI (par défaut: http://localhost:8000)",
)

level = st.sidebar.selectbox("Niveau", options=["1BAC"], index=0)
track = st.sidebar.selectbox("Filière", options=["SM", "SVT"], index=0)

max_chunks = st.sidebar.slider(
    "Nombre max de chunks à utiliser",
    min_value=2,
    max_value=8,
    value=4,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.markdown("Assure-toi que l’API FastAPI est en cours d’exécution.")

# ---------------------------------------------------------
# Chat state
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # list of dict: {"role": "user"/"assistant", "content": str}
if "history_sources" not in st.session_state:
    st.session_state["history_sources"] = []  # list of list[dict], aligned with assistant messages


# ---------------------------------------------------------
# Helper: call backend
# ---------------------------------------------------------
def call_backend(question: str):
    """Call the FastAPI /explain endpoint with the given question."""
    url = backend_url.rstrip("/") + "/explain"
    payload = {
        "question": question,
        "level": level,
        "track": track,
        "max_chunks": max_chunks,
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
    except requests.RequestException as e:
        raise RuntimeError(f"Erreur de connexion à l’API: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Erreur API {resp.status_code}: {resp.text}")

    data = resp.json()
    answer = data.get("answer", "")
    used_chunks = data.get("used_chunks", [])
    return answer, used_chunks


# ---------------------------------------------------------
# Display existing chat history
# ---------------------------------------------------------
for i, msg in enumerate(st.session_state["messages"]):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
            # Optional: show sources used for this assistant message
            # We align assistant messages with history_sources by index of assistant messages only.
            # For simplicity, we show sources for the last assistant answer only in the current run.
            # Full alignment can be added later if needed.


# ---------------------------------------------------------
# Chat input
# ---------------------------------------------------------
user_input = st.chat_input("Pose ta question sur le cours de logique (1BAC SM)…")

if user_input:
    # 1) Add user message to history
    st.session_state["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # 2) Call backend
    with st.chat_message("assistant"):
        with st.spinner("Le tuteur réfléchit..."):
            try:
                answer, used_chunks = call_backend(user_input)
            except Exception as e:
                st.error(str(e))
                answer = ""
                used_chunks = []

        if answer:
            st.markdown(answer)
        else:
            st.warning("Aucune réponse générée.")

        # Display the sources for this specific answer
        if used_chunks:
            with st.expander("📄 Sources utilisées (extraits du cours)"):
                for ch in used_chunks:
                    chunk_id = ch.get("id", "")
                    title = ch.get("title", "")
                    subchapter = ch.get("subchapter", "")
                    concept = ch.get("concept", "")
                    kind = ch.get("kind", "")

                    st.markdown(
                        f"- **{title or '(sans titre)'}**  \n"
                        f"  - id: `{chunk_id}`  \n"
                        f"  - type: `{kind}`  \n"
                        f"  - sous-chapitre: `{subchapter}`  \n"
                        f"  - concept: `{concept}`"
                    )

    # 3) Store assistant message + sources in history
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    st.session_state["history_sources"].append(used_chunks)
