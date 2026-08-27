#!/usr/bin/env python3
"""Schritt 6: Tool-Calling - das Modell darf Funktionen in DEINEM Code aufrufen.

Ablauf (immer derselbe Kreislauf):
  1. Wir beschreiben unsere Funktionen als JSON-Schema und schicken sie mit.
  2. Das Modell antwortet nicht mit Text, sondern mit einem tool_call + Argumenten.
  3. WIR führen die Funktion aus - das Modell kann das nicht selbst.
  4. Wir schicken das Ergebnis als role="tool" zurück; das Modell formuliert die Antwort.

Aufruf:  python3 06_tools.py "Wie warm ist es in Hamburg und was ist 17 * 23?"
"""
import json
import sys

import llm


# --- 1. Die echten Funktionen ------------------------------------------------

def get_weather(city: str) -> dict:
    """Tut hier nur so - in echt käme hier ein API-Aufruf (siehe Version-2)."""
    demo = {"hamburg": 18, "muenchen": 24, "berlin": 21}
    return {"stadt": city, "temperatur_c": demo.get(city.lower(), 20), "quelle": "Demo-Daten"}


def calculate(expression: str) -> dict:
    """Rechnet einen einfachen Ausdruck aus - nur Ziffern und Grundrechenarten."""
    if not set(expression) <= set("0123456789+-*/(). "):
        return {"fehler": "Nur Zahlen und + - * / ( ) erlaubt."}
    return {"ausdruck": expression, "ergebnis": eval(expression)}  # noqa: S307 (durch Filter oben abgesichert)


VERFUEGBAR = {"get_weather": get_weather, "calculate": calculate}


# --- 2. Die Beschreibung für das Modell -------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Liefert die aktuelle Temperatur für eine Stadt.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "Name der Stadt"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Rechnet einen mathematischen Ausdruck aus, z.B. '17 * 23'.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]


# --- 3. Der Kreislauf --------------------------------------------------------

def main() -> None:
    frage = " ".join(sys.argv[1:]) or "Wie warm ist es in Hamburg und wie viel ist 17 * 23?"
    print(f"> {frage}\n")

    verlauf = [{"role": "user", "content": frage}]

    for runde in range(1, 6):  # Obergrenze, damit es nie endlos läuft
        nachricht = llm.chat(verlauf, tools=TOOLS)
        verlauf.append(nachricht)

        aufrufe = nachricht.get("tool_calls")
        if not aufrufe:
            print(nachricht.get("content", ""))
            return

        for aufruf in aufrufe:
            name = aufruf["function"]["name"]
            argumente = json.loads(aufruf["function"]["arguments"])
            print(f"  [Runde {runde}] Modell ruft auf: {name}({argumente})")

            funktion = VERFUEGBAR.get(name)
            ergebnis = funktion(**argumente) if funktion else {"fehler": f"Unbekanntes Tool: {name}"}
            print(f"  [Runde {runde}] Ergebnis: {ergebnis}\n")

            verlauf.append({
                "role": "tool",
                "tool_call_id": aufruf["id"],
                "content": json.dumps(ergebnis, ensure_ascii=False),
            })

    print("Abbruch: zu viele Tool-Runden.")


if __name__ == "__main__":
    main()
