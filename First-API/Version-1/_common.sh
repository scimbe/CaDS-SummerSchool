#!/usr/bin/env bash
# Wird von allen Shell-Skripten geladen: liest .env und prüft die Variablen.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# .env suchen: erst neben dem Skript, dann eine Ebene höher (Projektwurzel).
ENV_FILE=""
for dir in "$HERE" "$HERE/.." "$HERE/../.."; do
  [[ -f "$dir/.env" ]] && { ENV_FILE="$dir/.env"; break; }
done

# Zeilen der Form KEY=VALUE laden, ohne bestehende Umgebungsvariablen zu überschreiben.
if [[ -n "$ENV_FILE" ]]; then
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^[A-Z_]+$ ]] || continue
    [[ -n "${!key:-}" ]] || export "$key=$value"
  done < "$ENV_FILE"
fi

: "${LLM_BASE_URL:?LLM_BASE_URL fehlt - bitte .env anlegen (siehe .env.example)}"
: "${LLM_API_KEY:?LLM_API_KEY fehlt - bitte .env anlegen (siehe .env.example)}"
: "${LLM_MODEL:=local-devstral-small2}"
