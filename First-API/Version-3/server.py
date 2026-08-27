#!/usr/bin/env python3
"""Kleiner Webserver für die Oberfläche - nur Python-Standardbibliothek.

    python3 server.py            -> http://localhost:8000
    python3 server.py 8080       -> anderer Port

Endpunkte:
    GET  /                 Oberfläche
    GET  /api/staedte      Städteliste (die Whitelist)
    GET  /api/harness      HARNESS.md als Text, für den Reiter „Regeln"
    POST /api/plan         {prompt} -> geprüfter Plan + Korrekturprotokoll
    POST /api/run          {plan}   -> Daten, Kennzahlen, optionaler Kommentar

Die Trennung von /api/plan und /api/run ist Absicht und der eigentliche Hebel:
Planen und Ausführen sind zwei Schritte. Dazwischen darf ein Mensch schauen.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import air_api
import datatools
import planner

STATISCH = Path(__file__).parent / "static"
TYPEN = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}


def ausfuehren(plan: dict) -> dict:
    """Führt einen geprüften Plan aus. Ab hier ist kein Modell mehr beteiligt."""
    staedte = air_api.staedteliste()
    namen = {s["slug"]: s["name"] for s in staedte}

    roh = [air_api.luftdaten(slug) for slug in plan["staedte"]]
    zeilen = [
        datatools.aufbereiten(r, namen.get(r["slug"], r["slug"]), plan["schadstoffe"])
        for r in roh
    ]
    zeilen = datatools.sortieren(zeilen, plan["sortierung"])
    kennzahlen = datatools.kennzahlen(zeilen)

    ergebnis = {
        "plan": plan,
        "zeilen": zeilen,
        "kennzahlen": kennzahlen,
        "rohdaten": [r.get("roh", r) for r in roh],
        "attribution": next(
            (r.get("attribution") for r in roh if r.get("attribution")),
            {"text": "Umweltbundesamt (UBA)", "license_url": "https://www.govdata.de/dl-de/by-2-0"},
        ),
    }

    if plan.get("kommentar"):
        ergebnis["kommentar"] = planner.kommentieren(zeilen, kennzahlen)
    return ergebnis


class Handler(BaseHTTPRequestHandler):
    server_version = "FirstAPI/3"

    def log_message(self, format, *args):  # noqa: A002 - Signatur ist vorgegeben
        print(f"  {self.command} {self.path}")

    # --- Hilfsmittel ---------------------------------------------------------

    def _json(self, nutzlast, status: int = 200) -> None:
        rumpf = json.dumps(nutzlast, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(rumpf)))
        self.end_headers()
        self.wfile.write(rumpf)

    def _datei(self, pfad: Path) -> None:
        if not pfad.is_file():
            self._json({"fehler": "nicht gefunden"}, 404)
            return
        rumpf = pfad.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TYPEN.get(pfad.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(rumpf)))
        self.end_headers()
        self.wfile.write(rumpf)

    def _eingang(self) -> dict:
        laenge = int(self.headers.get("Content-Length") or 0)
        if not laenge:
            return {}
        try:
            return json.loads(self.rfile.read(laenge))
        except json.JSONDecodeError:
            return {}

    # --- Routen --------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - von BaseHTTPRequestHandler vorgegeben
        pfad = self.path.split("?", 1)[0]
        if pfad == "/":
            self._datei(STATISCH / "index.html")
        elif pfad == "/api/staedte":
            self._json({"staedte": air_api.staedteliste()})
        elif pfad == "/api/harness":
            self._json({"text": (Path(__file__).with_name("HARNESS.md")).read_text(encoding="utf-8")})
        elif pfad.startswith("/static/"):
            # Nur Dateien direkt im static-Ordner - kein Ausbrechen über "..".
            name = Path(pfad).name
            self._datei(STATISCH / name)
        else:
            self._json({"fehler": "unbekannter Pfad"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        pfad = self.path.split("?", 1)[0]
        eingang = self._eingang()

        if pfad == "/api/plan":
            prompt = (eingang.get("prompt") or "").strip()
            if not prompt:
                self._json({"fehler": "Kein Prompt übergeben."}, 400)
                return
            self._json(planner.plane(prompt, air_api.staedteliste()))

        elif pfad == "/api/run":
            plan_roh = eingang.get("plan") or {}
            # Auch ein Plan aus der Oberfläche wird geprüft. Vertrauen ist keine
            # Architektur - egal ob der Plan vom Modell oder aus dem Formular kommt.
            plan, protokoll = planner.pruefe_plan(plan_roh, air_api.staedteliste())
            ergebnis = ausfuehren(plan)
            ergebnis["protokoll"] = protokoll
            self._json(ergebnis)

        else:
            self._json({"fehler": "unbekannter Pfad"}, 404)


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as fehler:
        # Errno 48 (macOS) bzw. 98 (Linux): Der Port ist belegt. Das passiert oft
        # genug, dass ein Traceback hier nur im Weg steht.
        if fehler.errno not in (48, 98):
            raise
        print(f"Port {port} ist schon belegt.\n")
        print("Wer ihn hält:")
        print(f"    lsof -nP -iTCP:{port} -sTCP:LISTEN\n")
        print("Anderen Port nehmen:")
        print(f"    python3 server.py {port + 1}")
        return 1

    print(f"Oberfläche läuft auf http://localhost:{port}  (Strg+C beendet)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
