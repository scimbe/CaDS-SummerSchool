#!/usr/bin/env bash
# Schritt 1: Einfachste Anfrage - eine Frage, eine Antwort.
# Aufruf:  ./01_chat_curl.sh "Deine Frage"
source "$(dirname "$0")/_common.sh"

FRAGE="${1:-Erkläre in drei Sätzen, was ein Large Language Model ist.}"

# jq baut das JSON, damit Anführungszeichen/Umlaute in der Frage sicher escaped werden.
BODY=$(jq -n --arg model "$LLM_MODEL" --arg frage "$FRAGE" '{
  model: $model,
  messages: [ { role: "user", content: $frage } ],
  temperature: 0.7,
  max_tokens: 500
}')

echo "> $FRAGE"
echo

curl -s "$LLM_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" \
| jq -r '.choices[0].message.content'
