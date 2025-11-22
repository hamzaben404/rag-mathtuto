#!/usr/bin/env bash

BACKEND_URL="http://127.0.0.1:8000/explain"

LEVEL="1BAC"
TRACK="SM"
MAX_CHUNKS=4

# Output file (will be overwritten at each run)
OUTPUT_FILE="test_rag_results.txt"

echo "RAG test run - $(date)" > "$OUTPUT_FILE"
echo "Backend: $BACKEND_URL" >> "$OUTPUT_FILE"
echo "Level: $LEVEL, Track: $TRACK, max_chunks: $MAX_CHUNKS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

questions=(
  # 1) Définitions / notions de base
  "C’est quoi une proposition logique ?"
  "Explique la différence entre une proposition vraie et une proposition fausse."
  "Que signifie l’écriture P ⇒ Q en logique ?"
  "C’est quoi une équivalence logique (P ⇔ Q) ?"
  "Définis une tautologie (loi logique)."
  "Qu’appelle-t-on la négation d’une proposition ?"

  # 2) Quantificateurs
  "Explique le rôle du quantificateur ∀ (pour tout)."
  "Explique ce que signifie le quantificateur ∃ (il existe)."
  "Quelle est la différence entre « ∀x ∈ E, P(x) » et « ∃x ∈ E, P(x) » ?"
  "Comment nie-t-on une proposition du type « ∀x ∈ E, P(x) » ?"
  "Comment nie-t-on une proposition du type « ∃x ∈ E, P(x) » ?"

  # 3) Opérations sur les propositions / connecteurs
  "Explique la différence entre « P et Q » et « P ou Q »."
  "C’est quoi la négation de « P et Q » ?"
  "C’est quoi la négation de « P ou Q » ?"
  "Explique en langage simple ce que veut dire « P ⇒ Q est vraie »."
  "Quelle est la réciproque de l’implication « P ⇒ Q » ?"
  "Quelle est la contraposée de l’implication « P ⇒ Q » ?"

  # 4) Lois logiques et raisonnements
  "C’est quoi une loi de Morgan ?"
  "Donne l’énoncé des deux lois de Morgan et explique-les simplement."
  "Explique le raisonnement par contraposée."
  "Explique le raisonnement par l’absurde."
  "Explique le raisonnement par disjonction des cas."
  "Explique le principe général du raisonnement par récurrence."
  "Dans quel cas on préfère utiliser un raisonnement par contraposée plutôt qu’un raisonnement direct ?"

  # 5) Exemples simples
  "Donne un exemple simple de proposition mathématique vraie et un exemple faux."
  "Donne un exemple de phrase qui n’est pas une proposition logique et explique pourquoi."
  "Donne un petit exemple qui illustre le quantificateur ∀."
  "Donne un petit exemple qui illustre le quantificateur ∃."
  "Donne un exemple de loi de Morgan avec des phrases simples en français."

  # 6) Méta-explication / liens
  "Pourquoi apprend-on les quantificateurs en logique au 1BAC ?"
  "Comment les lois de Morgan peuvent aider à simplifier une expression logique ?"
  "Quel est le lien entre la contraposée et la négation d’une implication ?"
  "Pourquoi le raisonnement par l’absurde est-il un type particulier de preuve ?"

  # 7) Hors scope (pour tester les limites)
  "Explique la dérivée d’une fonction."
  "Explique les suites arithmétiques."
  "Explique le théorème de Pythagore."
  "Parle-moi de la logique intuitionniste."
  "Explique le théorème d’incomplétude de Gödel."
)

for q in "${questions[@]}"; do
  echo "================================================================================"
  echo "QUESTION: $q"
  echo "================================================================================"

  # Write question to file
  {
    echo "================================================================================"
    echo "QUESTION: $q"
    echo "================================================================================"
  } >> "$OUTPUT_FILE"

  # Call the API
  response=$(curl -s -X POST "$BACKEND_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"question\": \"$q\",
      \"level\": \"$LEVEL\",
      \"track\": \"$TRACK\",
      \"max_chunks\": $MAX_CHUNKS
    }")

  # Print to terminal
  echo "$response"
  echo ""

  # Append to file
  {
    echo "$response"
    echo ""
  } >> "$OUTPUT_FILE"
done

echo "All results saved to $OUTPUT_FILE"
