#!/usr/bin/env bash
# Schritt 2: Dasselbe, aber mit "stream": true -> Antwort kommt Token für Token.
# Aufruf:  ./02_stream_curl.sh "Deine Frage"
source "$(dirname "$0")/_common.sh"

FRAGE="${1:-Schreibe ein kurzes Gedicht über Hamburg.}"

BODY=$(jq -n --arg model "$LLM_MODEL" --arg frage "$FRAGE" '{
  model: $model,
  messages: [ { role: "user", content: $frage } ],
  stream: true,
  max_tokens: 500
}')

echo "> $FRAGE"
echo

# Der Server schickt Server-Sent-Events: jede Zeile "data: {...}", am Ende "data: [DONE]".
# -N schaltet das Puffern von curl aus, damit man das Tippen live sieht.
curl -sN "$LLM_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" \
| while read -r line; do
    [[ "$line" == data:* ]] || continue
    payload="${line#data: }"
    [[ "$payload" == "[DONE]" ]] && break
    printf '%s' "$(jq -rj '.choices[0].delta.content // ""' <<< "$payload")"
  done

echo; echo
