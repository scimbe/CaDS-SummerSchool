# CaDS Summer School — First-API

**Von der offenen API zum eigenen Harness, mit einem kleinen selbst gehosteten Sprachmodell.**

Drei aufeinander aufbauende Schritte. Am Ende steht eine Weboberfläche, in der
ein Satz freier Text eine echte API steuert — und man kann erklären, warum das
zuverlässig funktioniert, obwohl das Modell klein ist.

Das Modell ist `local-devstral-small2` auf einem eigenen, OpenAI-kompatiblen
Endpunkt. Die Fachdaten kommen aus dem Messnetz des Umweltbundesamts, abgerufen
über die kostenlose, schlüssellose
[Luftqualitäts-API von infranode.dev](https://infranode.dev/daten/luftqualitaet-api/).

---

## Hier anfangen

<div class="grid cards" markdown>

- :material-school: **[Tutorials](tutorials/index.md)**

    Noch nichts davon gemacht. Der Reihe nach: erste Anfrage, erster Bericht,
    erste Oberfläche.

- :material-wrench: **[How-to](how-to/index.md)**

    Endpunkt einrichten, Auswahl ändern, Harness anpassen, Fehler suchen, auf
    eigene Daten übertragen.

- :material-book-open-variant: **[Referenz](reference/index.md)**

    Alle Dateien, alle Felder, alle Schwellenwerte, die Endpunkte im Detail.

- :material-lightbulb: **[Erklärung](explanation/index.md)**

    Was ein Harness ist, warum das Modell nicht rechnen darf, was Prüfen nicht
    leisten kann, und warum die Regeln in einer Markdown-Datei stehen.

</div>

---

## Die drei Versionen

| | Was entsteht | Was man danach kann |
|---|---|---|
| **Version-1** | Sieben kleine Skripte | Den Endpunkt ansprechen — curl, Python, Streaming, Tool-Calling |
| **Version-2** | Ein PDF-Bericht | Ein Harness bauen: rechnen lassen, formulieren lassen, prüfen |
| **Version-3** | Eine Weboberfläche | Freien Text sicher auf eine API abbilden |

---

## Die eine Idee

Der naheliegende Gedanke bei einem kleinen Modell ist, den Prompt zu verbessern.
Das hilft ein Stück weit und hört dann auf zu helfen. Was tatsächlich trägt, ist
die Aufgabenteilung:

> **Ein kleines Modell wird nicht dadurch gut, dass man den Prompt verbessert,
> sondern dadurch, dass man ihm die Aufgaben abnimmt, die es nicht kann.**

Konkret, in allen drei Versionen dasselbe Muster:

| Aufgabe | Wer | Warum |
|---|---|---|
| Daten holen | Code | Eine API-Antwort ist eine Tatsache. |
| Rechnen, sortieren, einstufen | Code | Kleine Modelle rechnen unzuverlässig und vergleichen Zahlen gerne falsch. |
| Formulieren | Modell | Genau das kann es gut — und nur das bekommt es. |
| Prüfen und Nachfassen | Code | Vertrauen ist keine Architektur. |
| Layout und Ausgabe | Code | Darstellung ist deterministisch. |

Das Ganze zusammen — die Aufgabenteilung, die Prompts, die Prüfungen, die
Wiederholung bei Fehlern und der Notfallplan — heißt **Harness**. Es ist alles,
was *nicht* das Modell ist, und es entscheidet über die Qualität des Ergebnisses
weit stärker als die Wahl des Modells.

In Version-2 und Version-3 steht das Harness ausdrücklich in einer Datei:
[`HARNESS.md`](reference/version-2.md#harnessmd). Sie ist nicht Dokumentation
neben dem Code, sondern wird beim Start eingelesen — wer sie ändert, ändert das
Verhalten.

---

## Voraussetzungen

- Python 3.10 oder neuer
- `curl` und `jq` für die Shell-Skripte in Version-1
- Ein installierter Browser (Chrome, Chromium oder Edge) für die PDF-Ausgabe in Version-2
- Zugang zum Endpunkt: URL, Schlüssel, Modellname

**Keine pip-Pakete nötig.** Alles läuft mit der Standardbibliothek — auch der
Webserver in Version-3. Das ist Absicht: Man soll sehen können, dass hinter
„LLM-Anwendung" ein HTTP-POST mit JSON steckt und sonst nichts.

---

## Quellen und Lizenz

Code: MIT. Luftdaten: Umweltbundesamt (UBA), Lizenz
[DL-DE BY 2.0](https://www.govdata.de/dl-de/by-2-0), durchgereicht von
[infranode.dev](https://infranode.dev/). Quelle, Lizenz-URL und Zeitstempel
stehen in jeder API-Antwort und werden in jedem erzeugten Bericht mitgeführt.
