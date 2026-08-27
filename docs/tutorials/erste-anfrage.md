# 1 — Die erste Anfrage

**Ziel:** Du hast dem Modell eine Frage gestellt, die Antwort live mitgelesen und
es dazu gebracht, eine deiner eigenen Funktionen aufzurufen.

**Vorher:** [Endpunkt einrichten](../how-to/endpunkt-einrichten.md).

---

## Läuft überhaupt etwas?

```bash
cd First-API
Version-1/00_check.sh
```

```
Endpoint : https://llm-…/v1
Modell   : local-devstral-small2
Key      : sk-dio…hL4g

HTTP 200
Verfügbare Modelle:
  - local-devstral-small2
```

Ein `HTTP 401` bedeutet: Schlüssel falsch. Alles andere:
[Fehler suchen](../how-to/fehler-suchen.md).

---

## Die kleinstmögliche Anfrage

```bash
Version-1/01_chat_curl.sh "Was ist ein Token? Kurz."
```

Sieh dir das Skript an — es ist kürzer als seine Kommentare. Der Kern:

```bash
curl -s "$LLM_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"…","messages":[{"role":"user","content":"…"}]}'
```

Mehr ist eine „LLM-API" nicht: ein HTTP-POST mit JSON. Die Antwort ist JSON, und
`jq` holt den Text heraus.

---

## Die Antwort live mitlesen

```bash
Version-1/02_stream_curl.sh "Schreibe ein kurzes Gedicht über Hamburg."
```

Der einzige Unterschied im Body ist `"stream": true`. Statt einer Antwort kommen
viele kleine — Server-Sent Events, jede Zeile beginnt mit `data:`, am Ende steht
`data: [DONE]`. Das Skript setzt sie wieder zusammen.

Streaming ändert nichts am Ergebnis. Es ändert nur, wann der Mensch davor etwas
sieht — und das ist bei einem lokalen Modell auf eigener Hardware der Unterschied
zwischen „hängt" und „arbeitet".

---

## Dasselbe aus Python

```bash
python3 Version-1/03_chat.py "Was ist ein Prompt? Ein Satz."
python3 Version-1/04_stream.py "Erzähle eine kurze Geschichte über einen Roboter."
```

Beide nutzen `llm.py` — rund 90 Zeilen, nur Standardbibliothek, kein `pip install`.
Wirf einen Blick hinein: `urllib.request`, `json`, fertig.

---

## Das Modell hat kein Gedächtnis

```bash
python3 Version-1/05_dialog.py
```

Stelle zwei Fragen, die aufeinander aufbauen — etwa „Was ist Python?" und danach
„Und wer hat es erfunden?". Es funktioniert. Sieh dann nach, warum:

```python
verlauf.append({"role": "user", "content": eingabe})
...
verlauf.append({"role": "assistant", "content": antwort})
```

Bei jeder Anfrage wird der **komplette bisherige Verlauf** erneut mitgeschickt.
Das Modell erinnert sich an nichts; dein Programm erinnert sich für es. Deshalb
wächst der Token-Verbrauch mit der Länge des Gesprächs, und deshalb ist
„Gedächtnis" immer eine Eigenschaft deines Codes.

---

## Das Modell ruft deine Funktion auf

```bash
python3 Version-1/06_tools.py "Wie warm ist es in Hamburg und wie viel ist 17 * 23?"
```

```
  [Runde 1] Modell ruft auf: get_weather({'city': 'Hamburg'})
  [Runde 1] Ergebnis: {'stadt': 'Hamburg', 'temperatur_c': 18, …}
  [Runde 1] Modell ruft auf: calculate({'expression': '17 * 23'})
  [Runde 1] Ergebnis: {'ausdruck': '17 * 23', 'ergebnis': 391}

In Hamburg sind es aktuell 18°C. Und 17 mal 23 sind 391.
```

Der wichtigste Satz dieses Tutorials:

!!! warning "Das Modell führt nichts aus"
    Es sagt nur, welche Funktion es mit welchen Argumenten gern hätte.
    Ausgeführt wird sie von **deinem** Programm. Zwischen „das Modell will
    `get_weather('Hamburg')`" und „`get_weather` läuft" steht dein Code — und
    genau dort gehört jede Prüfung hin.

Version-3 baut vollständig auf diesem Mechanismus auf.

---

## Und mit dem offiziellen SDK?

```bash
pip install openai
python3 Version-1/07_openai_sdk.py "Nenne drei Vorteile eines selbst gehosteten LLM."
```

```python
client = OpenAI(base_url=llm.BASE_URL, api_key=llm.API_KEY)
```

Das ist der einzige Unterschied zu einem Aufruf gegen OpenAI. Der Endpunkt ist
OpenAI-kompatibel, also spricht jede Bibliothek und jedes Werkzeug, das mit
OpenAI spricht, auch mit diesem Modell. Warum das so viel wert ist, steht unter
[Warum OpenAI-kompatibel wichtig ist](../explanation/openai-kompatibel.md).

---

## Weiter

[Der erste Bericht](erster-bericht.md) — echte Daten, ein Harness, ein PDF.
