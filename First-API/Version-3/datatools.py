"""Werkzeuge zur Aufbereitung - der deterministische Teil.

Jede Zahl, die in der Oberfläche erscheint, kommt aus dieser Datei. Das
Sprachmodell fasst hier nichts an; es darf später nur bestimmen, WELCHE dieser
Funktionen mit WELCHEN erlaubten Parametern laufen.
"""
import re
from pathlib import Path

from air_api import SCHADSTOFFE

INDEX_STUFEN = ["sehr gut", "gut", "mäßig", "schlecht", "sehr schlecht"]

# Obergrenzen der ersten vier Stufen des UBA-Luftqualitätsindex, in µg/m³.
SCHWELLEN = {
    "pm10": [20, 35, 50, 100],
    "pm25": [10, 20, 25, 50],
    "no2":  [20, 40, 100, 200],
    "o3":   [60, 120, 180, 240],
    "so2":  [50, 125, 350, 500],
}

EU_GRENZWERTE = {"pm10": 40, "pm25": 25, "no2": 40, "o3": 120}

RUECKFALL_FARBEN = {
    "sehr gut": "#2e7d32", "gut": "#7cb342", "mäßig": "#f9a825",
    "schlecht": "#ef6c00", "sehr schlecht": "#c62828", "unbekannt": "#9e9e9e",
}


def _darstellung() -> tuple[dict, str]:
    """Farbskala und Balkenbezug aus HARNESS.md.

    Wird bei jedem Aufruf gelesen, nicht beim Start zwischengespeichert: So
    wirkt eine Änderung an der Datei sofort, ohne Neustart des Servers.
    """
    datei = Path(__file__).with_name("HARNESS.md")
    try:
        text = datei.read_text(encoding="utf-8")
        abschnitt = text.split("## Aufbereitung", 1)[1].split("\n## ", 1)[0]
    except (OSError, IndexError):
        return dict(RUECKFALL_FARBEN), "index"

    farben = {
        stufe.strip(): farbe
        for stufe, farbe in re.findall(r"\|\s*([^|`#]+?)\s*\|\s*`(#[0-9a-fA-F]{3,8})`\s*\|", abschnitt)
    }
    bezug = re.search(r"`balken_bezug:\s*(\w+)`", abschnitt)
    return (farben or dict(RUECKFALL_FARBEN)), (bezug.group(1) if bezug else "index")


def farbe_fuer(stufe: str) -> str:
    farben, _ = _darstellung()
    return farben.get(stufe, RUECKFALL_FARBEN.get(stufe, "#9e9e9e"))


def einstufen(schadstoff: str, wert: float) -> str:
    grenzen = SCHWELLEN.get(schadstoff)
    if not grenzen:
        return "unbekannt"
    for stufe, grenze in zip(INDEX_STUFEN, grenzen):
        if wert <= grenze:
            return stufe
    return INDEX_STUFEN[-1]


def aufbereiten(rohdaten: dict, name: str, schadstoffe: list[str]) -> dict:
    """Eine API-Antwort wird zu einer Zeile für die Oberfläche."""
    if "fehler" in rohdaten:
        return {"slug": rohdaten["slug"], "name": name, "ok": False, "fehler": rohdaten["fehler"]}

    farben, bezug = _darstellung()

    werte = []
    for schluessel in schadstoffe:
        wert = rohdaten["messwerte"].get(schluessel)
        if wert is None:
            continue
        stufe = einstufen(schluessel, wert)
        grenzwert = EU_GRENZWERTE.get(schluessel)
        werte.append({
            "schluessel": schluessel,
            "name": SCHADSTOFFE[schluessel]["name"],
            "einheit": SCHADSTOFFE[schluessel]["einheit"],
            "wert": wert,
            "stufe": stufe,
            "farbe": farben.get(stufe, RUECKFALL_FARBEN[stufe]),
            "stufe_index": INDEX_STUFEN.index(stufe),
            # Anteil an der Obergrenze der Stufe "gut": macht Schadstoffe vergleichbar.
            "belastung": round(wert / SCHWELLEN[schluessel][1], 2),
            # Bezugsgröße laut HARNESS.md: Abstand zum Extremfall oder zur
            # rechtlichen Grenze. Das ändert die Aussage der Grafik deutlich.
            "balken": min(100, round(wert / (
                grenzwert if bezug == "grenzwert" and grenzwert else SCHWELLEN[schluessel][-1]
            ) * 100)),
            "ueber_eu": bool(grenzwert and wert > grenzwert),
            "eu_grenzwert": grenzwert,
        })

    if not werte:
        return {"slug": rohdaten["slug"], "name": name, "ok": False,
                "fehler": "Keiner der gewählten Schadstoffe wird hier gemessen"}

    schlechtester = max(werte, key=lambda w: (w["stufe_index"], w["belastung"]))
    return {
        "slug": rohdaten["slug"],
        "name": name,
        "ok": True,
        "station": rohdaten.get("station"),
        "gemessen_am": rohdaten.get("gemessen_am"),
        "werte": werte,
        "stufe": schlechtester["stufe"],
        "farbe": schlechtester["farbe"],
        "treiber": schlechtester["name"],
        "belastungsindex": schlechtester["belastung"],
    }


def sortieren(zeilen: list[dict], nach: str) -> list[dict]:
    """Sortierung - bewusst eine feste Auswahl, keine freie Formel."""
    gueltig = [z for z in zeilen if z["ok"]]
    fehler = [z for z in zeilen if not z["ok"]]
    schluessel = {
        "belastung_absteigend": lambda z: (-z["belastungsindex"], z["name"]),
        "belastung_aufsteigend": lambda z: (z["belastungsindex"], z["name"]),
        "name": lambda z: z["name"],
    }.get(nach, lambda z: (-z["belastungsindex"], z["name"]))
    return sorted(gueltig, key=schluessel) + fehler


def kennzahlen(zeilen: list[dict]) -> dict:
    """Summe der Auswertung - wieder reine Rechnung, kein Modell."""
    gueltig = [z for z in zeilen if z["ok"]]
    if not gueltig:
        return {"anzahl": 0}

    alle_werte = [w for z in gueltig for w in z["werte"]]
    mittel = {}
    for schluessel in SCHADSTOFFE:
        passend = [w["wert"] for w in alle_werte if w["schluessel"] == schluessel]
        if passend:
            mittel[schluessel] = round(sum(passend) / len(passend), 1)

    return {
        "anzahl": len(gueltig),
        "fehlend": [z["slug"] for z in zeilen if not z["ok"]],
        "hoechste": gueltig[0]["name"] if gueltig else None,
        "mittelwerte": mittel,
        "ueber_eu": [
            {"stadt": z["name"], "schadstoffe": [w["name"] for w in z["werte"] if w["ueber_eu"]]}
            for z in gueltig if any(w["ueber_eu"] for w in z["werte"])
        ],
        "stufen_verteilung": {
            stufe: sum(1 for z in gueltig if z["stufe"] == stufe)
            for stufe in INDEX_STUFEN
            if any(z["stufe"] == stufe for z in gueltig)
        },
    }
