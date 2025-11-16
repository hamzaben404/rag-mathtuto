# src/llm_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import os

from .retrieval_service import RetrievedChunk

from google import genai  # Gemini Python SDK


@dataclass
class GeminiConfig:
    """
    Configuration for the Gemini LLM layer.
    """

    model: str = "gemini-2.5-flash"  # default text model for explanations
    api_key: Optional[str] = None  # if None, read from GEMINI_API_KEY env var


class LLMService:
    """
    LLM service powered by Google Gemini.

    Public method:
        generate_explanation(question: str, chunks: List[RetrievedChunk], ...) -> str
    """

    def __init__(self, config: Optional[GeminiConfig] = None):
        if config is None:
            # Read config from environment if not provided
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            api_key = os.getenv("GEMINI_API_KEY")
            config = GeminiConfig(model=model, api_key=api_key)

        if not config.api_key:
            # Note: genai.Client() can also pick up GEMINI_API_KEY automatically,
            # but we explicitly require it to avoid silent misconfigurations.
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Export it in your environment before starting the app."
            )

        self.config = config
        # Initialize Gemini client (Developer API)
        # See: https://ai.google.dev/gemini-api/docs/quickstart
        self.client = genai.Client(api_key=self.config.api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_explanation(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        level: str = "1BAC",
        track: str = "SM",
    ) -> str:
        """
        Generate a pedagogical explanation for the given question,
        grounded in the provided retrieved chunks.
        """

        if not chunks:
            return (
                "Je n'ai pas trouvé de partie du cours correspondant à ta question. "
                "Vérifie l'orthographe ou précise un peu plus ta demande."
            )

        # Build the text prompt
        prompt = self._build_prompt(question, chunks, level, track)

        try:
            response = self.client.models.generate_content(
                model=self.config.model,
                contents=prompt,
            )
        except Exception as e:
            # Fallback if the API fails
            fallback = self._fallback_from_chunks(question, chunks, level, track)
            return (
                "Je rencontre un problème avec le modèle Gemini. "
                "Je te donne une explication de base à partir du cours :\n\n"
                + fallback
                + f"\n\n(Détails techniques cachés: {e})"
            )

        # Extract text safely
        text = getattr(response, "text", None)
        if not text:
            # Fallback if response has no text
            return self._fallback_from_chunks(question, chunks, level, track)

        return text.strip()

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def _build_prompt(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        level: str,
        track: str,
    ) -> str:
        """
        Build a single text prompt for Gemini using the question and course chunks.
        """

        # Keep only a few top chunks to avoid too long prompts (Gemini can handle a lot,
        # but we don't need to send everything for small 1BAC questions).
        top_chunks = chunks[:4]

        # Format chunks as "source" text
        context_parts = []
        for idx, ch in enumerate(top_chunks, start=1):
            title = ch.title.strip() if ch.title else ""
            header = f"Source {idx}: {title}" if title else f"Source {idx}:"
            body = ch.body.strip()
            context_parts.append(f"{header}\n{body}")

        context_text = "\n\n".join(context_parts)

        # System-style instruction + user question + context
        prompt = f"""
            Rôle :
            Tu es un professeur de mathématiques marocain, niveau {level} {track}.
            Tu t’adresses à un élève de 1BAC Science Math qui révise son cours.

            Contexte et règles RAG :
            - Tu disposes d’extraits du cours officiels ci-dessous (les "Sources").
            - Réponds UNIQUEMENT à partir de ces extraits.
            - Si l’information demandée n’apparaît pas clairement dans les Sources,
            dis explicitement que tu ne peux pas répondre à partir du cours
            (par exemple : "Le cours fourni ne contient pas assez d’informations pour répondre précisément.").
            - N’invente pas de nouveaux résultats, théorèmes ou notations qui ne figurent pas dans le cours.
            - N’ajoute pas d’exercices corrigés : contente-toi d’expliquer le cours.

            Objectif pédagogique :
            - Répondre à la question de l’élève.
            - Expliquer étape par étape avec un ton clair, bienveillant et rassurant.
            - Rester au niveau 1BAC {track} (éviter le vocabulaire universitaire).
            - Aider l’élève à COMPRENDRE, pas seulement à mémoriser.

            Format de la réponse :
            Donne ta réponse en 5 parties courtes :

            1. Rappel du thème :
            - Situe rapidement le sujet (par ex. proposition logique, quantificateur ∀, lois de Morgan, etc.).

            2. Définition / idée clé :
            - Donne la définition ou l’idée centrale, en reformulant le cours avec des mots simples.

            3. Explication détaillée :
            - Explique la définition ou la propriété de manière progressive.
            - Relie ton explication aux Sources (par exemple : "Comme indiqué dans la Source 2...").

            4. Exemple simple :
            - Propose un petit exemple inspiré du cours ou directement tiré des Sources.
            - Explique pourquoi cet exemple illustre bien la notion.

            5. À retenir :
            - Résume en 2–3 phrases ce que l’élève doit retenir.

            Quand tu utilises une information issue d’un extrait, indique la Source entre parenthèses,
            par exemple (Source 1) ou (Source 2), pour que l’élève sache d’où vient l’idée.

            Question de l’élève :
            \"\"\"{question}\"\"\"

            Extraits du cours (Sources) :
            {context_text}
        """

        # Gemini API accepts a simple string as 'contents' in generate_content.
        return prompt.strip()

    # ------------------------------------------------------------------
    # Fallback if Gemini API fails
    # ------------------------------------------------------------------
    def _fallback_from_chunks(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        level: str,
        track: str,
    ) -> str:
        """
        Simple deterministic explanation directly from chunks if Gemini is unavailable.
        """
        top_chunks = chunks[:3]
        parts = []
        for ch in top_chunks:
            title = (ch.title or "").strip()
            body = (ch.body or "").strip()
            if title:
                parts.append(f"**{title}**\n{body}")
            else:
                parts.append(body)

        context_text = "\n\n".join(parts)

        return (
            f"Question : {question}\n\n"
            f"Rappel du cours (niveau {level} {track}) :\n{context_text}\n\n"
            "Essaie de lire ces extraits et de reformuler avec tes propres mots. "
            "Quand Gemini sera disponible, je pourrai te donner une explication plus détaillée."
        )
