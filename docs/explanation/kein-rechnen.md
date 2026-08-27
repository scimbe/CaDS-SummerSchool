# Warum das Modell nicht rechnet

Ein Sprachmodell sagt voraus, welches Zeichen als nächstes plausibel ist. Bei
`17 * 23 =` ist `391` plausibel, aber `381` auch. Das Modell weiß nicht, welche
der beiden stimmt — es hat kein Verfahren, es hat eine Erwartung.

Bei einem großen Modell fällt das selten auf. Bei einem kleinen fällt es auf.
Und bei einem Bericht, den jemand liest und für richtig hält, ist „selten" zu oft.

## Was daraus folgt

Nicht: „Prompt schärfen." Sondern: **Die Aufgabe verschwindet.**

```python
# tools.py — das rechnet
belastung = round(wert / SCHWELLEN[schadstoff][1], 2)
gesamtstufe = max(werte, key=lambda w: (w["stufe_index"], w["belastung"]))
```

```python
# harness.py — das formuliert
"- Feinstaub PM10: 23.0 µg/m³ -> Stufe 'gut'"
"Gesamteinstufung: 'gut', bestimmt durch Feinstaub PM10."
```

Das Modell sieht nur die rechte Spalte: fertige Zahlen mit fertigen Einstufungen.
Es kann sich nicht verrechnen, weil es nicht rechnet.

## Was das Modell dann noch tut

Genug. Vergleiche:

> Hamburg: PM10 23.0 gut, PM2.5 9.0 sehr gut, NO₂ 16.0 sehr gut, O₃ 79.0 gut.
> Gesamt: gut, Treiber PM10.

mit:

> Hamburg weist eine gute Luftqualität auf, wobei der Feinstaub PM10 mit 23,0
> µg/m³ den ausschlaggebenden Wert darstellt. Die übrigen Messwerte liegen
> durchweg im sehr guten Bereich.

Der zweite Text ist die Arbeit, die man nicht in Schablonen gießen will — Auswahl
dessen, was erwähnenswert ist, Satzbau, Übergänge. Dafür ist das Modell da.

## Auch das Sortieren gehört zum Rechnen

Eine Rangfolge ist eine Kette von Vergleichen. Ein Modell, das eine Liste
sortieren soll, macht dieselben Fehler wie beim Rechnen — nur unauffälliger,
weil eine falsch sortierte Liste immer noch wie eine Liste aussieht.

In Version-2 sortiert `vergleich()`, und das Ergebnis wird dem Modell **mit
Platznummern** übergeben:

```
- Platz 1: Hamburg, Stufe 'gut', ausschlaggebend Feinstaub PM10
- Platz 2: Köln, …
```

Sogar dann kann es schiefgehen — in einem Testlauf nannte das Modell die
drittplatzierte Stadt als beste. Die Antwort darauf war nicht ein besserer
Prompt, sondern eine zusätzliche, unmissverständliche Zeile:

```
Am stärksten belastet ist Hamburg, am geringsten München.
```

Was das Modell nicht ableiten muss, kann es nicht falsch ableiten.

## Die Gegenprobe

Nimm in `HARNESS.md` die Zeile „Rechne nichts aus" aus dem Systemprompt und lass
den Bericht neu erzeugen. Die Tabelle „Wie dieser Bericht entstanden ist" füllt
sich mit beanstandeten Zahlen: Prozentangaben, Differenzen, Mittelwerte — alles
plausibel, nichts davon in den Daten.

Die Prüfung fängt es ab. Aber sie fängt es ab, *nachdem* es passiert ist — und
sie fängt nur das ab, was sie sehen kann. Siehe
[Was Prüfen nicht kann](grenzen-der-pruefung.md).
