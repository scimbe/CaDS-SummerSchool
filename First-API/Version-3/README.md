# Version-3 — Der Hebel

Eine Weboberfläche, in der ein Prompt die API steuert.

```bash
python3 server.py          # http://localhost:8000
python3 server.py 8080     # anderer Port
```

Keine Abhängigkeiten, kein Build-Schritt: `http.server` im Rücken, Vanilla-JS
vorne.

## Der Hebel

Ein Schieber mit drei Stellungen. Er regelt **nicht**, was das Modell darf — das
steht unveränderlich in [`HARNESS.md`](HARNESS.md). Er regelt, wie viel
Entscheidung man ihm überlässt:

| Stufe | Das Modell | Sinnvoll wenn |
|---|---|---|
| **0 Formular** | läuft gar nicht | Man weiß, was man will |
| **1 Vorschlag** | schlägt einen Plan vor, sichtbar und änderbar | Der Normalfall, Voreinstellung |
| **2 Direkt** | schlägt vor und führt sofort aus | Schnell viel ausprobieren |

## Das Modell füllt ein Formular

Es erzeugt kein HTML, keinen Code und keine URL — nur dieses Objekt:

```json
{ "staedte": ["hamburg"], "schadstoffe": ["pm10"],
  "sortierung": "belastung_absteigend", "darstellung": "balken",
  "titel": "…", "kommentar": true }
```

Jedes Feld hat eine abgeschlossene Menge erlaubter Werte. Was nicht hineinpasst,
entfernt `pruefe_plan()` vor der Ausführung — und zwar reparierend, nicht
ablehnend: `"München"` wird zu `"muenchen"`, `"Gotham City"` fliegt raus, der
Rest läuft. Jede Korrektur steht in der Oberfläche unter „Was das Harness
korrigiert hat".

## Dateien

| Datei | Aufgabe |
|---|---|
| `HARNESS.md` | Die Regeln. Wird von `planner.py` eingelesen |
| `air_api.py` | Städteliste (= Whitelist) und Messwerte |
| `datatools.py` | Einstufen, sortieren, Kennzahlen — ohne Modell |
| `planner.py` | Prompt → Plan, Prüfung, Reparatur, optionaler Kommentar |
| `server.py` | `/api/plan`, `/api/run`, statische Dateien |
| `static/` | Oberfläche |

`/api/plan` und `/api/run` sind getrennt. Das ist der Hebel im Code: Planen und
Ausführen sind zwei Schritte, und dazwischen darf ein Mensch schauen.

## Beispiele verlinken

Zustände lassen sich als URL weitergeben — praktisch für Kursunterlagen:

```
?stufe=0&darstellung=karten&staedte=hamburg,koeln
?stufe=2&prompt=Ozon%20im%20Ruhrgebiet
```
