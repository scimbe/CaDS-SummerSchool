#!/usr/bin/env python3
"""Schritt 7: Derselbe Endpoint mit dem offiziellen OpenAI-SDK.

Der Endpoint ist OpenAI-kompatibel. Das heißt: jede Bibliothek, jedes Framework
und jedes Tool, das mit OpenAI spricht, spricht auch mit diesem Modell.
Man ändert nur zwei Dinge: base_url und api_key.

Vorher einmalig:  pip install openai
Aufruf:           python3 07_openai_sdk.py "Deine Frage"
"""
import sys

import llm  # nur für die Werte aus .env

try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("Bitte einmalig installieren:  pip install openai")

client = OpenAI(
    base_url=llm.BASE_URL,   # <- der einzige echte Unterschied zu OpenAI
    api_key=llm.API_KEY,
)

frage = " ".join(sys.argv[1:]) or "Nenne drei Vorteile eines selbst gehosteten LLM."
print(f"> {frage}\n")

antwort = client.chat.completions.create(
    model=llm.MODEL,
    messages=[{"role": "user", "content": frage}],
    max_tokens=500,
)

print(antwort.choices[0].message.content)
print(f"\n[Tokens: {antwort.usage.prompt_tokens} rein, {antwort.usage.completion_tokens} raus]")
