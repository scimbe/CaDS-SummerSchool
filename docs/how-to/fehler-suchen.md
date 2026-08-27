# Fehler suchen

## Der Endpunkt antwortet nicht

```bash
Version-1/00_check.sh
```

Die Tabelle der Antwortcodes steht unter
[Endpunkt einrichten](endpunkt-einrichten.md#prufen).

## Das Modell antwortet, aber Unsinn

Sieh zuerst nach, **was** es bekommen hat. In Version-2:

```python
python3 -c "
import tools, harness
from air_api import fetch_cities
s = tools.stadt_auswerten(fetch_cities(['hamburg'])[0])
print(harness.auftrag_stadt(s))
"
```

Der Auftrag ist der ganze Kontext. Steht dort etwas Unklares, liegt es nicht am
Modell.

## „Beanstandete Zahlen" häufen sich

Im PDF, Tabelle „Wie dieser Bericht entstanden ist". Mehrere Versuche pro
Abschnitt bedeuten meist eines von zwei Dingen:

- **`temperature` zu hoch.** 0.3 ist ein guter Wert; ab 0.7 fängt das Modell an,
  Zahlen auszuschmücken.
- **Der Auftrag enthält zu viele ähnliche Zahlen.** Mittelwerte und Stadtwerte
  nebeneinander sind eine Einladung zur Verwechslung. Siehe
  [Was Prüfen nicht kann](../explanation/grenzen-der-pruefung.md).

## Eine Stadt liefert keine Daten

```
berlin       FEHLER: Station lieferte aktuell keine Messwerte.
```

Kein Fehler im Code. UBA-Stationen melden sich regelmäßig ohne Werte. Der Bericht
entsteht ohne diese Stadt und nennt die Lücke. Prüfen lässt sich das direkt:

```bash
curl -s https://infranode.dev/api/v1/cities/berlin/air-uba | jq .data.payload
```

## Version-3: das Modell ruft kein Werkzeug auf

Im Kasten „Was das Harness korrigiert hat":

```
Das Modell hat keinen Plan aufgerufen — noch einmal gefragt.
```

Kommt bei kleinen Modellen vor: Es antwortet mit Prosa statt mit dem
Funktionsaufruf. Das Harness fragt bis zu `max_versuche` mal nach und nimmt sonst
den Standardplan. Häuft es sich, hilft meist ein deutlicherer Systemprompt —
„antworte nie mit Fließtext" wirkt zuverlässiger als „bitte nutze die Funktion".

## Version-3: Seite lädt, aber bleibt leer

Konsole des Browsers öffnen. Häufigste Ursache: Der Server wurde aus einem
anderen Verzeichnis gestartet oder der Ordner wurde verschoben, während er lief —
dann findet er `static/` nicht mehr und `/` liefert 404. Neu starten:

```bash
cd First-API/Version-3
python3 server.py
```

## Port schon belegt

```
OSError: [Errno 48] Address already in use
```

Anderen Port nehmen — `python3 server.py 8080` — oder nachsehen, wer den Port
hält:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

## Umlaute erscheinen als Fragezeichen

Alle Dateien sind UTF-8, alle Antworten setzen `charset=utf-8`. Tritt das
Problem trotzdem auf, liegt es fast immer am Terminal:

```bash
export LANG=de_DE.UTF-8
```

## Das PDF hat leere Balken

Ältere Konverter drucken Hintergrundfarben nicht. Das CSS setzt dafür
`print-color-adjust: exact` — greift `wkhtmltopdf` oder `cupsfilter`, kann es
trotzdem passieren. Abhilfe: Chrome benutzen, siehe
[PDF-Erzeugung umstellen](pdf-werkzeug.md).
