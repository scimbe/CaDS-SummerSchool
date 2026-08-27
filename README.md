# CaDS Summer School

Kursmaterial der CaDS Summer School.
**Dokumentation: <https://scimbe.github.io/CaDS-SummerSchool/>**

## [First-API](First-API/)

Von der offenen API zum eigenen Harness, mit einem kleinen selbst gehosteten
Sprachmodell. Drei aufeinander aufbauende Schritte:

| | Was entsteht | Kern |
|---|---|---|
| [Version-1](First-API/Version-1/) | Sieben kleine Skripte | Wie man einen OpenAI-kompatiblen Endpunkt anspricht |
| [Version-2](First-API/Version-2/) | Ein PDF-Bericht | Was ein **Harness** ist: rechnen lassen, formulieren lassen, prüfen |
| [Version-3](First-API/Version-3/) | Eine Weboberfläche | Der **Hebel** zwischen freier Eingabe und dem, was ein kleines Modell kann |

Die rote Linie:

> **Ein kleines Modell wird nicht dadurch gut, dass man den Prompt verbessert,
> sondern dadurch, dass man ihm die Aufgaben abnimmt, die es nicht kann.**

Keine pip-Pakete nötig — alles läuft mit der Python-Standardbibliothek.

```bash
cd First-API
cp .env.example .env      # Endpunkt und Schlüssel eintragen
Version-1/00_check.sh
```

## Aufbau

```
CaDS-SummerSchool/
├── First-API/       Kursmaterial (Version-1 bis Version-3)
├── docs/            Quelle der Dokumentationsseite (MkDocs)
├── scripts/         Bilder für die Doku neu erzeugen
└── mkdocs.yml
```

## Dokumentation lokal bauen

```bash
python3 -m venv .venv && .venv/bin/pip install mkdocs-material
.venv/bin/mkdocs serve
```

## Lizenz und Quellen

Code: MIT. Luftdaten: Umweltbundesamt (UBA), Lizenz
[DL-DE BY 2.0](https://www.govdata.de/dl-de/by-2-0), bereitgestellt über
[infranode.dev](https://infranode.dev/).
