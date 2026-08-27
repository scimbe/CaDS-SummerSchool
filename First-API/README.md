# First-API — CaDS Summer School

Drei Schritte von „ich habe einen API-Schlüssel" zu „das läuft und ich weiß, warum".
Modell ist `local-devstral-small2` auf einem selbst gehosteten, OpenAI-kompatiblen
Endpunkt. Die Fachdaten kommen von der kostenlosen Luftqualitäts-API von
[infranode.dev](https://infranode.dev/daten/luftqualitaet-api/) (Quelle: Umweltbundesamt).

📖 **Dokumentation: <https://scimbe.github.io/CaDS-SummerSchool/>**

| | Was entsteht | Kern |
|---|---|---|
| [**Version-1**](Version-1/) | Sieben kleine Skripte | Wie man den Endpunkt anspricht — curl, Python, Streaming, Tool-Calling |
| [**Version-2**](Version-2/) | Ein PDF-Bericht | Was ein **Harness** ist: rechnen lassen, formulieren lassen, prüfen |
| [**Version-3**](Version-3/) | Eine Weboberfläche | Der **Hebel** zwischen freier Eingabe und dem, was ein kleines Modell zuverlässig kann |

Die rote Linie durch alle drei Teile:

> **Ein kleines Modell wird nicht dadurch gut, dass man den Prompt verbessert,
> sondern dadurch, dass man ihm die Aufgaben abnimmt, die es nicht kann.**

## Loslegen

```bash
cp .env.example .env      # Endpunkt und Schlüssel eintragen
Version-1/00_check.sh     # Erreichbarkeit prüfen
```

Danach der Reihe nach durch `Version-1/`, `Version-2/`, `Version-3/`.
Jede Version hat eine eigene `README.md`.

Voraussetzungen: Python 3.10+, `curl` und `jq` für die Shell-Skripte, ein
installierter Browser für die PDF-Ausgabe in Version-2. **Keine pip-Pakete nötig** —
alles läuft mit der Standardbibliothek.

## Aufbau

```
First-API/
├── .env                 Endpunkt, Schlüssel, Modellname (nicht im Git)
├── Version-1/           Skripte: der Endpunkt
├── Version-2/           Harness: API → Auswertung → PDF
│   └── HARNESS.md       die Regeln, die das Programm einliest
├── Version-3/           Weboberfläche: Prompt steuert die API
│   └── HARNESS.md       die Regeln, die das Programm einliest
└── docs/                Quelle der Dokumentationsseite
```

## Lizenz und Quellen

Code: MIT. Luftdaten: Umweltbundesamt (UBA), Lizenz
[DL-DE BY 2.0](https://www.govdata.de/dl-de/by-2-0), bereitgestellt über infranode.dev.
