# Endpunkt einrichten

## Zugangsdaten eintragen

```bash
cd First-API
cp .env.example .env
```

`.env` öffnen und ausfüllen:

```bash
LLM_BASE_URL=https://llm-34a13a96.bunsenbrenner.org/v1
LLM_API_KEY=sk-…
LLM_MODEL=local-devstral-small2
```

Drei Punkte, die oft Zeit kosten:

- **`/v1` gehört ans Ende der URL.** Ohne den Pfad landen die Anfragen im Leeren.
- **Kein Anführungszeichen um die Werte.** Die Datei wird zeilenweise gelesen, ein
  `"` wird Teil des Schlüssels.
- **`.env` ist in `.gitignore`.** Sie darf da bleiben.

## Prüfen

```bash
Version-1/00_check.sh
```

![Ausgabe von 00_check.sh](../assets/v1-check.png)

| Ausgabe | Bedeutung |
|---|---|
| `HTTP 200` + Modellliste | Alles in Ordnung |
| `HTTP 401` | Schlüssel falsch oder abgelaufen |
| `HTTP 404` | `/v1` fehlt in der URL, oder der Pfad stimmt nicht |
| `curl: (6)` | Hostname unbekannt — Tippfehler in der URL |
| Zeitüberschreitung | Endpunkt nicht erreichbar; VPN oder Netzwerk prüfen |

## Werte im Terminal überschreiben

Umgebungsvariablen gewinnen gegen `.env`. Praktisch zum Ausprobieren:

```bash
LLM_MODEL=anderes-modell Version-1/01_chat_curl.sh "Test"
```

Das nutzt auch der Ausfalltest in
[Der erste Bericht](../tutorials/erster-bericht.md#den-notfallplan-auslosen):

```bash
LLM_BASE_URL=https://localhost:1/v1 python3 run.py
```

## Wo die Werte gelesen werden

| Ort | Datei |
|---|---|
| Shell-Skripte | `Version-1/_common.sh` |
| Python | `llm.py` (in jeder Version dieselbe Datei) |

Beide suchen `.env` neben sich und in den Elternordnern. Deshalb genügt **eine**
Datei in `First-API/` für alle drei Versionen.
