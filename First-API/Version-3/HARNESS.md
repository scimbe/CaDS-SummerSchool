# Harness-Regeln — Version-3

Diese Datei ist die **maßgebliche Beschreibung des Harness**. `planner.py` liest
sie beim Start ein und übernimmt daraus den Systemprompt und die Grenzen. Wer
diese Datei ändert, ändert das Verhalten der Anwendung — ohne eine Zeile Python
anzufassen. Dieselbe Idee wie `CLAUDE.md` oder `AGENTS.md` bei Coding-Agenten.

---

## Die eine Entscheidung

Ein kleines Modell soll eine API steuern. Man kann ihm dafür zwei sehr
verschiedene Dinge geben:

| | Was das Modell liefert | Was schiefgehen kann |
|---|---|---|
| Naiv | Code, URL oder fertiges HTML | Alles. Falsche Pfade, erfundene Städte, kaputtes Markup, im schlimmsten Fall ein Request, den niemand wollte. |
| Hier | **Einen Plan als JSON** | Nichts, was nicht vorher erlaubt war. |

Das Modell füllt ein Formular. Mehr nicht. Es sieht keine URL, es schreibt
keinen Code, es rührt die Daten nicht an. Jedes Feld des Plans hat eine
abgeschlossene Menge erlaubter Werte, und was nicht hineinpasst, wird vor der
Ausführung entfernt.

> **Der Prompt bestimmt, was das Modell will. Das Harness bestimmt, was möglich ist.**

---

## Der Plan

Das ist das einzige, was das Modell produziert:

```json
{
  "staedte":     ["hamburg", "muenchen"],
  "schadstoffe": ["pm10", "no2", "o3"],
  "sortierung":  "belastung_absteigend",
  "darstellung": "balken",
  "titel":       "Feinstaub und Stickoxide im Süden",
  "kommentar":   true
}
```

| Feld | Erlaubt | Bei Verstoß |
|---|---|---|
| `staedte` | 1–8 Slugs aus der Städteliste der API (84 Stück) | Auflösungsversuch über Name und Slug, sonst verwerfen |
| `schadstoffe` | Teilmenge von `pm10, pm25, no2, o3, so2` | Unbekannte verwerfen |
| `sortierung` | `belastung_absteigend`, `belastung_aufsteigend`, `name` | Standardwert |
| `darstellung` | `tabelle`, `balken`, `karten` | Standardwert |
| `titel` | Text, höchstens 80 Zeichen | Kürzen |
| `kommentar` | `true` / `false` | `false` |

Bleibt nach der Prüfung nichts übrig, gilt der Plan als gescheitert und die
Oberfläche zeigt den Formularzustand — nie eine leere Seite und nie eine
Fehlermeldung ohne Ausweg.

---

## Der Hebel

Die Oberfläche hat einen Schieber mit drei Stellungen. Er regelt **nicht**, was
das Modell darf — das steht oben und ist unveränderlich. Er regelt, wie viel
Entscheidung man ihm überlässt:

| Stufe | Name | Das Modell | Sinnvoll wenn |
|---|---|---|---|
| 0 | **Formular** | läuft gar nicht | Man weiß, was man will. Schnellster und zuverlässigster Weg. |
| 1 | **Vorschlag** | schlägt einen Plan vor, der Plan ist sichtbar und änderbar, nichts läuft ungefragt | Der Normalfall. Man sieht, was das Modell verstanden hat, bevor es zählt. |
| 2 | **Direkt** | schlägt vor und führt sofort aus | Man probiert schnell viel aus. |

Stufe 1 ist die Voreinstellung. Der sichtbare, editierbare Plan ist der
eigentliche Hebel: Er macht aus einem undurchsichtigen „die KI hat irgendwas
gemacht" ein nachvollziehbares „das hat sie verstanden, hier korrigiere ich es".

---

## Systemprompt

Dieser Block wird wörtlich als `system`-Nachricht geschickt:

```text
Du bist ein Formular-Ausfüller für eine Luftqualitäts-Anwendung.
Du rufst ausschließlich die Funktion plan_erstellen auf und antwortest nie mit Fließtext.
Du wählst nur aus den Werten, die in der Funktionsbeschreibung stehen.
Erfinde keine Städtenamen. Nennst du eine Stadt, die es nicht gibt, wird sie entfernt.
Nennt die Anfrage keine Stadt, wähle bis zu fünf große, zur Anfrage passende Städte.
Nennt die Anfrage keinen Schadstoff, wähle alle fünf.
```

---

## Grenzen

- `max_staedte: 8` — mehr Städte bedeuten mehr API-Aufrufe und eine unlesbare Seite
- `max_titel: 80`
- `max_versuche: 2` — so oft darf das Modell einen Plan nachbessern
- `temperature: 0.2` — ein Formular ist keine Kreativaufgabe
- `max_tokens: 400`

---

## Aufbereitung

Auch die Darstellung gehört ins Harness. Diese Tabelle liest `datatools.py` ein;
sie bestimmt die Farben der Einstufungen in allen drei Ansichten:

| Stufe | Farbe |
|---|---|
| sehr gut | `#2e7d32` |
| gut | `#7cb342` |
| mäßig | `#f9a825` |
| schlecht | `#ef6c00` |
| sehr schlecht | `#c62828` |
| unbekannt | `#9e9e9e` |

- `balken_bezug: index` — woran die Balkenlänge hängt. `index` bezieht sie auf die
  Obergrenze der Stufe „sehr schlecht", `grenzwert` auf den EU-Grenzwert.

Farbe ändern, Seite neu laden, fertig. Kein Python, kein Neustart des Servers
nötig — die Datei wird bei jedem Aufruf gelesen.

---

## Prüfen statt vertrauen

`planner.py` prüft jeden Plan gegen die Tabelle oben und **repariert** ihn, statt
ihn abzulehnen. Jede Korrektur wird protokolliert und in der Oberfläche unter
„Was das Harness korrigiert hat" angezeigt.

Häufigster echter Fall: Das Modell schreibt `"münchen"` oder `"Munich"` statt
`"muenchen"`. Die Auflösung über Name und Slug fängt das ab — deterministisch,
ohne das Modell erneut zu fragen.

Zweithäufigster Fall: Das Modell nennt eine Stadt, die die API nicht abdeckt.
Sie wird entfernt und im Protokoll benannt. Der Rest des Plans läuft trotzdem.

---

## Was das Modell nie tut

- Es sieht keine Messwerte und formuliert daraus keine Zahlen. Der optionale
  Kommentar wird **nach** der Auswertung erzeugt und darf nur die Zahlen
  nennen, die im Ergebnis stehen — dieselbe Prüfung wie in Version-2.
- Es erzeugt kein HTML und kein CSS. Die Darstellung ist eine Auswahl aus drei
  fertigen Ansichten, nicht ein vom Modell geschriebenes Layout.
- Es baut keine URLs. Slugs werden gegen die Städteliste aufgelöst.

Das ist der Grund, warum ein kleines Modell hier zuverlässig funktioniert: Es
bekommt eine Aufgabe in seiner Gewichtsklasse.
