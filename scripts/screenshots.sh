#!/usr/bin/env bash
# Erzeugt alle Bilder für die Dokumentation neu.
#
#   ./scripts/screenshots.sh
#
# Braucht: einen laufenden Endpunkt (siehe First-API/.env), Internetzugang für
# die Luftdaten und einen installierten Chrome/Chromium. Die Bilder landen in
# docs/assets/ und werden mit eingecheckt, damit die Doku ohne Endpunkt baut.
set -euo pipefail

WURZEL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIEL="$WURZEL/docs/assets"
TMP="$(mktemp -d)"
PORT=8799
mkdir -p "$ZIEL"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[[ -x "$CHROME" ]] || CHROME="/Applications/Chromium.app/Contents/MacOS/Chromium"

term() { python3 "$WURZEL/scripts/terminal_png.py" "$1" "$ZIEL/$2" "$3"; }
web()  { "$CHROME" --headless --disable-gpu --no-sandbox --window-size="$3" \
           --virtual-time-budget=25000 --screenshot="$ZIEL/$2" "$1" 2>/dev/null; echo "  $2"; }

aufraeumen() { pkill -f "server.py $PORT" 2>/dev/null || true; rm -rf "$TMP"; }
trap aufraeumen EXIT

echo "== Version-1: Konsole =="
cd "$WURZEL/First-API"

{ Version-1/00_check.sh; } > "$TMP/check.txt" 2>&1
sed -i '' \
  -e 's/^HTTP 200$/{{g:HTTP 200}}/' \
  -e 's/^Verfügbare Modelle:$/{{d:Verfügbare Modelle:}}/' \
  -e 's/^\(Endpoint\|Modell\|Key\)/{{d:\1}}/' "$TMP/check.txt"
term "$TMP/check.txt" v1-check.png "Version-1/00_check.sh"

{ echo '$ Version-1/01_chat_curl.sh "Was ist ein Token? Kurz."'; echo
  Version-1/01_chat_curl.sh "Was ist ein Token? Kurz."; } > "$TMP/chat.txt" 2>&1
sed -i '' -e 's/^\$ \(.*\)$/{{f:$ \1}}/' -e 's/^> \(.*\)$/{{b:> \1}}/' "$TMP/chat.txt"
term "$TMP/chat.txt" v1-chat.png "Version-1/01_chat_curl.sh"

{ echo '$ python3 Version-1/06_tools.py'; echo
  python3 Version-1/06_tools.py; } > "$TMP/tools.txt" 2>&1
sed -i '' -e 's/^\$ \(.*\)$/{{f:$ \1}}/' -e 's/^> \(.*\)$/{{b:> \1}}/' \
          -e 's/^\(  \[Runde .*\)$/{{w:\1}}/' "$TMP/tools.txt"
term "$TMP/tools.txt" v1-tools.png "Version-1/06_tools.py — Tool-Calling"

echo "== Version-2: Konsole und PDF =="
cd "$WURZEL/First-API/Version-2"
{ echo '$ python3 run.py'; echo; python3 run.py; } > "$TMP/run.txt" 2>&1
sed -i '' -e 's/^\$ \(.*\)$/{{f:$ \1}}/' \
          -e 's/^\(\[[0-9]\/5\].*\)$/{{b:\1}}/' \
          -e 's/\(FEHLER: .*\)$/{{r:\1}}/' \
          -e 's/\(Notfalltext des Harness\)/{{w:\1}}/' \
          -e 's/^\(Fertig in .*\)$/{{g:\1}}/' "$TMP/run.txt"
term "$TMP/run.txt" v2-run.png "Version-2/run.py"

sips -s format png output/bericht.pdf --out "$ZIEL/v2-bericht-s1.png" >/dev/null 2>&1
echo "  v2-bericht-s1.png"

# Der Anhang steht auf der letzten PDF-Seite. sips kann keine Seite auswählen,
# also schneiden wir ihn stattdessen direkt aus dem erzeugten HTML heraus.
python3 - <<'PY'
import re, subprocess, tempfile
from pathlib import Path

quelle = Path("output/bericht.html").read_text(encoding="utf-8")
stil = re.search(r"<style>(.*?)</style>", quelle, re.S).group(1)
anhang = re.search(r'<div class="anhang">.*?</div>\s*(?=<footer>)', quelle, re.S).group(0)

seite = (f'<!doctype html><html lang="de"><head><meta charset="utf-8">'
         f'<style>{stil}\nbody{{padding:14mm 12mm;background:#fff}}'
         f'.anhang{{page-break-before:auto}}</style></head><body>{anhang}</body></html>')

with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as t:
    t.write(seite)
    pfad = Path(t.name)

subprocess.run([
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--headless", "--disable-gpu", "--no-sandbox", "--window-size=760,1000",
    "--screenshot=../../docs/assets/v2-bericht-anhang.png", pfad.as_uri(),
], capture_output=True, timeout=90)
pfad.unlink(missing_ok=True)
print("  v2-bericht-anhang.png")
PY

echo "== Version-2: Wirkung einer Harness-Änderung =="
cp HARNESS.md "$TMP/HARNESS.md.orig"
python3 - <<'PY'
from pathlib import Path
p = Path("HARNESS.md"); s = p.read_text(encoding="utf-8")
# Einfarbige blaue Skala statt Ampel, und die Balken auf den EU-Grenzwert beziehen.
for alt, neu in [("#2e7d32", "#cfe0f5"), ("#7cb342", "#8fb4dd"), ("#f9a825", "#4a7cb8"),
                 ("#ef6c00", "#25548c"), ("#c62828", "#12305a"),
                 ("`akzent: #204c86`", "`akzent: #12305a`"),
                 ("`balken_bezug: index`", "`balken_bezug: grenzwert`")]:
    s = s.replace(alt, neu)
p.write_text(s, encoding="utf-8")
PY
python3 run.py hamburg muenchen koeln stuttgart >/dev/null 2>&1
sips -s format png output/bericht.pdf --out "$ZIEL/v2-bericht-variante.png" >/dev/null 2>&1
echo "  v2-bericht-variante.png"
cp "$TMP/HARNESS.md.orig" HARNESS.md
python3 run.py hamburg muenchen koeln stuttgart >/dev/null 2>&1
sips -s format png output/bericht.pdf --out "$ZIEL/v2-bericht-standard.png" >/dev/null 2>&1
echo "  v2-bericht-standard.png"

echo "== Version-3: Oberfläche =="
cd "$WURZEL/First-API/Version-3"
pkill -f "server.py $PORT" 2>/dev/null || true
python3 server.py $PORT >/dev/null 2>&1 &
sleep 2

BASIS="http://localhost:$PORT"
AUSWAHL="staedte=hamburg,muenchen,koeln,stuttgart"
web "$BASIS/"                                             v3-start.png    1400,900
web "$BASIS/?stufe=0&darstellung=balken&$AUSWAHL"          v3-balken.png   1400,1150
web "$BASIS/?stufe=0&darstellung=tabelle&$AUSWAHL&schadstoffe=pm10,no2,o3" v3-tabelle.png 1400,900
web "$BASIS/?stufe=0&darstellung=karten&$AUSWAHL&schadstoffe=pm10,no2,o3"  v3-karten.png  1400,950

echo "== Version-3: Wirkung einer Harness-Änderung =="
cp HARNESS.md "$TMP/HARNESS-v3.orig"
python3 - <<'PY'
from pathlib import Path
p = Path("HARNESS.md"); s = p.read_text(encoding="utf-8")
for alt, neu in [("#2e7d32", "#cfe0f5"), ("#7cb342", "#8fb4dd"), ("#f9a825", "#4a7cb8"),
                 ("#ef6c00", "#25548c"), ("#c62828", "#12305a"),
                 ("`balken_bezug: index`", "`balken_bezug: grenzwert`")]:
    s = s.replace(alt, neu)
p.write_text(s, encoding="utf-8")
PY
web "$BASIS/?stufe=0&darstellung=balken&$AUSWAHL" v3-balken-variante.png 1400,1150
cp "$TMP/HARNESS-v3.orig" HARNESS.md

echo
echo "Fertig. Bilder in docs/assets/:"
ls -1 "$ZIEL"
