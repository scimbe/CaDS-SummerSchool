#!/usr/bin/env python3
"""Schritt 4: Antwort live mitlesen (Streaming).

Aufruf:  python3 04_stream.py "Deine Frage"
"""
import sys

import llm

frage = " ".join(sys.argv[1:]) or "Erzähle eine kurze Geschichte über einen Roboter."

print(f"> {frage}\n")

for schnipsel in llm.stream([{"role": "user", "content": frage}]):
    print(schnipsel, end="", flush=True)

print("\n")
