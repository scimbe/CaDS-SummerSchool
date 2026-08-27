"""Layout: aus den ausgewerteten Daten wird eine druckfertige HTML-Seite.

Bewusst reines HTML mit CSS und ohne Bibliothek: So sieht man, dass ein PDF am
Ende nur eine gut gesetzte Seite ist. Die Balken sind <div>s mit Prozentbreite,
keine Grafikbibliothek nötig.
"""
import html
import json
from datetime import datetime, timezone

import harness
from air_api import BASE

# Farben und Akzent stehen in HARNESS.md, nicht hier. Die Werte unten sind nur
# der Rückfall, falls der Abschnitt "## Aufbereitung" dort fehlt.
STUFEN_FARBEN = harness.FARBEN or {
    "sehr gut": "#2e7d32",
    "gut": "#7cb342",
    "mäßig": "#f9a825",
    "schlecht": "#ef6c00",
    "sehr schlecht": "#c62828",
    "unbekannt": "#9e9e9e",
}
AKZENT = harness.AKZENT
# "index" oder "grenzwert" - siehe HARNESS.md, Abschnitt Aufbereitung.
BALKEN = "balken_grenzwert" if harness.BALKEN_BEZUG == "grenzwert" else "balken_index"

CSS = """
@page { size: A4; margin: 18mm 16mm 16mm 16mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       color: #1a1a1a; font-size: 10.5pt; line-height: 1.5; margin: 0; }
h1 { font-size: 21pt; margin: 0 0 2mm; color: AKZENTFARBE; letter-spacing: -0.01em; }
h2 { font-size: 13pt; margin: 9mm 0 3mm; color: AKZENTFARBE;
     border-bottom: 1.5px solid AKZENTFARBE; padding-bottom: 1.5mm; }
h3 { font-size: 11pt; margin: 5mm 0 1.5mm; }
.sub { color: #5a5a5a; font-size: 9pt; margin: 0 0 6mm; }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
th { background: AKZENTFARBE; color: #fff; text-align: left; padding: 2mm 2.5mm; font-weight: 600; }
td { padding: 2mm 2.5mm; border-bottom: 1px solid #e0e0e0; }
tr:nth-child(even) td { background: #f7f9fc; }
.badge { display: inline-block; padding: 0.5mm 2mm; border-radius: 3px;
         color: #fff; font-size: 8.5pt; font-weight: 600; white-space: nowrap; }
.stadt { break-inside: avoid; page-break-inside: avoid; margin-bottom: 6mm; }
.bar-row { display: flex; align-items: center; gap: 2mm; margin: 1mm 0; font-size: 9pt; }
.bar-label { width: 42mm; flex: none; }
.bar-track { flex: 1; height: 4mm; background: #eceff1; border-radius: 2px; overflow: hidden;
             display: block; }
/* display:block ist nötig - ein <span> ist sonst inline und hat keine Höhe. */
.bar-fill { display: block; height: 4mm; border-radius: 2px; min-width: 1px; }
.bar-value { width: 26mm; flex: none; text-align: right; font-variant-numeric: tabular-nums; }
.warn { color: #c62828; font-weight: 600; }
.note { background: #f7f9fc; border-left: 3px solid AKZENTFARBE;
        padding: 3mm 4mm; margin: 4mm 0; font-size: 9pt; }
footer { margin-top: 10mm; padding-top: 3mm; border-top: 1px solid #d0d0d0;
         font-size: 8pt; color: #666; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 8.5pt; background: #eceff1;
       padding: 0.3mm 1mm; border-radius: 2px; }
.anhang { page-break-before: always; break-before: page; }
.herkunft { break-inside: avoid; page-break-inside: avoid; }
.roh { font-family: "SF Mono", Menlo, monospace; font-size: 7.5pt; line-height: 1.35;
       background: #f7f9fc; border: 1px solid #dfe6ef; border-radius: 3px;
       padding: 2.5mm 3mm; white-space: pre-wrap; word-break: break-word;
       break-inside: avoid; page-break-inside: avoid; margin: 0 0 4mm; }
.roh-titel { font-size: 9.5pt; font-weight: 600; margin: 4mm 0 1.5mm; }
.roh-url { font-size: 8pt; color: #5a5a5a; margin: 0 0 1.5mm;
           font-family: "SF Mono", Menlo, monospace; word-break: break-all; }
"""


def _e(text) -> str:
    return html.escape(str(text))


def _badge(stufe: str) -> str:
    return f'<span class="badge" style="background:{STUFEN_FARBEN.get(stufe, "#9e9e9e")}">{_e(stufe)}</span>'


def _stadt_block(stadt: dict, text: str) -> str:
    balken = "".join(
        f'<div class="bar-row">'
        f'<span class="bar-label">{_e(w["name"])}</span>'
        f'<span class="bar-track"><span class="bar-fill" style="width:{w[BALKEN]}%;'
        f'background:{STUFEN_FARBEN.get(w["stufe"], "#9e9e9e")}"></span></span>'
        f'<span class="bar-value">{w["wert"]:g} {_e(w["einheit"])}</span>'
        f"</div>"
        for w in stadt["werte"]
    )
    hinweis = ""
    if stadt["grenzwert_überschreitungen"]:
        hinweis = f'<p class="warn">Über EU-Grenzwert: {_e(", ".join(stadt["grenzwert_überschreitungen"]))}</p>'
    return (
        f'<div class="stadt"><h3>{_e(stadt["name"])} {_badge(stadt["gesamtstufe"])}</h3>'
        f"<p>{_e(text)}</p>{balken}{hinweis}</div>"
    )


def _anhang(roh: list[dict]) -> str:
    """Die unveränderten API-Antworten - damit jede Zahl im Bericht prüfbar bleibt.

    Ohne diesen Anhang müsste man dem Bericht glauben. Mit ihm kann man
    nachrechnen: Messwert im Anhang, Einstufung in der Tabelle, Satz im Text.
    """
    blöcke = []
    for eintrag in roh:
        url = f"{BASE}/{eintrag['slug']}/air-uba"
        inhalt = json.dumps(eintrag, indent=2, ensure_ascii=False, sort_keys=True)
        blöcke.append(
            f'<div class="roh-titel">{_e(eintrag["slug"])}</div>'
            f'<div class="roh-url">GET {_e(url)}</div>'
            f'<div class="roh">{_e(inhalt)}</div>'
        )
    return "".join(blöcke) or '<p class="sub">Keine Rohdaten übergeben.</p>'


def baue_html(vgl: dict, städte: list[dict], texte: dict, protokolle: list[dict],
              attribution: dict, roh: list[dict] | None = None) -> str:
    jetzt = datetime.now(timezone.utc).astimezone()
    gültig = [s for s in städte if s["ok"]]
    stand = gültig[0]["observed_at"] if gültig else "-"

    rang_zeilen = "".join(
        f"<tr><td>{e['platz']}</td><td>{_e(e['name'])}</td><td>{_badge(e['stufe'])}</td>"
        f"<td>{_e(e['treiber'])}</td><td>{e['belastungsindex']:.2f}</td></tr>"
        for e in vgl["rangliste"]
    )

    stadt_blöcke = "".join(
        _stadt_block(s, texte.get(s["slug"], "")) for s in gültig
    )

    fehler = ""
    if vgl.get("fehlgeschlagen"):
        fehler = (
            f'<p class="warn">Keine Daten erhalten für: '
            f'{_e(", ".join(vgl["fehlgeschlagen"]))}</p>'
        )

    nachgebessert = sum(1 for p in protokolle if p["beanstandet"])
    notfall = sum(1 for p in protokolle if p["quelle"] == "notfall")
    protokoll_zeilen = "".join(
        f"<tr><td>{_e(p['abschnitt'])}</td><td>{p['versuche']}</td>"
        f"<td>{_e('; '.join(', '.join(v) for v in p['beanstandet']) or '-')}</td>"
        f"<td>{_e('Modell' if p['quelle'] == 'modell' else 'Harness (Notfalltext)')}</td></tr>"
        for p in protokolle
    )

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Luftqualitätsbericht</title><style>{CSS.replace("AKZENTFARBE", AKZENT)}</style></head><body>

<h1>Luftqualität in deutschen Großstädten</h1>
<p class="sub">Erzeugt am {jetzt:%d.%m.%Y um %H:%M} &middot; Messstand {_e(stand)} &middot;
Datenquelle Umweltbundesamt (UBA) &middot; Texte formuliert von einem lokalen Sprachmodell,
alle Zahlen aus der API berechnet</p>

<h2>Kurzfassung</h2>
<p>{_e(texte.get("kurzfassung", ""))}</p>
{fehler}

<h2>Rangfolge</h2>
<table><thead><tr><th>Platz</th><th>Stadt</th><th>Einstufung</th><th>Ausschlaggebend</th><th>Index</th></tr></thead>
<tbody>{rang_zeilen}</tbody></table>
<p class="sub" style="margin-top:2mm">Platz 1 ist die am stärksten belastete Stadt.
Die Einstufung entspricht dem schlechtesten Einzelwert - so rechnet auch der
UBA-Luftqualitätsindex. Der <b>Index</b> setzt diesen Wert ins Verhältnis zur
Obergrenze der Stufe „gut": 1,00 bedeutet genau an der Grenze zu „mäßig". Er macht
Städte vergleichbar, die bei gleicher Stufe unterschiedlich nah an ihr liegen, und
er ist der einzige Grund, warum die Reihenfolge hier nicht alphabetisch ist.</p>

<h2>Die Städte im Einzelnen</h2>
{stadt_blöcke}

<div class="herkunft">
<h2>Wie dieser Bericht entstanden ist</h2>
<div class="note">
Die Messwerte kommen über einen GET-Request von
<code>infranode.dev/api/v1/cities/&lt;stadt&gt;/air-uba</code>. Einstufung, Rangfolge und
Mittelwerte rechnet <code>tools.py</code> in normalem Python. Das Sprachmodell bekommt
diese fertigen Zahlen und formuliert daraus die Absätze - es rechnet nichts.
Anschliessend prüft das Harness jeden Absatz darauf, ob eine Zahl auftaucht, die es in
den Daten nicht gibt, und lässt ihn im Zweifel neu schreiben.
</div>
<table><thead><tr><th>Abschnitt</th><th>Versuche</th><th>Beanstandete Zahlen</th><th>Ergebnis</th></tr></thead>
<tbody>{protokoll_zeilen}</tbody></table>
<p class="sub" style="margin-top:2mm">{len(protokolle)} Abschnitte,
{nachgebessert} davon nachgebessert, {notfall} vom Harness selbst geschrieben.</p>
</div>

<div class="anhang">
<h2>Anhang: Originaldaten der API</h2>
<p class="sub">Die Antworten des Endpunkts, unverändert und vollständig. Jede Zahl im
Bericht lässt sich hier nachschlagen. Abgerufen am {jetzt:%d.%m.%Y um %H:%M}.</p>
{_anhang(roh or [])}
</div>

<footer>
Datenquelle: {_e(attribution.get("text", "Umweltbundesamt (UBA)"))},
Lizenz <a href="{_e(attribution.get("license_url", ""))}">DL-DE BY 2.0</a>.
Bereitgestellt über infranode.dev. Einzelmesswerte einer Station sind nicht mit
Jahresmittelwerten vergleichbar; die EU-Grenzwerte dienen hier nur der Einordnung.<br>
CaDS Summer School &middot; First-API &middot; Version-2
</footer>
</body></html>"""
