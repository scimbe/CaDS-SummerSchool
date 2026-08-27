#!/usr/bin/env python3
"""Macht aus einer Textdatei ein Terminal-Bild.

    python3 terminal_png.py eingabe.txt ausgabe.png "Titel der Fensterleiste"

Der Umweg über HTML und den Browser spart eine Bildbibliothek und liefert
saubere Schrift. Farben werden über einfache Marker gesetzt, die die
Aufrufer-Skripte in den Text schreiben.
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

VORLAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; }}
body {{ margin: 0; padding: 20px; background: #eef2f7; }}
.fenster {{ border-radius: 10px; overflow: hidden; box-shadow: 0 8px 30px rgba(18,48,90,.18);
           max-width: 940px; }}
.leiste {{ background: #e6e9ee; padding: 9px 13px; display: flex; align-items: center; gap: 7px;
          border-bottom: 1px solid #d3d8e0; }}
.punkt {{ width: 11px; height: 11px; border-radius: 50%; }}
.titel {{ flex: 1; text-align: center; font: 600 12px -apple-system, sans-serif; color: #5d6874;
         margin-right: 40px; }}
pre {{ margin: 0; padding: 16px 18px; background: #11151c; color: #d6deea;
      font: 13px/1.62 ui-monospace, "SF Mono", Menlo, monospace; white-space: pre-wrap;
      word-break: break-word; }}
.b {{ color: #7fb3ff; }} .g {{ color: #9ccc5a; }} .r {{ color: #ff8a80; }}
.d {{ color: #7b8794; }} .w {{ color: #ffd479; }} .f {{ font-weight: 700; color: #fff; }}
</style></head><body>
<div class="fenster">
  <div class="leiste">
    <span class="punkt" style="background:#ff5f57"></span>
    <span class="punkt" style="background:#febc2e"></span>
    <span class="punkt" style="background:#28c840"></span>
    <span class="titel">{titel}</span>
  </div>
  <pre>{inhalt}</pre>
</div></body></html>"""

MARKER = re.compile(r"\{\{(b|g|r|d|w|f):(.*?)\}\}", re.S)


def main() -> int:
    quelle, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    titel = sys.argv[3] if len(sys.argv) > 3 else "Terminal"

    inhalt = html.escape(quelle.read_text(encoding="utf-8").rstrip())
    # Marker wie {{g:Text}} in farbige Spans übersetzen (nach dem Escapen, damit
    # der Text selbst keine Tags einschmuggeln kann).
    inhalt = MARKER.sub(lambda m: f'<span class="{m.group(1)}">{m.group(2)}</span>', inhalt)

    browser = next((c for c in CHROME if Path(c).exists()), None)
    if not browser:
        print("Kein Browser für die Aufnahme gefunden.", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(VORLAGE.format(titel=html.escape(titel), inhalt=inhalt))
        pfad = Path(tmp.name)

    # Fensterhöhe aus der Zeilenzahl: 20px Rand + 33px Leiste + 32px Innenabstand
    # + 21px je Zeile + 20px Rand. Trifft nah genug, um unten keinen leeren
    # Streifen zu lassen.
    # Lange Zeilen brechen im <pre> um und brauchen mehr als eine Zeilenhöhe.
    # Bei 13px Monospace in 940px Breite passen rund 100 Zeichen nebeneinander.
    roh = MARKER.sub(lambda m: m.group(2), quelle.read_text(encoding="utf-8").rstrip())
    zeilen = sum(max(1, -(-len(z) // 100)) for z in roh.split("\n"))
    subprocess.run([
        browser, "--headless", "--disable-gpu", "--no-sandbox",
        f"--window-size=1000,{min(2400, 106 + zeilen * 21)}",
        "--default-background-color=00000000",
        f"--screenshot={ziel}", pfad.as_uri(),
    ], capture_output=True, timeout=90)
    pfad.unlink(missing_ok=True)

    if not ziel.exists():
        print(f"Aufnahme fehlgeschlagen: {ziel}", file=sys.stderr)
        return 1
    print(f"  {ziel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
