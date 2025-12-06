# src/llm_service.py
import time
import os
from typing import Dict, Any, List, Tuple
import google.generativeai as genai

# CHANGE THIS LINE (add the dot)
from .retrieval_service import (
    hybrid_retrieve,
    build_context_text,
    simplify_chunks_for_api,
)

# ---------------------------------------------------------
# GEMINI CONFIG
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

_gemini_model = None


def get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        _gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    return _gemini_model


# ---------------------------------------------------------
# PROMPT BUILDER (COACH + FICHE CONCEPT)
# ---------------------------------------------------------

def build_concept_card_prompt(
    question: str,
    level: str,
    track: str,
    context_text: str,
) -> str:
    """
    Build the new Coach-style prompt with dual-layer context.
    `context_text` must already contain [OFFICIEL] / [COACH] tags.
    """
    prompt = f"""
Rôle :
Tu es "Le Coach Math", un tuteur expert pour des élèves marocains de niveau {level} {track} (BIOF).
Ton but est de débloquer l'intuition des élèves sans faire les exercices à leur place.
Ton ton est encourageant, direct, et tu utilises le "tu" ou le "on".

Contexte (RAG) :
Tu disposes d'extraits du cours officiel et d'explications ci-dessous (les "Sources").
- Utilise les sources [OFFICIEL] pour garantir la rigueur mathématique.
- Utilise les sources [COACH] (si disponibles) pour tes analogies.
- Si l'information est absente, dis : "Je ne peux pas répondre à partir du cours fourni."

Règle d'Or (Anti-Triche) :
Si l'élève te demande de résoudre un exercice spécifique (avec des nombres ou fonctions qui ne sont pas dans les Sources) :
1. REFUSE poliment : "Je ne peux pas faire ton exercice à ta place."
2. PIVOTE : Trouve l'exemple type le plus proche dans les Sources.
3. GUIDE : Explique la méthode de cet exemple type et encourage l'élève à l'appliquer.

Format de Réponse (La "Fiche Concept") :
Structure ta réponse exactement comme suit :

1. 🎯 C'est quoi ? (Définition) :
- Donne la définition exacte ou le théorème (en français soutenu, comme dans l'examen).
- Cite la source utilisée (ex: Source 1).

2. 💡 L'Intuition (Le Coach) :
- Explique "avec les mains". Pourquoi on a inventé ça ?
- Utilise une ANALOGIE concrète (balance, vitesse, argent, etc.).
- Utilise des phrases simples : "Imagine que...", "C'est comme...".

3. 🎨 Visualisation :
- Décris ce que l'élève doit voir dans sa tête (géométrie, courbe, schéma mental).
- Si le sujet s'y prête (Logique, Barycentre, Cercle Trigo), tu peux insérer un tag d'image pertinent à la fin de la description, par exemple :
  [Image of Table de vérité]
  [Image of Barycentre]
  [Image of Cercle Trigonométrique]

4. ⚠️ Attention ! (Pièges) :
- Quelle est l'erreur classique que tous les élèves font ? (ex: "Attention, l'implication inverse est fausse").

Question de l'élève :
\"\"\"{question}\"\"\"

Sources disponibles :
{context_text}
"""
    return prompt


# ---------------------------------------------------------
# MAIN ENTRYPOINT USED BY FASTAPI
# ---------------------------------------------------------

def explain_math(
    question: str,
    level: str = "1BAC",
    track: str = "SM",
    max_chunks: int = 6,
) -> Tuple[str, List[Dict[str, Any]]]:
    
    # 1) Retrieve chunks
    # The timing print is inside hybrid_retrieve now
    chunks = hybrid_retrieve(
        question=question,
        level=level,
        track=track,
        max_chunks=max_chunks,
    )

    if not chunks:
        no_data_answer = (
            "Je ne peux pas répondre à partir du cours fourni. "
            "Vérifie que le chapitre correspondant a bien été ajouté dans la base."
        )
        return no_data_answer, []

    # 2) Build Prompt
    context_text = build_context_text(chunks)
    prompt = build_concept_card_prompt(
        question=question,
        level=level,
        track=track,
        context_text=context_text,
    )

    # 3) Call Gemini
    t_start = time.time()
    print("⏱️ [Gemini] Sending request to Google API...")
    
    model = get_gemini_model()
    resp = model.generate_content(prompt)
    
    print(f"⏱️ [Gemini] Generation took {time.time() - t_start:.4f}s")

    answer_text = getattr(resp, "text", None)
    if not answer_text and getattr(resp, "candidates", None):
        answer_text = resp.candidates[0].content.parts[0].text
    if not answer_text:
        answer_text = "Une erreur s'est produite lors de la génération de la réponse."

    used_chunks = simplify_chunks_for_api(chunks)

    return answer_text, used_chunks