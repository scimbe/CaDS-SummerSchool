# Was Prüfen nicht kann

Version-2 prüft jede Zahl im generierten Text gegen die übergebenen Daten. Das
klingt lückenlos. Es ist es nicht — und der Fall, an dem es scheitert, ist
lehrreicher als die Fälle, die es fängt.

## Was die Prüfung leistet

```python
erlaubt = erlaubte_zahlen({"pm10": 23.0})
pruefe_text("Der Wert liegt bei 23 µg/m³.", erlaubt)   # []
pruefe_text("Der Wert liegt bei 42 µg/m³.", erlaubt)   # ['42']
```

Jede Zahl im Text muss in den Daten vorkommen. Erfundene Zahlen — der klassische
Fall — werden zuverlässig gefunden. Ausgenommen sind Zahlen, die zu einem Namen
gehören (PM10, PM2.5, NO₂) und Zählwörter bis zwölf.

## Wo sie versagt

Ein echter Testlauf. Das Modell schrieb:

> „Stuttgart weist mit einem Stickstoffdioxid-Wert von **18.2** µg/m³ die höchste
> Belastung auf."

Stuttgarts tatsächlicher NO₂-Wert lag bei 23,0. 18,2 war der **Mittelwert über
alle Städte** — und stand damit in den Daten. Die Prüfung ließ den Satz durch.

Er war trotzdem falsch.

!!! danger "Die Lücke"
    Die Prüfung erkennt **erfundene** Zahlen. Sie erkennt keine **falsch
    zugeordneten**. Für sie ist eine Zahl ein Zeichen in einer Menge, kein Wert
    mit einer Bedeutung.

Eine schärfere Prüfung müsste verstehen, welche Zahl zu welcher Stadt gehört —
also den Satz interpretieren. Damit hätte man das ursprüngliche Problem einmal
im Kreis herum wieder da: Man bräuchte ein Sprachmodell, um die Ausgabe des
Sprachmodells zu prüfen.

## Die Antwort: weniger übergeben

Statt eines besseren Prüfers ein engerer Auftrag.

Die **Kurzfassung** wird ohne jede Messzahl geschrieben:

```python
harness.schreibe_abschnitt(auftrag, vgl, notfalltext, mit_messwerten=False)
```

Der Auftrag nennt keine Werte mehr, nur Rangfolge und Einstufungen, und die Regel
lautet: *jede* Zahl im Text ist ein Verstoß. Damit wird aus einem Abgleich, der
Bedeutung bräuchte, eine Ja/Nein-Frage, die keine braucht.

Das Ergebnis liest sich nicht schlechter:

> Die Luftqualität in den untersuchten Städten wird als gut eingestuft, wobei
> keine Stadt die EU-Grenzwerte überschreitet. Köln ist die am stärksten
> belastete Stadt, wobei Feinstaub PM10 den Hauptschadstoff darstellt.

Die Zahlen stehen in der Tabelle direkt darunter. In einer Kurzfassung haben sie
ohnehin wenig verloren.

Die **Stadtabschnitte** bekommen weiterhin Zahlen — aber nur die einer einzigen
Stadt. Dort gibt es nichts zu verwechseln.

## Die allgemeine Regel

> **Statt zu hoffen, dass das Modell eine Unterscheidung trifft, entfernt man
> das, was verwechselt werden kann, aus dem Auftrag.**

Das ist unbequemer als eine Zeile im Prompt, weil man den Aufbau ändern muss. Es
ist die einzige Variante, die auch beim tausendsten Durchlauf hält.

## Zwei ehrliche Einschränkungen

**Falsch positive.** „Feinstaub PM2.5" enthält die Zahl 2.5. Ohne Ausnahmeliste
gilt jeder korrekte Satz über PM2.5 als Verstoß. Solche Ausnahmen sind
unvermeidlich — und jede ist ein kleines Loch.

**Prüfen ist kein Verstehen.** Ein Satz kann jede Prüfung bestehen und trotzdem
irreführend sein. Deshalb steht der Anhang mit den Rohdaten im Bericht: Am Ende
ist die Nachprüfbarkeit durch einen Menschen die letzte Instanz, nicht die
Prüffunktion.
