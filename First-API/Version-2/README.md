# Version-2 — Das Harness

Aus einer offenen API wird ein fertiger PDF-Bericht.

```bash
python3 run.py                          # fünf Standardstädte
python3 run.py hamburg koeln dresden    # eigene Auswahl
```

Ergebnis: `output/bericht.pdf` (und das HTML daneben).

## Der Ablauf

```
air_api.py    Daten holen        ┐
tools.py      rechnen, einstufen ├─ ohne Modell
              sortieren          ┘
harness.py    formulieren lassen ─── Modell, eng geführt
              prüfen, nachfassen ┐
report.py     setzen             ├─ ohne Modell
pdf.py        drucken            ┘
```

## Die Regeln stehen in [`HARNESS.md`](HARNESS.md)

Nicht als Dokumentation, sondern als **Konfiguration**: `harness.py` liest die
Datei beim Start und holt sich daraus den Systemprompt und die Grenzwerte. Ändere
den Textblock unter `## Systemprompt` — das Programmverhalten ändert sich, ohne
dass eine Zeile Python angefasst wird. Dieselbe Idee wie `CLAUDE.md` oder
`AGENTS.md` bei Coding-Agenten.

## Was hängen bleiben soll

**Das Modell rechnet nicht.** Jede Zahl, jede Einstufung und jede Rangfolge
entsteht in `tools.py` in normalem Python. Das Modell bekommt fertige Ergebnisse
und gießt sie in Sätze.

**Nach dem Modell wird geprüft.** `pruefe_text()` vergleicht jede Zahl im
generierten Text mit den übergebenen Daten. Steht dort eine Zahl, die es nicht
gibt, wird der Abschnitt verworfen und mit konkreter Rückmeldung neu angefordert.
Wie oft das nötig war, steht im PDF — siehe die Tabelle „Wie dieser Bericht
entstanden ist".

**Es gibt immer ein Ergebnis.** Bleibt ein Abschnitt beanstandet oder ist der
Endpunkt nicht erreichbar, schreibt das Harness den Satz selbst aus den Daten.
Ein Bericht ohne Modell ist besser als ein Bericht mit falschen Zahlen.

**Prüfen hat Grenzen.** Die Zahlenprüfung erkennt erfundene Zahlen, aber keine
falsch zugeordneten — ein Mittelwert und ein Stadtwert sehen für das Modell gleich
aus. Die Antwort darauf ist kein besserer Prüfer, sondern ein engerer Auftrag:
Die Kurzfassung wird ohne jede Messzahl geschrieben. Ausführlich in `HARNESS.md`
unter „Zahlen nur dort, wo sie eindeutig sind".

**Jede Zahl ist nachprüfbar.** Der Anhang des PDFs enthält die unveränderten
API-Antworten samt Abruf-URL.
