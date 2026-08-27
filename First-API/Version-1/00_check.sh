#!/usr/bin/env bash
# Schritt 0: Erreichbarkeit + Key prüfen und verfügbare Modelle auflisten.
source "$(dirname "$0")/_common.sh"

echo "Endpoint : $LLM_BASE_URL"
echo "Modell   : $LLM_MODEL"
echo "Key      : ${LLM_API_KEY:0:6}...${LLM_API_KEY: -4}"
echo

code=$(curl -s -o /tmp/models.json -w '%{http_code}' \
  "$LLM_BASE_URL/models" \
  -H "Authorization: Bearer $LLM_API_KEY")

echo "HTTP $code"
case "$code" in
  200) echo "Verfügbare Modelle:"; jq -r '.data[].id' /tmp/models.json | sed 's/^/  - /' ;;
  401) echo "FEHLER: Key ungültig." ;;
  *)   echo "FEHLER:"; cat /tmp/models.json ;;
esac
