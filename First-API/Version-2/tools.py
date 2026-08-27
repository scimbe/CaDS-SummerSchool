"""Werkzeuge: alles, was gerechnet, eingeordnet und geprüft wird.

Das ist die wichtigste Datei für die Idee hinter dem Harness:
Jede Zahl, jede Einstufung und jede Rangfolge entsteht HIER - in normalem,
testbarem Python. Das Sprachmodell bekommt später nur das fertige Ergebnis
und darf daraus Fließtext machen.

Ein kleines Modell rechnet unzuverlässig und vergleicht Zahlen gerne falsch.
Also lassen wir es nicht rechnen. Genau das ist der Hebel.
"""
from air_api import SCHADSTOFFE

# Schwellen des UBA-Luftqualitätsindex in µg/m³ (obere Grenze je Stufe).
# Quelle: Umweltbundesamt, "Luftqualitätsindex".
INDEX_STUFEN = ["sehr gut", "gut", "mäßig", "schlecht", "sehr schlecht"]

SCHWELLEN = {
    "pm10": [20, 35, 50, 100],
    "pm25": [10, 20, 25, 50],
    "no2":  [20, 40, 100, 200],
    "o3":   [60, 120, 180, 240],
    "so2":  [50, 125, 350, 500],
}

# Der API-Slug ist kleingeschrieben und ohne Umlaute ("muenchen"). Für den Bericht
# brauchen wir den richtigen Namen; alles Übrige leiten wir aus dem Slug ab.
STADTNAMEN = {
    "muenchen": "München",
    "koeln": "Köln",
    "duesseldorf": "Düsseldorf",
    "nuernberg": "Nürnberg",
    "frankfurt-am-main": "Frankfurt am Main",
    "halle-saale": "Halle (Saale)",
    "offenbach-am-main": "Offenbach am Main",
    "muelheim-an-der-ruhr": "Mülheim an der Ruhr",
    "saarbruecken": "Saarbrücken",
    "osnabrueck": "Osnabrück",
    "luebeck": "Lübeck",
    "goettingen": "Göttingen",
}


def stadtname(slug: str) -> str:
    """Slug -> lesbarer Stadtname."""
    return STADTNAMEN.get(slug, slug.replace("-", " ").title())


# EU-Grenzwerte zur Einordnung (Jahresmittel bzw. Zielwert) - nur als Kontext,
# ein Einzelmesswert verletzt keinen Jahresmittelwert.
EU_GRENZWERTE = {"pm10": 40, "pm25": 25, "no2": 40, "o3": 120}


def einstufen(schadstoff: str, wert: float) -> str:
    """Ordnet einen Messwert einer der fünf UBA-Indexstufen zu."""
    grenzen = SCHWELLEN.get(schadstoff)
    if grenzen is None:
        return "unbekannt"
    for stufe, grenze in zip(INDEX_STUFEN, grenzen):
        if wert <= grenze:
            return stufe
    return INDEX_STUFEN[-1]


def stadt_auswerten(rohdaten: dict) -> dict:
    """Macht aus einer API-Antwort eine fertig bewertete Stadt.

    Die Gesamteinstufung ist bewusst der SCHLECHTESTE Einzelwert - so macht es
    der UBA-Index auch. Würde man mitteln, verschwände ein guter Wert einen
    schlechten.
    """
    if "error" in rohdaten:
        return {"slug": rohdaten["slug"], "ok": False, "fehler": rohdaten["error"]}

    werte = []
    for schlüssel, wert in rohdaten["messwerte"].items():
        name, einheit = SCHADSTOFFE[schlüssel]
        stufe = einstufen(schlüssel, wert)
        grenzwert = EU_GRENZWERTE.get(schlüssel)
        werte.append({
            "schlüssel": schlüssel,
            "name": name,
            "wert": wert,
            "einheit": einheit,
            "stufe": stufe,
            "stufe_index": INDEX_STUFEN.index(stufe) if stufe in INDEX_STUFEN else -1,
            "eu_grenzwert": grenzwert,
            "über_grenzwert": bool(grenzwert and wert > grenzwert),
            # Zwei Bezugsgrößen für die Balkenlänge, beide in Prozent und bei 100
            # gedeckelt. Welche im Report gilt, steht in HARNESS.md unter
            # "balken_bezug". Die Wahl ändert die Aussage der Grafik erheblich:
            # "index" zeigt den Abstand zum Extremfall, "grenzwert" den zur
            # rechtlichen Grenze - bei der zweiten schlagen die Balken viel weiter aus.
            "balken_index": min(100, round(wert / SCHWELLEN[schlüssel][-1] * 100)),
            "balken_grenzwert": min(100, round(wert / grenzwert * 100)) if grenzwert else
                                min(100, round(wert / SCHWELLEN[schlüssel][-1] * 100)),
            # Belastung relativ zur Obergrenze der Stufe "gut". 1.0 heißt: genau
            # an der Grenze zu "mäßig". Erst das macht Schadstoffe vergleichbar -
            # 79 µg/m³ Ozon und 23 µg/m³ Feinstaub sind sonst zwei Zahlen ohne Bezug.
            "belastung": round(wert / SCHWELLEN[schlüssel][1], 2),
        })

    if not werte:
        return {"slug": rohdaten["slug"], "ok": False, "fehler": "Keine verwertbaren Messwerte."}

    werte.sort(key=lambda w: (w["stufe_index"], w["belastung"]), reverse=True)
    schlechtester = werte[0]

    return {
        "slug": rohdaten["slug"],
        "name": stadtname(rohdaten["slug"]),
        "ok": True,
        "station_id": rohdaten.get("station_id"),
        "observed_at": rohdaten.get("observed_at"),
        "werte": werte,
        "gesamtstufe": schlechtester["stufe"],
        # Kennzahl der Stadt: die höchste Einzelbelastung. Ohne sie wäre die
        # Rangfolge bei gleicher Stufe alphabetisch - also willkürlich.
        "belastungsindex": schlechtester["belastung"],
        "gesamtstufe_index": schlechtester["stufe_index"],
        "treiber": schlechtester["name"],
        "fehlende_schadstoffe": [
            SCHADSTOFFE[k][0] for k in SCHADSTOFFE if k not in rohdaten["messwerte"]
        ],
        "grenzwert_überschreitungen": [w["name"] for w in werte if w["über_grenzwert"]],
    }


def vergleich(städte: list[dict]) -> dict:
    """Rangfolge und Kennzahlen über alle Städte - ebenfalls reine Rechnung."""
    gültig = [s for s in städte if s["ok"]]
    if not gültig:
        return {"anzahl": 0, "rangliste": [], "auffällig": []}

    rangliste = sorted(
        gültig,
        key=lambda s: (-s["gesamtstufe_index"], -s["belastungsindex"], s["name"]),
    )

    def mittel(schlüssel: str) -> float | None:
        werte = [w["wert"] for s in gültig for w in s["werte"] if w["schlüssel"] == schlüssel]
        return round(sum(werte) / len(werte), 1) if werte else None

    return {
        "anzahl": len(gültig),
        "fehlgeschlagen": [s["slug"] for s in städte if not s["ok"]],
        "rangliste": [
            {"platz": i, "name": s["name"], "stufe": s["gesamtstufe"],
             "treiber": s["treiber"], "belastungsindex": s["belastungsindex"]}
            for i, s in enumerate(rangliste, start=1)
        ],
        "bestes": rangliste[-1]["name"],
        "schlechtestes": rangliste[0]["name"],
        "mittelwerte": {k: mittel(k) for k in SCHADSTOFFE},
        "auffällig": [
            {"stadt": s["name"], "schadstoffe": s["grenzwert_überschreitungen"]}
            for s in gültig if s["grenzwert_überschreitungen"]
        ],
    }


if __name__ == "__main__":  # Schnelltest:  python3 tools.py
    import json

    from air_api import fetch_cities

    ausgewertet = [stadt_auswerten(r) for r in fetch_cities(["hamburg", "muenchen", "berlin"])]
    print(json.dumps(vergleich(ausgewertet), indent=2, ensure_ascii=False))
