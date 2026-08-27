"""Das Harness: die Leitplanken um das Sprachmodell herum.

Ein Harness ist alles, was NICHT das Modell ist: die Aufgabenteilung, die
Prompts, die Prüfungen, die Wiederholung bei Fehlern und der Notfallplan.
Bei einem kleinen Modell entscheidet das Harness über die Qualität des
Ergebnisses weit stärker als der Prompt.

Die Regel hier lautet:
    Rechnen -> tools.py.    Formulieren -> Modell.    Prüfen -> Harness.

Konkret:
  * Das Modell bekommt nur fertige Zahlen und darf sie nur in Prosa giessen.
  * Nach jeder Antwort prüft prüfe_text(), ob eine Zahl auftaucht, die es in
    den Daten gar nicht gibt. Wenn ja: Antwort verwerfen, mit konkreter
    Rückmeldung erneut fragen.
  * Klappt es nach mehreren Versuchen nicht, schreibt das Harness den Satz
    selbst. Ein Report ohne Modell ist besser als ein Report mit falschen Zahlen.
"""
import re
from pathlib import Path

import llm
from air_api import SCHADSTOFFE

# --- Die Regeln stehen in HARNESS.md, nicht hier -----------------------------
#
# Systemprompt und Grenzwerte werden aus der Datei gelesen. Damit ist HARNESS.md
# die maßgebliche Beschreibung des Verhaltens und nicht bloß Dokumentation, die
# neben dem Code veraltet. Wer den Systemprompt ändern will, ändert HARNESS.md.

REGELDATEI = Path(__file__).with_name("HARNESS.md")


def _lies_regeln() -> tuple[str, dict]:
    """Holt Systemprompt und Grenzen aus HARNESS.md."""
    text = REGELDATEI.read_text(encoding="utf-8")

    # Systemprompt: der erste ```text-Block nach der Überschrift "## Systemprompt".
    abschnitt = text.split("## Systemprompt", 1)[1]
    system = abschnitt.split("```text", 1)[1].split("```", 1)[0].strip()

    # Grenzen: die Zeilen "- `name: wert`" unter "## Grenzen".
    grenzen_text = text.split("## Grenzen", 1)[1].split("\n## ", 1)[0]
    grenzen = {
        name: int(wert)
        for name, wert in re.findall(r"`(\w+):\s*([\d.]+)`", grenzen_text)
        if wert.isdigit()
    }
    grenzen.update({
        name: float(wert)
        for name, wert in re.findall(r"`(\w+):\s*([\d.]+)`", grenzen_text)
        if not wert.isdigit()
    })
    return system, grenzen


def _lies_darstellung() -> tuple[dict, str, str]:
    """Farbskala, Akzentfarbe und Balkenbezug aus HARNESS.md.

    Damit steuert dieselbe Datei den Text UND sein Aussehen. Wer die Tabelle
    unter "## Aufbereitung" ändert, ändert das PDF.
    """
    text = REGELDATEI.read_text(encoding="utf-8")
    if "## Aufbereitung" not in text:
        return {}, "#204c86", "index"
    abschnitt = text.split("## Aufbereitung", 1)[1].split("\n## ", 1)[0]

    farben = {
        stufe.strip(): farbe
        for stufe, farbe in re.findall(r"\|\s*([^|`#]+?)\s*\|\s*`(#[0-9a-fA-F]{3,8})`\s*\|", abschnitt)
    }
    akzent = re.search(r"`akzent:\s*(#[0-9a-fA-F]{3,8})`", abschnitt)
    bezug = re.search(r"`balken_bezug:\s*(\w+)`", abschnitt)
    return farben, (akzent.group(1) if akzent else "#204c86"), (bezug.group(1) if bezug else "index")


SYSTEM, GRENZEN = _lies_regeln()
FARBEN, AKZENT, BALKEN_BEZUG = _lies_darstellung()

MAX_VERSUCHE = int(GRENZEN.get("max_versuche", 3))
TEMPERATUR = float(GRENZEN.get("temperature", 0.3))
TOKENS_KURZFASSUNG = int(GRENZEN.get("max_tokens_kurzfassung", 320))
TOKENS_STADT = int(GRENZEN.get("max_tokens_stadt", 220))


# --- Prüfung ----------------------------------------------------------------

ZAHL = re.compile(r"\d+(?:[.,]\d+)?")


def _normalisieren(text: str) -> str:
    return text.replace(",", ".").rstrip("0").rstrip(".") if "." in text.replace(",", ".") else text


def erlaubte_zahlen(*werte, mit_messwerten: bool = True) -> set[str]:
    """Sammelt alle Zahlen, die im Text vorkommen DÜRFEN, in normalisierter Form.

    mit_messwerten=False heißt: gar keine Messwerte erlaubt. Das nutzen wir für
    die Kurzfassung. Grund (siehe HARNESS.md): Ein Mittelwert und ein Stadtwert
    sehen für das Modell gleich aus, und es ordnet gern den einen der falschen
    Stadt zu. Eine Zahl, die nie genannt wird, kann nicht falsch zugeordnet werden.
    """
    erlaubt: set[str] = set()

    def sammeln(objekt):
        if isinstance(objekt, dict):
            for v in objekt.values():
                sammeln(v)
        elif isinstance(objekt, (list, tuple)):
            for v in objekt:
                sammeln(v)
        elif isinstance(objekt, (int, float)):
            erlaubt.add(_normalisieren(str(objekt)))
        elif isinstance(objekt, str):
            for treffer in ZAHL.findall(objekt):
                erlaubt.add(_normalisieren(treffer))

    if mit_messwerten:
        sammeln(list(werte))

    # Zahlen, die zu Namen gehören statt zu Messwerten: PM10, PM2.5, NO2, O3, SO2.
    # Ohne diese Ausnahme würde "Feinstaub PM2.5" als erfundene Zahl gelten.
    sammeln([name for name, _ in SCHADSTOFFE.values()])

    # Jahreszahlen und Zählwörter bis zwölf sind unkritisch und stehen oft im Satzbau.
    erlaubt.update(str(n) for n in range(0, 13))
    return erlaubt


def prüfe_text(text: str, erlaubt: set[str]) -> list[str]:
    """Gibt die Zahlen zurück, die im Text stehen, aber nicht in den Daten."""
    gefunden = {_normalisieren(t) for t in ZAHL.findall(text)}
    return sorted(gefunden - erlaubt)


# --- Der Aufruf mit Leitplanken ----------------------------------------------

def schreibe_abschnitt(auftrag: str, daten, notfalltext: str, *,
                       max_tokens: int | None = None,
                       mit_messwerten: bool = True) -> tuple[str, dict]:
    """Lässt das Modell einen Abschnitt schreiben und prüft ihn.

    Rückgabe: (Text, Protokoll). Das Protokoll wandert in den Report - so sieht
    man im fertigen PDF, wie oft nachgebessert werden musste.
    """
    max_tokens = max_tokens or TOKENS_KURZFASSUNG
    erlaubt = erlaubte_zahlen(daten, mit_messwerten=mit_messwerten)
    verlauf = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": auftrag}]
    protokoll = {"versuche": 0, "beanstandet": [], "quelle": "modell"}

    for versuch in range(1, MAX_VERSUCHE + 1):
        protokoll["versuche"] = versuch
        try:
            text = llm.chat(verlauf, temperature=TEMPERATUR, max_tokens=max_tokens).get("content", "").strip()
        except Exception as fehler:  # Netz weg, Timeout, 500er - der Report entsteht trotzdem
            protokoll.update(quelle="notfall", fehler=str(fehler))
            return notfalltext, protokoll

        text = re.sub(r"^#+ .*$", "", text, flags=re.MULTILINE).strip()
        verstöße = prüfe_text(text, erlaubt)

        if not verstöße:
            return text, protokoll

        protokoll["beanstandet"].append(verstöße)
        verlauf += [
            {"role": "assistant", "content": text},
            {"role": "user", "content": (
                ("Der Abschnitt darf überhaupt keine Messwerte enthalten. Diese Zahlen "
                 "müssen raus: " if not mit_messwerten else
                 "Diese Zahlen stehen nicht in den Daten: ")
                + ", ".join(verstöße)
                + ". Schreibe den Abschnitt neu."
            )},
        ]

    protokoll["quelle"] = "notfall"
    return notfalltext, protokoll


# --- Die Aufträge -----------------------------------------------------------

def auftrag_kurzfassung(vgl: dict) -> str:
    """Bewusst ohne Messwerte - siehe erlaubte_zahlen()."""
    zeilen = [
        f"- Platz {e['platz']}: {e['name']}, Stufe '{e['stufe']}', "
        f"ausschlaggebend {e['treiber']}"
        for e in vgl["rangliste"]
    ]
    über = (
        "Über einem EU-Grenzwert liegen: "
        + "; ".join(f"{a['stadt']} bei {', '.join(a['schadstoffe'])}" for a in vgl["auffällig"])
        if vgl["auffällig"] else "Keine Stadt liegt über einem EU-Grenzwert."
    )
    return (
        "Schreibe die Kurzfassung eines Luftqualitätsberichts, 3 bis 4 Sätze.\n\n"
        f"Untersuchte Städte. Platz 1 ist die am STÄRKSTEN belastete Stadt, "
        f"der letzte Platz die am GERINGSTEN belastete:\n"
        + "\n".join(zeilen)
        + f"\n{über}"
        + f"\n\nAm stärksten belastet ist {vgl['schlechtestes']}, am geringsten "
          f"{vgl['bestes']}. Nenne beide beim Namen und sage, welcher Schadstoff "
          "das Bild bestimmt.\n"
          "WICHTIG: Nenne in diesem Abschnitt keine einzige Messzahl. Die Zahlen stehen "
          "in der Tabelle darunter. Schreibe qualitativ ('am höchsten', 'am geringsten'). "
          "Keine Bewertung der Gesundheitslage."
    )


def auftrag_stadt(stadt: dict) -> str:
    werte = "\n".join(
        f"- {w['name']}: {w['wert']} {w['einheit']} -> Stufe '{w['stufe']}'"
        + (f" (EU-Grenzwert {w['eu_grenzwert']} µg/m³ überschritten)" if w["über_grenzwert"] else "")
        for w in stadt["werte"]
    )
    fehlend = (
        f"\nNicht gemessen an dieser Station: {', '.join(stadt['fehlende_schadstoffe'])}."
        if stadt["fehlende_schadstoffe"] else ""
    )
    return (
        f"Schreibe 2 bis 3 Sätze über die Luftqualität in {stadt['name']}.\n\n"
        f"Messwerte der UBA-Station {stadt['station_id']}:\n{werte}"
        f"\nGesamteinstufung: '{stadt['gesamtstufe']}', bestimmt durch {stadt['treiber']}."
        f"{fehlend}"
        "\n\nBeginne mit dem Stadtnamen. Erwähne den ausschlaggebenden Schadstoff mit "
        "seinem Wert. Wenn Werte fehlen, sage das in einem Nebensatz."
    )


# --- Notfalltexte (rein aus den Daten gebaut, ohne Modell) --------------------

def notfall_kurzfassung(vgl: dict) -> str:
    return (
        f"Ausgewertet wurden mehrere Städte. Die beste Einstufung erreicht "
        f"{vgl['bestes']}, die schlechteste {vgl['schlechtestes']}. "
        + (
            "Kein Messwert liegt über einem EU-Grenzwert."
            if not vgl["auffällig"]
            else "Grenzwertüberschreitungen: "
            + "; ".join(f"{a['stadt']} ({', '.join(a['schadstoffe'])})" for a in vgl["auffällig"])
            + "."
        )
    )


def notfall_stadt(stadt: dict) -> str:
    w = stadt["werte"][0]
    return (
        f"{stadt['name']} wird insgesamt mit '{stadt['gesamtstufe']}' eingestuft. "
        f"Ausschlaggebend ist {w['name']} mit {w['wert']} {w['einheit']}. "
        f"Gemessen an UBA-Station {stadt['station_id']}."
    )
