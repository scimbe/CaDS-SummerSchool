# Der Hebel

Version-3 hat einen Schieber mit drei Stellungen: **Formular**, **Vorschlag**,
**Direkt**. Er sieht aus wie eine Komforteinstellung. Er ist die zentrale
Entwurfsentscheidung.

## Das Missverständnis, das er auflöst

Bei „ein Sprachmodell steuert eine API" denken die meisten an eines von zwei
Extremen:

| | Klingt nach | Ist in Wahrheit |
|---|---|---|
| Freie Eingabe | mächtig, modern | unkontrollierbar, kaum zu testen |
| Festes Formular | sicher, langweilig | unbequem bei 84 Städten und fünf Schadstoffen |

Der Hebel sagt: Das ist keine Entweder-oder-Frage. Beide Wege füllen **dasselbe
Objekt** aus, und dieses Objekt hat in beiden Fällen dieselben Grenzen.

```json
{ "staedte": […], "schadstoffe": […], "sortierung": "…",
  "darstellung": "…", "titel": "…", "kommentar": true }
```

Der Prompt ist eine **Abkürzung durch das Formular**, kein zusätzliches Können.
Alles, was per Prompt erreichbar ist, ist auch per Klick erreichbar — nur
langsamer zu tippen. Und nichts, was per Klick unmöglich ist, wird per Prompt
möglich.

## Was der Hebel regelt und was nicht

Er regelt **nicht**, was das Modell darf. Das steht unveränderlich in
`HARNESS.md` und wird in `pruefe_plan()` durchgesetzt — in jeder Stufe gleich.

Er regelt, **wie viel Entscheidung man abgibt**:

| Stufe | Das Modell | Der Mensch |
|---|---|---|
| 0 Formular | läuft nicht | entscheidet alles |
| 1 Vorschlag | schlägt vor | prüft und bestätigt |
| 2 Direkt | schlägt vor und führt aus | sieht das Ergebnis |

Stufe 1 ist die Voreinstellung, und der sichtbare, änderbare Plan ist der
eigentliche Gewinn. Er verwandelt

> „Die KI hat irgendwas gemacht."

in

> „Das hat sie verstanden. Hier korrigiere ich es."

Das ist der Unterschied zwischen einem Werkzeug, dem man vertrauen muss, und
einem, mit dem man arbeiten kann.

## Warum das ein kleines Modell tragfähig macht

Die Aufgabe „fülle sechs Felder aus, jedes mit fester Wertemenge" ist klein
genug für ein kleines Modell. Die Aufgabe „schreibe eine Abfrage" ist es nicht.

Kommt trotzdem Unsinn, greift die Reparatur:

```
· Stadt „Gotham City" kennt die API nicht — entfernt.
· darstellung=„3d-globus" ist nicht erlaubt — „balken" gesetzt.
· Titel war länger als 80 Zeichen — gekürzt.
```

Reparieren statt ablehnen ist bewusst gewählt. Ein Plan mit einer erfundenen
Stadt ist zu 80 % brauchbar; ihn ganz zu verwerfen wäre unfreundlich. Aber jede
Korrektur wird angezeigt — stillschweigendes Reparieren wäre schlimmer als
Ablehnen, weil dann niemand mehr weiß, was eigentlich lief.

## Die Trennung im Code

`/api/plan` und `/api/run` sind zwei Endpunkte. Das ist keine Formalie:

- **`/api/plan`** ruft das Modell und ändert nichts.
- **`/api/run`** ruft kein Modell und liefert Daten.

Dazwischen passt ein Mensch. Und weil `/api/run` **jeden** Plan erneut prüft —
auch einen aus dem Formular —, gibt es keinen Weg an der Prüfung vorbei. Auch
nicht mit einem selbstgebauten POST.

## Übertragbar

Das Muster passt überall dort, wo freier Text eine Auswahl steuern soll: ein
Filter über einem Datenbestand, ein Report, eine Suche. Drei Regeln, mehr nicht:

1. Das Modell füllt ein Objekt mit abgeschlossenen Wertemengen.
2. Kennungen werden gegen eine Whitelist aufgelöst, nie übernommen.
3. Die Ausführung prüft erneut und zeigt jede Korrektur.
