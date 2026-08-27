#!/usr/bin/env python3
"""Schritt 5: Mehrere Runden - das Modell hat kein Gedächtnis.

Kernidee: Der komplette bisherige Verlauf wird bei JEDER Anfrage mitgeschickt.
Genau deshalb wächst der Token-Verbrauch mit der Länge des Gesprächs.

Aufruf:  python3 05_dialog.py     (beenden mit 'exit' oder Strg+D)
"""
import llm

verlauf = [
    {"role": "system", "content": "Du bist ein knapper, freundlicher Assistent. Antworte auf Deutsch."}
]

print("Dialog gestartet. 'exit' zum Beenden.\n")

while True:
    try:
        eingabe = input("Du > ").strip()
    except EOFError:
        break
    if not eingabe:
        continue
    if eingabe.lower() in {"exit", "quit", "ende"}:
        break

    verlauf.append({"role": "user", "content": eingabe})

    print("KI > ", end="", flush=True)
    antwort = ""
    for schnipsel in llm.stream(verlauf):
        print(schnipsel, end="", flush=True)
        antwort += schnipsel
    print("\n")

    # Antwort in den Verlauf legen, sonst "vergisst" das Modell die nächste Runde.
    verlauf.append({"role": "assistant", "content": antwort})

print(f"\nEnde. {len(verlauf) - 1} Nachrichten im Verlauf.")
