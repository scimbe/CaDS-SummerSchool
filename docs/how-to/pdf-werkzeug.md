# PDF-Erzeugung umstellen

`pdf.py` probiert der Reihe nach, was auf dem System vorhanden ist. Die erste
Möglichkeit, die ein brauchbares PDF liefert, gewinnt.

| Reihenfolge | Werkzeug | Anmerkung |
|---|---|---|
| 1 | Chrome / Chromium / Edge, headless | Beste Darstellung, fast überall vorhanden |
| 2 | `weasyprint` | `pip install weasyprint` |
| 3 | `wkhtmltopdf` | Älteres CSS, Balken können abweichen |
| 4 | `cupsfilter` | macOS-Bordmittel, kein modernes CSS — Notnagel |

Welches benutzt wurde, steht in der Abschlusszeile:

```
Fertig in 21.0s -> output/bericht.pdf  (167 KB, via Google Chrome)
```

## Einen anderen Browser erzwingen

In `pdf.py` steht die Suchliste ganz oben:

```python
CHROME_PFADE = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    …
]
```

Eintrag nach vorne stellen oder ergänzen. Unter Linux genügt meist, dass
`chromium` im `PATH` liegt.

## Wenn gar nichts gefunden wird

```
Kein PDF-Werkzeug gefunden. HTML liegt hier: output/bericht.html
Im Browser öffnen und 'Als PDF sichern' wählen.
```

Das HTML ist vollständig und trägt eine `@page`-Regel für A4. Der Umweg über den
Druckdialog liefert dasselbe Ergebnis.

## Nur HTML erzeugen

Wenn das PDF gar nicht gebraucht wird — etwa für eine Weboberfläche — genügt es,
den letzten Schritt in `run.py` wegzulassen. `report.baue_html()` gibt eine
vollständige Seite zurück.

## Papierformat und Ränder

In `report.py`, ganz oben im CSS:

```css
@page { size: A4; margin: 18mm 16mm 16mm 16mm; }
```

`size: A4 landscape` für Querformat. Bei vielen Städten lohnt sich das für die
Rangfolgetabelle.

## Warum kein `reportlab` oder `fpdf`

Weil dann eine Abhängigkeit installiert werden müsste und das Layout in einer
Bibliotheks-API steckt statt in CSS. Der Umweg über HTML kostet nichts, ist im
Browser prüfbar — `output/bericht.html` lässt sich direkt öffnen — und dieselbe
Datei taugt für Web und Druck.
