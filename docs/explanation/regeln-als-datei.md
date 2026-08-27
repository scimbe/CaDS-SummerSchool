# Regeln in einer Datei

Version-2 und Version-3 haben je eine `HARNESS.md`. Sie ist keine Dokumentation
neben dem Code — sie wird beim Start eingelesen und bestimmt das Verhalten.

```python
SYSTEM, GRENZEN = _lies_regeln()          # aus HARNESS.md
FARBEN, AKZENT, BALKEN_BEZUG = _lies_darstellung()
```

Dasselbe Muster wie `CLAUDE.md` oder `AGENTS.md` bei Coding-Agenten: Die Regeln,
nach denen ein Modell arbeiten soll, stehen in einer lesbaren Datei neben dem
Code.

## Warum nicht einfach im Code

**Weil Prompts sonst niemand findet.** Ein Systemprompt als Stringliteral
zwischen zwei Funktionen ist für alle unsichtbar, die nicht in dieser Datei
lesen. In `HARNESS.md` steht er unter einer Überschrift.

**Weil man sonst nicht diskutieren kann.** Ein Systemprompt ist eine fachliche
Festlegung, keine technische. Ob ein Bericht „sachlich" oder „knapp" klingen soll,
entscheidet nicht, wer Python schreibt. Eine Markdown-Datei kann jemand ändern,
der kein Python kann.

**Weil Dokumentation sonst veraltet.** Der übliche Zustand: Der Prompt im Code
wurde dreimal geändert, die Beschreibung im Wiki einmal. Wenn die Beschreibung
*die Quelle* ist, kann sie nicht auseinanderlaufen.

**Weil man sonst nicht ausprobieren kann.** Ton ändern, `run.py` starten,
vergleichen. Kein Editor mit Syntaxhervorhebung nötig, kein Neustart eines
Servers — in Version-3 wird die Datei bei jedem Aufruf gelesen.

## Was drinsteht

| Abschnitt | Bestimmt |
|---|---|
| Rollenverteilung | Wer was macht — als Tabelle, nachlesbar |
| Systemprompt | Der Text, der wörtlich geschickt wird |
| Grenzen | Versuche, Temperatur, Token, Höchstzahlen |
| Aufbereitung | Farbskala, Akzentfarbe, Bezug der Balken |
| Prüfregeln | Was nach der Antwort geprüft wird |
| Notfallregel | Was passiert, wenn nichts klappt |

Dass auch die **Farben** dort stehen, ist kein Zufall. Die Darstellung entscheidet
mit, was ein Leser sieht — dieselben Messwerte wirken mit einer Ampelskala anders
als mit einer einfarbigen. Diese Entscheidung gehört sichtbar in eine Datei und
nicht versteckt in ein Stylesheet. Der Vergleich steht unter
[Das Harness anpassen](../how-to/harness-anpassen.md#die-wirkung-im-pdf).

## Die Grenze

Was das Modell **auslösen** darf, steht nicht in der Datei — es wird in
`planner.py` geprüft. `HARNESS.md` beschreibt die erlaubten Darstellungen,
durchgesetzt werden sie in Python:

```python
DARSTELLUNGEN = ["tabelle", "balken", "karten"]
```

Das ist Absicht. Eine Textdatei, die den Wirkungskreis eines Modells erweitern
kann, ist keine Konfiguration mehr, sondern eine Angriffsfläche. Konfigurierbar
ist, wie sich das System innerhalb seiner Grenzen verhält — nicht, wo die Grenzen
liegen.

## In der Oberfläche sichtbar

Version-3 zeigt die Datei im Reiter **Regeln des Harness** — geliefert von
`/api/harness`, also genau die Datei, die `planner.py` gelesen hat. Wer die
Anwendung benutzt, kann nachlesen, nach welchen Regeln sie arbeitet, ohne ins
Repository zu schauen.

Das ist die eigentliche Pointe: Ein Harness, das man nicht lesen kann, ist für
alle außer seinem Autor dasselbe wie kein Harness.
