# streamlit_app.py
import os
import requests
import streamlit as st

API_URL = os.getenv("MATHTUTO_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Le Coach Math – Logique 1BAC SM", layout="centered")

st.title("Le Coach Math – Logique 1BAC SM")

st.write(
    "Pose une question sur le cours de logique (propositions, quantificateurs, lois de Morgan, "
    "raisonnement par contraposée, etc.). Le Coach utilisera le cours officiel + les explications."
)

question = st.text_area("Ta question :", height=120, placeholder="Ex: Explique le rôle du quantificateur ∀.")

col1, col2, col3 = st.columns(3)
with col1:
    level = st.selectbox("Niveau", ["1BAC"], index=0)
with col2:
    track = st.selectbox("Filière", ["SM"], index=0)
with col3:
    max_chunks = st.slider("Nb de morceaux de contexte", 2, 8, 6)

if st.button("Lancer l'explication"):
    if not question.strip():
        st.warning("Écris d'abord une question.")
    else:
        with st.spinner("Le Coach réfléchit..."):
            try:
                resp = requests.post(
                    f"{API_URL}/explain",
                    json={
                        "question": question,
                        "level": level,
                        "track": track,
                        "max_chunks": max_chunks,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                st.error(f"Erreur en appelant l'API : {e}")
            else:
                st.markdown("## Réponse du Coach")
                st.markdown(data.get("answer", ""), unsafe_allow_html=False)

                sources = data.get("used_chunks", [])
                if sources:
                    st.markdown("## Sources utilisées")
                    for i, ch in enumerate(sources, 1):
                        tag = ch.get("source_tag", "")
                        title = ch.get("title", "") or "(sans titre)"
                        with st.expander(f"Source {i} – {tag} {title}"):
                            st.write(f"**ID** : `{ch.get('id')}`")
                            st.write(f"**Type** : `{ch.get('kind')}`")
                            if ch.get("concept"):
                                st.write(f"**Concept** : `{ch.get('concept')}`")
