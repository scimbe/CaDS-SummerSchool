# Auf eigene Daten übertragen

Das Muster hängt nicht an Luftqualität. Was zu tun ist, wenn eine andere Quelle
dran soll — eine Datenbank, ein internes System, eine andere offene API.

## Die vier Stellen

| Datei | Was zu ersetzen ist |
|---|---|
| `air_api.py` | Der Abruf. Eine Funktion, die ein Dict zurückgibt — Fehler als Feld, nicht als Ausnahme. |
| `tools.py` / `datatools.py` | Die Fachlogik: rechnen, einstufen, sortieren. Der größte Teil der Arbeit. |
| `HARNESS.md` | Systemprompt, Grenzen, erlaubte Werte, Farben. |
| `report.py` / `static/app.js` | Die Darstellung. |

`harness.py` und `planner.py` bleiben fast unverändert. Sie enthalten keine
Fachlogik — nur Prüfen, Nachfassen und Notfallplan.

## Die Reihenfolge, die sich bewährt

1. **Abruf zuerst, ohne Modell.** Ein Skript, das Daten holt und ausgibt. Wenn
   das nicht steht, hilft kein Sprachmodell.
2. **Fachlogik zweitens, ohne Modell.** Alles, was gerechnet, eingestuft und
   sortiert wird. Testbar, ohne dass jemals ein Token verbraucht wird.
3. **Darstellung drittens, ohne Modell.** Ein Bericht mit Platzhaltertexten. Ab
   hier ist das Produkt vollständig.
4. **Modell zuletzt.** Es ersetzt die Platzhalter durch Sprache.

!!! tip "Der Test für Schritt 4"
    Wenn Schritt 4 wegfällt und das Ergebnis immer noch brauchbar ist — hölzern,
    aber richtig —, ist die Aufgabenteilung richtig. Wenn nicht, macht das Modell
    zu viel.

## Fehler gehören ins Ergebnis, nicht ins Programm

```python
def hole(kennung: str) -> dict:
    try:
        …
    except (urllib.error.URLError, TimeoutError) as fehler:
        return {"kennung": kennung, "fehler": str(fehler)}
```

Bei zehn Quellen fällt garantiert eine aus. Eine Ausnahme reißt den ganzen
Durchlauf ab; ein Feld `fehler` lässt die anderen neun durchlaufen und macht die
Lücke sichtbar.

## Der Plan in Version-3

Das ist der Teil, der sich am meisten lohnt. Ein Plan taugt für jede Anwendung,
in der ein Prompt eine Auswahl steuert:

```json
{ "was": […], "womit": […], "wie": "…", "sortierung": "…" }
```

Drei Regeln:

1. **Jedes Feld hat eine abgeschlossene Menge erlaubter Werte.** Ein Freitextfeld
   im Plan ist ein Loch in der Prüfung.
2. **Kennungen werden aufgelöst, nicht übernommen.** Erst gegen eine Whitelist
   abgleichen, dann benutzen. Sonst baut das Modell Pfade.
3. **Reparieren statt ablehnen, und die Reparatur zeigen.** Ein Plan mit einem
   falschen Feld ist zu 80 % brauchbar. Aber der Mensch muss sehen, was
   geändert wurde.

## Was sich nicht überträgt

Die **Zahlenprüfung** aus Version-2 funktioniert, weil Messwerte kurze,
eindeutige Zahlen sind. Bei Fließtext, Namen oder langen Kennungen braucht es
etwas anderes — etwa einen Abgleich der genannten Entitäten mit den übergebenen.
Das Prinzip bleibt: **nach dem Modell prüfen, mit Code, gegen die Daten.**
