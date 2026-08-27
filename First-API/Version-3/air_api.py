"""Datenschicht für Version-3: Städteliste und Luftmesswerte von infranode.dev.

Zwei Endpunkte, beide keylos:
    GET /api/v1/cities                      -> Liste aller abgedeckten Städte
    GET /api/v1/cities/<slug>/air-uba       -> Messwerte der nächsten UBA-Station

Die Städteliste ist gleichzeitig unsere **Whitelist**: Was nicht in ihr steht,
darf das Sprachmodell später auch nicht anfragen. Damit kann ein Prompt niemals
einen beliebigen Pfad auf dem Server auslösen.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASIS = "https://infranode.dev/api/v1"
KOPFZEILEN = {"User-Agent": "CaDS-SummerSchool/First-API-V3"}

SCHADSTOFFE = {
    "pm10": {"name": "Feinstaub PM10", "einheit": "µg/m³"},
    "pm25": {"name": "Feinstaub PM2.5", "einheit": "µg/m³"},
    "no2":  {"name": "Stickstoffdioxid NO₂", "einheit": "µg/m³"},
    "o3":   {"name": "Ozon O₃", "einheit": "µg/m³"},
    "so2":  {"name": "Schwefeldioxid SO₂", "einheit": "µg/m³"},
}

_zwischenspeicher: dict[str, tuple[float, object]] = {}
CACHE_SEKUNDEN = 300


def _hole(pfad: str, timeout: int = 20):
    """GET mit kleinem Zwischenspeicher - die Messwerte ändern sich stündlich."""
    jetzt = time.time()
    if pfad in _zwischenspeicher:
        zeit, wert = _zwischenspeicher[pfad]
        if jetzt - zeit < CACHE_SEKUNDEN:
            return wert

    req = urllib.request.Request(f"{BASIS}{pfad}", headers=KOPFZEILEN)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        wert = json.loads(resp.read())
    _zwischenspeicher[pfad] = (jetzt, wert)
    return wert


def staedteliste() -> list[dict]:
    """Alle abgedeckten Städte mit Slug, Name, Bundesland und Einwohnerzahl."""
    try:
        antwort = _hole("/cities?limit=200")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    return [
        {
            "slug": s["slug"],
            "name": s.get("name_de", s["slug"]),
            "land": s.get("state", ""),
            "einwohner": s.get("population"),
        }
        for s in antwort.get("data", [])
    ]


def luftdaten(slug: str) -> dict:
    """Messwerte einer Stadt. Fehler werden zu einem Feld, nicht zu einer Ausnahme."""
    try:
        antwort = _hole(f"/cities/{urllib.parse.quote(slug)}/air-uba")
    except urllib.error.HTTPError as fehler:
        return {"slug": slug, "fehler": f"HTTP {fehler.code}"}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as fehler:
        return {"slug": slug, "fehler": type(fehler).__name__}

    daten = antwort.get("data", {})
    nutzlast = daten.get("payload", {})
    messwerte = {k: nutzlast.get(k) for k in SCHADSTOFFE if nutzlast.get(k) is not None}
    if not messwerte:
        return {"slug": slug, "fehler": "Station meldet aktuell keine Werte"}

    return {
        "slug": slug,
        "station": nutzlast.get("station_id"),
        "gemessen_am": daten.get("observed_at"),
        "messwerte": messwerte,
        "attribution": daten.get("attribution", {}),
        "roh": antwort,          # unverändert, für den Kontroll-Tab in der Oberfläche
    }


if __name__ == "__main__":
    liste = staedteliste()
    print(f"{len(liste)} Städte, z.B.: {', '.join(s['slug'] for s in liste[:8])}")
    print(json.dumps(luftdaten("hamburg")["messwerte"], indent=2, ensure_ascii=False))
