# 2 — Der erste Bericht

**Ziel:** Du hast aus einer offenen API einen fertigen PDF-Bericht erzeugt — und
du kannst zeigen, an welcher Stelle das Sprachmodell beteiligt war und an welcher
nicht.

**Vorher:** [Die erste Anfrage](erste-anfrage.md).

---

## Erst die Daten

Die Luftqualitäts-API braucht keinen Schlüssel:

```bash
curl -s https://infranode.dev/api/v1/cities/hamburg/air-uba | jq .data.payload
```

```json
{ "kind": "air_quality", "station_id": "784",
  "pm10": 23.0, "no2": 16.0, "pm25": 9.0, "o3": 79.0, "so2": 3.0 }
```

Fünf Zahlen. Alles, was gleich im Bericht steht, kommt aus diesem Objekt.

---

## Der ganze Durchlauf

```bash
cd First-API/Version-2
python3 run.py
```

```
[1/5] Luftdaten holen für: hamburg, berlin, muenchen, koeln, stuttgart
      hamburg      5 Messwerte
      berlin       FEHLER: Station lieferte aktuell keine Messwerte.
      muenchen     4 Messwerte
      …
[2/5] Einstufen und vergleichen (reines Python, kein Modell)
      4 Städte ausgewertet, beste: München, schlechteste: Hamburg
[3/5] Texte formulieren lassen und prüfen
      Kurzfassung        OK
      Hamburg            OK
      …
[4/5] HTML setzen
[5/5] PDF erzeugen

Fertig in 20.5s -> output/bericht.pdf  (167 KB, via Google Chrome)
```

Öffne das PDF.

!!! note "Berlin fehlt vielleicht, vielleicht auch nicht"
    Es kommt regelmäßig vor, dass eine UBA-Station sich meldet, aber gerade
    keinen einzigen Wert liefert. Der Bericht entsteht trotzdem und nennt die
    Lücke ausdrücklich. Das ist kein Schönheitsfehler, sondern der Normalfall bei
    echten Daten — und der Grund, warum jede Stadt einzeln scheitern darf.

---

## Wer hat was gemacht?

Blättere im PDF zum Abschnitt **„Wie dieser Bericht entstanden ist"**. Dort steht
für jeden Absatz, wie viele Versuche das Modell gebraucht hat, welche Zahlen
beanstandet wurden und ob der Text am Ende vom Modell oder vom Harness stammt.

Die Aufgabenteilung dahinter:

```
air_api.py    Daten holen        ┐
tools.py      rechnen, einstufen ├─ ohne Modell
              sortieren          ┘
harness.py    formulieren lassen ─── Modell, eng geführt
              prüfen, nachfassen ┐
report.py     setzen             ├─ ohne Modell
pdf.py        drucken            ┘
```

Jede Zahl im Bericht — Messwert, Einstufung, Rangfolge, Index — entsteht in
`tools.py` in normalem Python. Das Modell bekommt fertige Ergebnisse und macht
Sätze daraus.

---

## Die Prüfung bei der Arbeit zusehen

Öffne `harness.py` und suche `pruefe_text`. Nach jeder Antwort des Modells wird
jede Zahl im Text mit den übergebenen Daten verglichen. Probier es direkt aus:

```bash
python3 -c "
import harness
erlaubt = harness.erlaubte_zahlen({'pm10': 23.0})
print(harness.pruefe_text('Der Wert liegt bei 23 µg/m³.', erlaubt))
print(harness.pruefe_text('Der Wert liegt bei 42 µg/m³.', erlaubt))
"
```

```
[]
['42']
```

Findet die Prüfung etwas, bekommt das Modell die beanstandeten Zahlen genannt und
schreibt den Abschnitt neu. Bis zu drei Mal — danach schreibt das Harness den
Satz selbst.

---

## Den Notfallplan auslösen

Der interessanteste Test ist der, bei dem nichts funktioniert. Ziehe dem Harness
den Endpunkt unter den Füßen weg:

```bash
LLM_BASE_URL=https://localhost:1/v1 python3 run.py hamburg muenchen
```

```
[3/5] Texte formulieren lassen und prüfen
      Kurzfassung        Notfalltext des Harness
      Hamburg            Notfalltext des Harness
      …
Fertig in 1.2s -> output/bericht.pdf
```

Der Bericht entsteht. Die Zahlen stimmen. Nur die Sprache ist hölzern.

!!! success "Das ist der Punkt"
    Ein Bericht ohne Modell ist besser als ein Bericht mit falschen Zahlen. Wenn
    der Ausfall des Modells deine Anwendung umbringt, hast du kein Harness
    gebaut, sondern eine Abhängigkeit.

---

## Die Regeln ändern, ohne Code zu ändern

Öffne [`HARNESS.md`](../reference/version-2.md#harnessmd) im selben Ordner. Der
Block unter `## Systemprompt` wird beim Start eingelesen und wörtlich als
`system`-Nachricht geschickt. Ändere ihn — etwa auf „Schreibe betont knapp, ein
Satz je Abschnitt." — und starte `run.py` neu.

Der Bericht sieht anders aus. Python wurde nicht angefasst.

Dasselbe gilt für die Werte unter `## Grenzen`: `max_versuche`, `temperature`,
`max_tokens_stadt`. Warum die Regeln in einer Markdown-Datei stehen und nicht im
Code, steht unter [Regeln in einer Datei](../explanation/regeln-als-datei.md).

---

## Nachprüfen

Ganz hinten im PDF steht der **Anhang mit den Originaldaten**: die unveränderten
API-Antworten samt Abruf-URL. Such dir eine Zahl aus dem Fließtext und verfolge
sie zurück — Text, Balken, Tabelle, Anhang, API.

Genau diese Kette ist der Unterschied zwischen einem Bericht, dem man glauben
muss, und einem, den man prüfen kann.

---

## Eigene Städte

```bash
python3 run.py dresden leipzig magdeburg
```

Die Slugs stehen in der [Städteliste](../reference/luftqualitaet-api.md#staedteliste).

---

## Weiter

[Die erste Oberfläche](erste-oberflaeche.md) — jetzt darf das Modell die API steuern.
