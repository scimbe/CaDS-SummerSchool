#!/usr/bin/env python3
"""Schritt 3: Einzelne Frage aus Python heraus.

Aufruf:  python3 03_chat.py "Deine Frage"
"""
import sys

import llm

frage = " ".join(sys.argv[1:]) or "Erkläre den Unterschied zwischen KI und Machine Learning."

print(f"> {frage}\n")

antwort = llm.ask(
    frage,
    system="Du bist ein hilfsbereiter Tutor. Antworte präzise und auf Deutsch.",
)

print(antwort)
