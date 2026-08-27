# Eigene Städte und Schadstoffe

## Slugs finden

Die API deckt 84 deutsche Großstädte ab. Die Liste:

```bash
curl -s "https://infranode.dev/api/v1/cities?limit=200" | jq -r '.data[] | "\(.slug)\t\(.name_de)"'
```

Slugs sind kleingeschrieben und ohne Umlaute: `muenchen`, `koeln`,
`frankfurt-am-main`, `duesseldorf`.

## Version-2: andere Städte im Bericht

```bash
python3 run.py dresden leipzig magdeburg erfurt
```

Dauerhaft ändern — in `run.py`:

```python
STANDARD = ["hamburg", "berlin", "muenchen", "koeln", "stuttgart"]
```

Der Bericht wird mit jeder Stadt länger. Ab etwa acht Städten lohnt es sich, die
Einzelabschnitte wegzulassen und nur die Rangfolge zu setzen.

## Version-3: in der Oberfläche

Städtefeld benutzen — die Suche greift auf Name und Slug, `München` findet
`muenchen`. Höchstens acht Städte; die Grenze steht in `HARNESS.md` als
`max_staedte` und lässt sich dort erhöhen.

Als Link:

```
http://localhost:8000/?stufe=0&staedte=dresden,leipzig&darstellung=karten
```

## Andere Schadstoffe

Verfügbar sind `pm10`, `pm25`, `no2`, `o3`, `so2` — mehr liefert der Endpunkt
nicht. Nicht jede Station misst alle fünf; fehlende Werte werden ausgelassen und
im Bericht benannt.

Version-2, in `run.py` oder direkt in `tools.py`:

```python
ausgewertet = [tools.stadt_auswerten(r) for r in roh]   # alle fünf
```

Version-3: Kästchen in der Oberfläche, oder `?schadstoffe=pm10,no2`.

## Schwellenwerte ändern

Die Einstufung folgt dem UBA-Luftqualitätsindex. Die Tabelle steht in
`tools.py` (Version-2) beziehungsweise `datatools.py` (Version-3):

```python
SCHWELLEN = {
    "pm10": [20, 35, 50, 100],   # Obergrenzen: sehr gut, gut, mäßig, schlecht
    …
}
```

Die vollständigen Werte samt Herkunft:
[Einstufung und Grenzwerte](../reference/einstufung.md).

!!! warning "Zwei Zahlen, die nicht dasselbe sind"
    `SCHWELLEN` sind die Stufen des UBA-Index für **Einzelmesswerte**.
    `EU_GRENZWERTE` sind rechtliche Grenzwerte, meist als **Jahresmittel**
    definiert. Ein einzelner Messwert über 40 µg/m³ NO₂ verletzt keinen
    Jahresmittelwert. Deshalb steht in jedem Bericht der Hinweis, dass die
    EU-Werte hier nur der Einordnung dienen.
