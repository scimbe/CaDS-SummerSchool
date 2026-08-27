"""Datenschicht: Luftqualität vom InfraNode-/UBA-Endpunkt holen.

API-Doku: https://infranode.dev/daten/luftqualität-api/
Keylos, kostenlos, 300 Anfragen pro Minute und IP. Quelle: Umweltbundesamt (UBA),
Lizenz DL-DE BY 2.0 - die Attribution steht in jeder Antwort und gehört in den Report.

Wichtig für das Harness-Prinzip: Hier kommen die ZAHLEN her. Das Sprachmodell
sieht sie später nur noch als fertig gerechnetes Ergebnis - es darf sie
formulieren, aber niemals erfinden oder nachrechnen.
"""
import json
import urllib.error
import urllib.request

BASE = "https://infranode.dev/api/v1/cities"

# Was der Endpunkt liefert, mit Einheit und Klartextnamen für den Report.
SCHADSTOFFE = {
    "pm10": ("Feinstaub PM10", "µg/m³"),
    "pm25": ("Feinstaub PM2.5", "µg/m³"),
    "no2":  ("Stickstoffdioxid NO₂", "µg/m³"),
    "o3":   ("Ozon O₃", "µg/m³"),
    "so2":  ("Schwefeldioxid SO₂", "µg/m³"),
}


def fetch_city(slug: str, timeout: int = 20) -> dict:
    """Holt die Messwerte der nächstgelegenen UBA-Station für eine Stadt.

    Gibt immer ein Dict zurück - im Fehlerfall mit 'error' statt 'payload',
    damit ein Ausfall einer Stadt den ganzen Report nicht kippt.
    """
    url = f"{BASE}/{slug}/air-uba"
    req = urllib.request.Request(url, headers={"User-Agent": "CaDS-SummerSchool/First-API"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            antwort = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as fehler:
        return {"slug": slug, "error": f"{type(fehler).__name__}: {fehler}"}

    daten = antwort.get("data", {})
    payload = daten.get("payload", {})
    if not payload:
        return {"slug": slug, "error": "Antwort enthält keine Messwerte."}

    messwerte = {k: payload.get(k) for k in SCHADSTOFFE if payload.get(k) is not None}
    if not messwerte:
        # Kommt in der Praxis vor: Die Station meldet sich, liefert aber gerade
        # keinen einzigen Wert. Das ist kein Absturz, sondern ein Datenausfall.
        return {"slug": slug, "error": "Station lieferte aktuell keine Messwerte."}

    return {
        "slug": slug,
        "station_id": payload.get("station_id"),
        "observed_at": daten.get("observed_at"),
        "messwerte": messwerte,
        "attribution": daten.get("attribution", {}),
    }


def fetch_cities(slugs: list[str]) -> list[dict]:
    """Mehrere Städte nacheinander - reicht völlig, das Rate-Limit ist großzügig."""
    return [fetch_city(s) for s in slugs]


if __name__ == "__main__":  # Schnelltest:  python3 air_api.py
    import sys
    for stadt in sys.argv[1:] or ["hamburg"]:
        print(json.dumps(fetch_city(stadt), indent=2, ensure_ascii=False))
