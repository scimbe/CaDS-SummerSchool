#!/usr/bin/env python3
"""Version-2: von der offenen API zum fertigen PDF.

    API holen  ->  rechnen (tools.py)  ->  formulieren lassen (harness.py)
                ->  prüfen  ->  setzen (report.py)  ->  drucken (pdf.py)

Aufruf:
    python3 run.py                          # Standardstädte
    python3 run.py hamburg koeln dresden    # eigene Auswahl (Slugs wie in der API)
"""
import sys
import time
from pathlib import Path

import harness
import pdf
import report
import tools
from air_api import fetch_cities

STANDARD = ["hamburg", "berlin", "muenchen", "koeln", "stuttgart"]
AUSGABE = Path(__file__).parent / "output"


def main() -> int:
    städte_slugs = sys.argv[1:] or STANDARD
    AUSGABE.mkdir(exist_ok=True)
    start = time.time()

    # --- 1. Daten holen ------------------------------------------------------
    print(f"[1/5] Luftdaten holen für: {', '.join(städte_slugs)}")
    roh = fetch_cities(städte_slugs)
    for r in roh:
        status = "FEHLER: " + r["error"] if "error" in r else f"{len(r['messwerte'])} Messwerte"
        print(f"      {r['slug']:<12} {status}")

    # --- 2. Rechnen (ohne Modell) -------------------------------------------
    print("[2/5] Einstufen und vergleichen (reines Python, kein Modell)")
    ausgewertet = [tools.stadt_auswerten(r) for r in roh]
    vgl = tools.vergleich(ausgewertet)
    if vgl["anzahl"] == 0:
        print("      Keine einzige Stadt lieferte Daten - Abbruch.")
        return 1
    print(f"      {vgl['anzahl']} Städte ausgewertet, "
          f"beste: {vgl['bestes']}, schlechteste: {vgl['schlechtestes']}")

    # --- 3. Texte vom Modell, mit Prüfung ----------------------------------
    print("[3/5] Texte formulieren lassen und prüfen")
    texte, protokolle = {}, []

    text, prot = harness.schreibe_abschnitt(
        harness.auftrag_kurzfassung(vgl), vgl, harness.notfall_kurzfassung(vgl),
        mit_messwerten=False
    )
    texte["kurzfassung"] = text
    protokolle.append({"abschnitt": "Kurzfassung", **prot})
    print(f"      Kurzfassung        {_status(prot)}")

    for stadt in [s for s in ausgewertet if s["ok"]]:
        text, prot = harness.schreibe_abschnitt(
            harness.auftrag_stadt(stadt), stadt, harness.notfall_stadt(stadt),
            max_tokens=harness.TOKENS_STADT,
        )
        texte[stadt["slug"]] = text
        protokolle.append({"abschnitt": stadt["name"], **prot})
        print(f"      {stadt['name']:<18} {_status(prot)}")

    # --- 4. Setzen -----------------------------------------------------------
    print("[4/5] HTML setzen")
    attribution = next(
        (r.get("attribution", {}) for r in roh if r.get("attribution")), {}
    )
    html_datei = AUSGABE / "bericht.html"
    html_datei.write_text(
        report.baue_html(vgl, ausgewertet, texte, protokolle, attribution, roh), encoding="utf-8"
    )

    # --- 5. Drucken ----------------------------------------------------------
    print("[5/5] PDF erzeugen")
    pdf_datei = AUSGABE / "bericht.pdf"
    erfolg, werkzeug = pdf.html_zu_pdf(html_datei, pdf_datei)

    print()
    if erfolg:
        größe = pdf_datei.stat().st_size // 1024
        print(f"Fertig in {time.time() - start:.1f}s -> {_kurz(pdf_datei)}  "
              f"({größe} KB, via {werkzeug})")
    else:
        print(f"Kein PDF-Werkzeug gefunden. HTML liegt hier: {_kurz(html_datei)}")
        print("Im Browser öffnen und 'Als PDF sichern' wählen.")
    return 0


def _kurz(pfad: Path) -> str:
    """Pfad relativ zum Arbeitsverzeichnis - der volle Pfad hilft niemandem."""
    try:
        return str(pfad.resolve().relative_to(Path.cwd()))
    except ValueError:
        return str(pfad)


def _status(prot: dict) -> str:
    if prot["quelle"] == "notfall":
        return "Notfalltext des Harness"
    if prot["beanstandet"]:
        return f"OK nach {prot['versuche']} Versuchen (erfundene Zahlen verworfen)"
    return "OK"


if __name__ == "__main__":
    raise SystemExit(main())
