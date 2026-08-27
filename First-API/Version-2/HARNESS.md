# Harness-Regeln — Version-2

Diese Datei ist die **maßgebliche Beschreibung des Harness**. Sie ist nicht nur
Dokumentation: `harness.py` liest sie beim Start ein und übernimmt daraus den
Systemprompt und die Grenzwerte. Wer diese Datei ändert, ändert das Verhalten
des Programms — ohne eine Zeile Python anzufassen.

Das ist dieselbe Idee wie `CLAUDE.md` oder `AGENTS.md` bei Coding-Agenten: die
Regeln, nach denen ein Modell arbeiten soll, gehören in eine lesbare Datei
neben den Code und nicht verstreut in Stringliterale.

---

## Rollenverteilung

Die einzige Regel, auf die es wirklich ankommt:

| Aufgabe | Zuständig | Warum |
|---|---|---|
| Daten holen | `air_api.py` | Eine API-Antwort ist eine Tatsache, keine Meinung. |
| Rechnen, einstufen, sortieren | `tools.py` | Ein kleines Modell rechnet unzuverlässig und vergleicht Zahlen gerne falsch. |
| Formulieren | Sprachmodell | Genau das kann es gut — und nur das wird ihm überlassen. |
| Prüfen und Nachfassen | `harness.py` | Vertrauen ist keine Architektur. |
| Setzen und Drucken | `report.py`, `pdf.py` | Layout ist deterministisch. |

Das Modell bekommt **fertig gerechnete Zahlen** und gießt sie in Sätze. Es
bekommt nie die Rohdaten und nie den Auftrag, etwas auszurechnen.

---

## Systemprompt

Dieser Block wird wörtlich als `system`-Nachricht an das Modell geschickt:

```text
Du schreibst kurze, sachliche Abschnitte für einen Umweltbericht auf Deutsch.
Strikte Regeln: Verwende ausschließlich die Zahlen, die dir im Auftrag genannt werden.
Rechne nichts aus, schätze nichts, ergänze keine Werte aus deinem Wissen.
Keine Überschriften, keine Aufzählungen, keine Emojis — nur Fließtext.
```

---

## Grenzen

Diese Werte liest `harness.py` aus dieser Datei aus:

- `max_versuche: 3` — so oft darf ein Abschnitt neu geschrieben werden
- `temperature: 0.3` — niedrig, weil Bericht und nicht Belletristik
- `max_tokens_kurzfassung: 320`
- `max_tokens_stadt: 220`

---

## Aufbereitung

Auch die Darstellung ist Teil des Harness, nicht Geschmackssache im Code. Diese
Tabelle liest `report.py` ein — sie bestimmt die Farben der Einstufungen im PDF,
in den Balken und in den Marken:

| Stufe | Farbe |
|---|---|
| sehr gut | `#2e7d32` |
| gut | `#7cb342` |
| mäßig | `#f9a825` |
| schlecht | `#ef6c00` |
| sehr schlecht | `#c62828` |
| unbekannt | `#9e9e9e` |

Zusätzlich:

- `akzent: #204c86` — Überschriften, Tabellenköpfe, Rahmen
- `balken_bezug: index` — woran die Balkenlänge hängt. `index` bezieht sie auf die
  Obergrenze der Stufe „sehr schlecht", `grenzwert` auf den EU-Grenzwert.

Ändere eine Farbe hier und erzeuge den Bericht neu: Das PDF sieht anders aus,
ohne dass eine Zeile Python angefasst wurde. Das ist derselbe Mechanismus wie
beim Systemprompt und aus demselben Grund — was das Ergebnis prägt, gehört in
eine lesbare Datei neben den Code.

---

## Prüfregeln

Nach jeder Antwort des Modells:

1. **Zahlenprüfung.** Jede Zahl im Text muss in den übergebenen Daten vorkommen.
   Taucht eine Zahl auf, die es dort nicht gibt, gilt der Abschnitt als
   beanstandet. Ausgenommen sind Zahlen, die Teil eines Namens sind (PM10,
   PM2.5, NO₂, O₃, SO₂) sowie Zählwörter bis zwölf.
2. **Formatprüfung.** Markdown-Überschriften werden entfernt; das Layout kommt
   aus `report.py`, nicht aus dem Modell.
3. **Nachfassen.** Bei einer Beanstandung bekommt das Modell die konkreten
   Zahlen genannt und schreibt den Abschnitt neu. Bis zu `max_versuche` mal.

---

## Notfallregel

Bleibt ein Abschnitt nach `max_versuche` Versuchen beanstandet, oder ist der
Endpunkt nicht erreichbar, schreibt das Harness den Satz selbst aus den Daten
(`notfall_kurzfassung`, `notfall_stadt`).

**Ein Bericht ohne Modell ist besser als ein Bericht mit falschen Zahlen.**

---

## Nachweispflicht

Jeder erzeugte Bericht enthält verpflichtend:

- eine Tabelle „Wie dieser Bericht entstanden ist" mit Versuchszahl, beanstandeten
  Zahlen und der Angabe, ob der Text vom Modell oder vom Harness stammt;
- einen **Anhang mit den unveränderten API-Antworten**, damit jede Zahl im
  Bericht bis zur Quelle zurückverfolgt werden kann;
- die Attribution der Datenquelle (UBA, DL-DE BY 2.0).

---

## Zahlen nur dort, wo sie eindeutig sind

Die Zahlenprüfung erkennt **erfundene** Zahlen, aber keine **falsch zugeordneten**.
Ein Mittelwert über alle Städte und ein Messwert einer einzelnen Stadt sehen für
das Modell gleich aus — beide stehen in den Daten, beide bestehen die Prüfung.
In einem Testlauf schrieb das Modell den Mittelwert 18,2 µg/m³ der Stadt
Stuttgart zu, deren tatsächlicher Wert bei 23,0 lag.

Die Konsequenz ist keine schärfere Prüfung, sondern ein engerer Auftrag:

> Die **Kurzfassung** wird ohne jede Messzahl geschrieben
> (`mit_messwerten=False`). Sie ordnet nur qualitativ ein — „am höchsten",
> „am geringsten". Jede Zahl im Text gilt dort als Verstoß.
>
> Die **Stadtabschnitte** bekommen Zahlen, aber nur die einer einzigen Stadt.
> Dort gibt es nichts zu verwechseln.

Das ist die allgemeine Regel hinter diesem Harness: Statt zu hoffen, dass das
Modell eine Unterscheidung trifft, entfernt man das, was verwechselt werden kann,
aus dem Auftrag.
