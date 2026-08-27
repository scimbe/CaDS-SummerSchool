# Einstufung und Grenzwerte

Drei verschiedene Zahlen, die leicht verwechselt werden: die Stufen des
UBA-Index, die EU-Grenzwerte und der Belastungsindex dieses Projekts.

## UBA-Luftqualitätsindex

Obergrenzen je Stufe, in µg/m³. Quelle: Umweltbundesamt, „Luftqualitätsindex".

| Schadstoff | sehr gut | gut | mäßig | schlecht | sehr schlecht |
|---|---|---|---|---|---|
| PM10 | ≤ 20 | ≤ 35 | ≤ 50 | ≤ 100 | > 100 |
| PM2.5 | ≤ 10 | ≤ 20 | ≤ 25 | ≤ 50 | > 50 |
| NO₂ | ≤ 20 | ≤ 40 | ≤ 100 | ≤ 200 | > 200 |
| O₃ | ≤ 60 | ≤ 120 | ≤ 180 | ≤ 240 | > 240 |
| SO₂ | ≤ 50 | ≤ 125 | ≤ 350 | ≤ 500 | > 500 |

Im Code: `SCHWELLEN` in `tools.py` (Version-2) und `datatools.py` (Version-3).

**Die Stufe einer Stadt ist ihr schlechtester Einzelwert**, nicht der Mittelwert.
So macht es der UBA-Index auch — und aus gutem Grund: Ein Mittelwert ließe einen
sehr guten Wert einen sehr schlechten aufwiegen, was für die Luft, die man
einatmet, nicht zutrifft.

## EU-Grenzwerte

| Schadstoff | Wert | Art |
|---|---|---|
| PM10 | 40 µg/m³ | Jahresmittel |
| PM2.5 | 25 µg/m³ | Jahresmittel |
| NO₂ | 40 µg/m³ | Jahresmittel |
| O₃ | 120 µg/m³ | Zielwert, 8-Stunden-Mittel |

Im Code: `EU_GRENZWERTE`.

!!! danger "Ein Einzelmesswert verletzt keinen Jahresmittelwert"
    Wenn ein Bericht „über EU-Grenzwert" anzeigt, heißt das: **dieser eine
    Messwert** liegt über einer Zahl, die als Jahresmittel definiert ist. Das ist
    eine Einordnung, keine Feststellung einer Überschreitung. Der Hinweis steht
    deshalb in jedem Bericht und in der Oberfläche im Fuß.

## Belastungsindex

Eine Zahl dieses Projekts, nicht des UBA:

```
belastung = messwert ÷ Obergrenze der Stufe "gut"
```

Beispiele: PM10 23 µg/m³ ÷ 35 = **0,66**. Ozon 79 ÷ 120 = **0,66**.

| Wert | Bedeutung |
|---|---|
| < 0,6 | deutlich im guten Bereich |
| ~ 1,0 | genau an der Grenze zu „mäßig" |
| > 1,0 | jenseits von „gut" |

**Wozu?** Ohne ihn ist die Rangfolge bei gleicher Stufe alphabetisch — also
willkürlich. Vier Städte mit der Einstufung „gut" ließen sich sonst nicht
ordnen, und ein Modell, das eine solche Liste zusammenfasst, nennt prompt die
falsche Stadt als beste. Der Index macht Schadstoffe untereinander vergleichbar:
79 µg/m³ Ozon und 23 µg/m³ Feinstaub sind ohne Bezugsgröße zwei Zahlen ohne
Beziehung.

Der Index einer **Stadt** ist der ihres schlechtesten Einzelwerts.

!!! note "Grenze der Vergleichbarkeit"
    Städte messen unterschiedliche Schadstoffe. Eine Stadt ohne Ozonmessung kann
    keinen hohen Ozonindex haben. Der Vergleich ist also nur so gut wie die
    Abdeckung — deshalb nennt jeder Stadtabschnitt die fehlenden Schadstoffe.

## Balkenlängen

Zwei Bezugsgrößen, einstellbar in `HARNESS.md` über `balken_bezug`:

| Wert | Balken = | Aussage |
|---|---|---|
| `index` | Wert ÷ Obergrenze „sehr schlecht" | Abstand zum Extremfall |
| `grenzwert` | Wert ÷ EU-Grenzwert | Abstand zur rechtlichen Grenze |

Bei identischen Messwerten schlagen die Balken mit `grenzwert` deutlich weiter
aus. Der Vergleich steht unter
[Das Harness anpassen](../how-to/harness-anpassen.md#die-wirkung-im-pdf).
