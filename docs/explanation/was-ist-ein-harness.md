# Was ein Harness ist

Ein Harness ist **alles, was nicht das Modell ist**: die Aufgabenteilung, die
Prompts, die Prüfungen, die Wiederholung bei Fehlern und der Notfallplan.

Der Begriff kommt aus dem Testbau — *test harness*, das Gestell, in das ein
Prüfling eingespannt wird. Das trifft es: Das Modell ist eingespannt. Es kann
sich in eine Richtung bewegen und in andere nicht.

## Warum das der entscheidende Teil ist

Die naheliegende Reaktion auf ein schwaches Ergebnis ist, den Prompt zu
verbessern. Das hilft ein Stück weit und hört dann auf zu helfen — irgendwann
steht in der Anweisung schon alles Richtige, und das Modell hält sich trotzdem
nicht daran.

Ab da hilft nur noch, die Aufgabe zu ändern:

| Statt | Besser |
|---|---|
| „Bitte rechne sorgfältig" | Nicht rechnen lassen |
| „Nenne nur echte Städte" | Gegen eine Liste prüfen und reparieren |
| „Erfinde keine Zahlen" | Nach der Antwort jede Zahl gegen die Daten prüfen |
| „Antworte im JSON-Format" | Tool-Calling mit Schema erzwingen |

Jede Zeile links ist eine Bitte. Jede Zeile rechts ist eine Eigenschaft des
Systems. Bitten skalieren mit der Modellgröße, Eigenschaften nicht — und genau
deshalb funktioniert hier ein kleines Modell.

## Die Aufgabenteilung

In allen drei Versionen dieselbe:

| Aufgabe | Wer | Warum |
|---|---|---|
| Daten holen | Code | Eine API-Antwort ist eine Tatsache. |
| Rechnen, sortieren, einstufen | Code | Kleine Modelle rechnen unzuverlässig. |
| Formulieren | Modell | Genau das kann es gut. |
| Prüfen und Nachfassen | Code | Vertrauen ist keine Architektur. |
| Layout und Ausgabe | Code | Darstellung ist deterministisch. |

Das Modell bekommt einen schmalen Streifen in der Mitte. Der ist echt und nicht
ersetzbar — die Absätze in Version-2 liest sich niemand gern als
Schablonentext —, aber er ist schmal.

## Der Test, ob es ein Harness ist

**Nimm das Modell weg. Was bleibt übrig?**

```bash
LLM_BASE_URL=https://localhost:1/v1 python3 run.py
```

In Version-2 entsteht der Bericht trotzdem: alle Zahlen, alle Einstufungen, alle
Balken, der Anhang. Nur die Sprache ist hölzern, weil die Notfalltexte aus
Schablonen kommen.

Wenn beim selben Test eine Ausnahme fliegt oder eine leere Seite herauskommt,
wurde kein Harness gebaut, sondern eine Abhängigkeit.

## Was ein Harness nicht ist

**Kein Prompt-Sammelbecken.** Ein längerer Systemprompt ist kein Harness. Er ist
eine längere Bitte.

**Keine Fehlerbehandlung.** `try/except` um einen Modellaufruf fängt ab, dass der
Aufruf scheitert — nicht, dass er gelingt und falsch ist. Der interessante Fall
ist der zweite.

**Keine Frage der Modellgröße.** Ein großes Modell mit schlechtem Harness
erzeugt schöner formulierte falsche Zahlen.
