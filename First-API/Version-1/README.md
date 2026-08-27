# Version-1 — Der Endpunkt

Sieben Skripte, jedes zeigt genau eine Sache. In dieser Reihenfolge durchgehen.

```bash
cp ../.env.example ../.env    # einmalig: Schlüssel eintragen
./00_check.sh
```

| Skript | Zeigt |
|---|---|
| `00_check.sh` | Läuft der Endpunkt, stimmt der Schlüssel, welche Modelle gibt es |
| `01_chat_curl.sh` | Die kleinstmögliche Anfrage — ein `curl`, eine Antwort |
| `02_stream_curl.sh` | `"stream": true` — die Antwort kommt Token für Token |
| `03_chat.py` | Dasselbe aus Python, ohne Zusatzpakete |
| `04_stream.py` | Streaming in Python |
| `05_dialog.py` | Mehrere Runden — und warum das Modell kein Gedächtnis hat |
| `06_tools.py` | Tool-Calling: das Modell ruft **deine** Funktionen auf |
| `07_openai_sdk.py` | Derselbe Endpunkt mit dem offiziellen `openai`-SDK |

`llm.py` ist der gemeinsame Mini-Client: rund 90 Zeilen, nur Standardbibliothek,
damit man einmal gesehen hat, dass hinter „LLM-API" ein HTTP-POST mit JSON steckt.

## Was hängen bleiben soll

**Der Endpunkt ist OpenAI-kompatibel.** Das ist keine Nebensache, sondern der
Grund, warum das hier funktioniert: Jede Bibliothek und jedes Werkzeug, das mit
OpenAI spricht, spricht auch mit diesem Modell. Man ändert `base_url` und
`api_key` — sonst nichts. Siehe `07_openai_sdk.py`.

**Das Modell hat kein Gedächtnis.** In `05_dialog.py` wird bei jeder Anfrage der
komplette Verlauf erneut mitgeschickt. Deshalb wächst der Token-Verbrauch mit der
Länge des Gesprächs, und deshalb ist „das Modell erinnert sich" immer eine
Eigenschaft deines Codes, nie des Modells.

**Tool-Calling führt nichts aus.** Das Modell sagt nur, welche Funktion es mit
welchen Argumenten gern hätte. Ausgeführt wird sie von deinem Programm — siehe die
Schleife in `06_tools.py`. Darauf baut Version-3 auf.
