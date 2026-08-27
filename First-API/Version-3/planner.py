"""Vom Prompt zum geprüften Plan.

Der ganze Umgang mit dem Sprachmodell steckt hier - und er ist eng:
Das Modell darf genau eine Funktion aufrufen (plan_erstellen) und bekommt in
deren Beschreibung die vollständige Liste der erlaubten Werte. Was es trotzdem
danebenlegt, repariert pruefe_plan() deterministisch.

Die Regeln stehen in HARNESS.md und werden von dort gelesen, nicht hier
festverdrahtet.
"""
import json
import re
import unicodedata
from pathlib import Path

import llm
from air_api import SCHADSTOFFE

REGELDATEI = Path(__file__).with_name("HARNESS.md")

SORTIERUNGEN = ["belastung_absteigend", "belastung_aufsteigend", "name"]
DARSTELLUNGEN = ["tabelle", "balken", "karten"]

STANDARDPLAN = {
    "staedte": ["hamburg", "berlin", "muenchen", "koeln", "stuttgart"],
    "schadstoffe": list(SCHADSTOFFE),
    "sortierung": "belastung_absteigend",
    "darstellung": "balken",
    "titel": "Luftqualität in deutschen Großstädten",
    "kommentar": True,
}


def _lies_regeln() -> tuple[str, dict]:
    """Systemprompt und Grenzen aus HARNESS.md - die Datei ist die Autorität."""
    text = REGELDATEI.read_text(encoding="utf-8")
    system = text.split("## Systemprompt", 1)[1].split("```text", 1)[1].split("```", 1)[0].strip()
    grenzen_text = text.split("## Grenzen", 1)[1].split("\n## ", 1)[0]
    grenzen = {}
    for name, wert in re.findall(r"`(\w+):\s*([\d.]+)`", grenzen_text):
        grenzen[name] = int(wert) if wert.isdigit() else float(wert)
    return system, grenzen


SYSTEM, GRENZEN = _lies_regeln()
MAX_STAEDTE = int(GRENZEN.get("max_staedte", 8))
MAX_TITEL = int(GRENZEN.get("max_titel", 80))
MAX_VERSUCHE = int(GRENZEN.get("max_versuche", 2))
TEMPERATUR = float(GRENZEN.get("temperature", 0.2))
MAX_TOKENS = int(GRENZEN.get("max_tokens", 400))


# --- Städte auflösen ---------------------------------------------------------

def _normal(text: str) -> str:
    """'München' und 'Muenchen' und 'MUNICH' sollen dasselbe ergeben."""
    text = text.lower().strip()
    text = (text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text)


def aufloesen(eingabe: str, staedte: list[dict]) -> str | None:
    """Macht aus 'München', 'munich' oder 'muenchen ' den Slug 'muenchen'.

    Rein deterministisch. Das Modell noch einmal zu fragen wäre langsamer und
    unzuverlässiger als ein Wörterbuch-Nachschlag.
    """
    ziel = _normal(eingabe)
    if not ziel:
        return None
    nachschlag = {}
    for stadt in staedte:
        nachschlag.setdefault(_normal(stadt["slug"]), stadt["slug"])
        nachschlag.setdefault(_normal(stadt["name"]), stadt["slug"])
    if ziel in nachschlag:
        return nachschlag[ziel]
    # Zweiter Anlauf: eindeutiger Präfix, fängt 'frankfurt' -> 'frankfurt-am-main'.
    treffer = sorted({slug for norm, slug in nachschlag.items() if norm.startswith(ziel)})
    return treffer[0] if len(treffer) == 1 else None


# --- Prüfung und Reparatur ---------------------------------------------------

def pruefe_plan(plan: dict, staedte: list[dict]) -> tuple[dict, list[str]]:
    """Bringt einen beliebigen Plan in die erlaubte Form.

    Wichtig: Es wird repariert, nicht abgelehnt. Ein Plan mit einer erfundenen
    Stadt ist zu 80 % brauchbar - den Rest wegzuwerfen wäre unfreundlich.
    Jede Korrektur landet im Protokoll und wird in der Oberfläche angezeigt.
    """
    protokoll: list[str] = []
    geprueft: dict = {}

    # Städte
    slugs: list[str] = []
    for eintrag in plan.get("staedte") or []:
        if not isinstance(eintrag, str):
            continue
        slug = aufloesen(eintrag, staedte)
        if slug is None:
            protokoll.append(f"Stadt „{eintrag}“ kennt die API nicht — entfernt.")
        elif slug in slugs:
            protokoll.append(f"Stadt „{eintrag}“ war doppelt — einmal behalten.")
        else:
            if _normal(slug) != _normal(eintrag):
                protokoll.append(f"„{eintrag}“ aufgelöst zu „{slug}“.")
            slugs.append(slug)

    if not slugs:
        slugs = list(STANDARDPLAN["staedte"])
        protokoll.append("Keine gültige Stadt im Plan — Standardauswahl eingesetzt.")
    if len(slugs) > MAX_STAEDTE:
        protokoll.append(f"{len(slugs)} Städte angefragt, {MAX_STAEDTE} sind das Maximum — gekürzt.")
        slugs = slugs[:MAX_STAEDTE]
    geprueft["staedte"] = slugs

    # Schadstoffe
    stoffe = [s for s in (plan.get("schadstoffe") or []) if s in SCHADSTOFFE]
    unbekannt = [s for s in (plan.get("schadstoffe") or []) if s not in SCHADSTOFFE]
    if unbekannt:
        protokoll.append(f"Unbekannte Schadstoffe entfernt: {', '.join(map(str, unbekannt))}.")
    if not stoffe:
        stoffe = list(SCHADSTOFFE)
        protokoll.append("Kein gültiger Schadstoff im Plan — alle fünf eingesetzt.")
    geprueft["schadstoffe"] = stoffe

    # Auswahllisten
    for feld, erlaubt in (("sortierung", SORTIERUNGEN), ("darstellung", DARSTELLUNGEN)):
        wert = plan.get(feld)
        if wert not in erlaubt:
            if wert is not None:
                protokoll.append(f"{feld}=„{wert}“ ist nicht erlaubt — „{STANDARDPLAN[feld]}“ gesetzt.")
            wert = STANDARDPLAN[feld]
        geprueft[feld] = wert

    # Titel: Lässt das Modell ihn weg, bauen wir ihn aus dem Plan - das ist
    # verlässlicher als eine generische Überschrift und kostet keinen Aufruf.
    titel = str(plan.get("titel") or "").strip()
    if not titel:
        titel = _titel_aus_plan(geprueft["staedte"], geprueft["schadstoffe"], staedte)
        protokoll.append(f"Kein Titel im Plan — aus der Auswahl gebildet: „{titel}“.")
    if len(titel) > MAX_TITEL:
        titel = titel[:MAX_TITEL].rstrip() + "…"
        protokoll.append(f"Titel war länger als {MAX_TITEL} Zeichen — gekürzt.")
    geprueft["titel"] = titel

    geprueft["kommentar"] = bool(plan.get("kommentar", False))
    return geprueft, protokoll


def _titel_aus_plan(slugs: list[str], stoffe: list[str], staedte: list[dict]) -> str:
    """Überschrift aus der Auswahl - rein beschreibend, ohne Wertung."""
    namen = {s["slug"]: s["name"] for s in staedte}
    orte = [namen.get(s, s) for s in slugs]
    ort_text = (
        orte[0] if len(orte) == 1
        else " und ".join(orte) if len(orte) == 2
        else f"{', '.join(orte[:-1])} und {orte[-1]}" if len(orte) <= 4
        else f"{len(orte)} Städten"
    )
    stoff_text = (
        "Luftqualität" if len(stoffe) >= len(SCHADSTOFFE)
        else " und ".join(SCHADSTOFFE[k]["name"] for k in stoffe) if len(stoffe) <= 2
        else f"{len(stoffe)} Schadstoffe"
    )
    return f"{stoff_text} in {ort_text}"[:MAX_TITEL]


# --- Die Funktionsbeschreibung für das Modell --------------------------------

def werkzeug(staedte: list[dict]) -> list[dict]:
    """Die Tool-Definition. Die Städteliste kommt live aus der API.

    Bei 84 Städten würde die vollständige Aufzählung als enum den Prompt
    aufblähen. Wir nennen die größten als Beispiele und lassen den Rest über die
    Auflösung laufen - das ist für ein kleines Modell die freundlichere Variante.
    """
    beispiele = ", ".join(s["slug"] for s in staedte[:25])
    return [{
        "type": "function",
        "function": {
            "name": "plan_erstellen",
            "description": (
                "Erstellt den Anzeigeplan für die Luftqualitäts-Oberfläche. "
                "Wähle Städte, Schadstoffe, Sortierung und Darstellung passend zur Anfrage."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "staedte": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            f"Städte als Slug, höchstens {MAX_STAEDTE}. "
                            f"Verfügbar sind 84 deutsche Großstädte, darunter: {beispiele}. "
                            "Slugs sind kleingeschrieben und ohne Umlaute (muenchen, koeln)."
                        ),
                    },
                    "schadstoffe": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(SCHADSTOFFE)},
                        "description": "pm10 und pm25 sind Feinstaub, no2 Stickstoffdioxid, o3 Ozon, so2 Schwefeldioxid.",
                    },
                    "sortierung": {"type": "string", "enum": SORTIERUNGEN},
                    "darstellung": {
                        "type": "string",
                        "enum": DARSTELLUNGEN,
                        "description": "tabelle für Zahlenvergleich, balken für Belastung auf einen Blick, karten für wenige Städte im Detail.",
                    },
                    "titel": {"type": "string", "description": f"Überschrift, höchstens {MAX_TITEL} Zeichen."},
                    "kommentar": {"type": "string", "enum": ["ja", "nein"],
                                  "description": "ja, wenn die Anfrage nach einer Einordnung oder Erklärung fragt."},
                },
                "required": ["staedte", "schadstoffe", "darstellung"],
            },
        },
    }]


# --- Der eigentliche Aufruf --------------------------------------------------

def plane(prompt: str, staedte: list[dict]) -> dict:
    """Prompt -> geprüfter Plan. Wirft nie; im Zweifel kommt der Standardplan."""
    nachrichten = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    protokoll: list[str] = []

    for versuch in range(1, MAX_VERSUCHE + 1):
        try:
            antwort = llm.chat(
                nachrichten, tools=werkzeug(staedte),
                temperature=TEMPERATUR, max_tokens=MAX_TOKENS,
            )
        except Exception as fehler:
            protokoll.append(f"Modell nicht erreichbar ({type(fehler).__name__}) — Standardplan.")
            plan, weitere = pruefe_plan(dict(STANDARDPLAN), staedte)
            return {"plan": plan, "protokoll": protokoll + weitere, "versuche": versuch,
                    "quelle": "notfall"}

        aufrufe = antwort.get("tool_calls") or []
        if not aufrufe:
            # Kommt bei kleinen Modellen vor: Es antwortet mit Prosa statt mit dem Aufruf.
            protokoll.append("Das Modell hat keinen Plan aufgerufen — noch einmal gefragt.")
            nachrichten += [
                antwort,
                {"role": "user", "content": "Rufe jetzt plan_erstellen auf. Kein Fließtext."},
            ]
            continue

        try:
            roh = json.loads(aufrufe[0]["function"]["arguments"])
        except json.JSONDecodeError:
            protokoll.append("Argumente waren kein gültiges JSON — noch einmal gefragt.")
            continue

        # "ja"/"nein" aus dem enum in einen echten Wahrheitswert übersetzen.
        if isinstance(roh.get("kommentar"), str):
            roh["kommentar"] = roh["kommentar"].strip().lower() in {"ja", "true", "yes"}

        plan, weitere = pruefe_plan(roh, staedte)
        return {"plan": plan, "roh": roh, "protokoll": protokoll + weitere,
                "versuche": versuch, "quelle": "modell"}

    protokoll.append(f"Nach {MAX_VERSUCHE} Versuchen kein Plan — Standardplan eingesetzt.")
    plan, weitere = pruefe_plan(dict(STANDARDPLAN), staedte)
    return {"plan": plan, "protokoll": protokoll + weitere, "versuche": MAX_VERSUCHE,
            "quelle": "notfall"}


if __name__ == "__main__":
    import sys

    from air_api import staedteliste

    frage = " ".join(sys.argv[1:]) or "Zeig mir Feinstaub in den drei größten Städten Bayerns"
    ergebnis = plane(frage, staedteliste())
    print(f"> {frage}\n")
    print(json.dumps(ergebnis["plan"], indent=2, ensure_ascii=False))
    print("\nProtokoll:", *ergebnis["protokoll"] or ["(nichts zu korrigieren)"], sep="\n  ")


# --- Optionaler Kommentar zum Ergebnis ---------------------------------------
#
# Derselbe Grundsatz wie in Version-2: Das Modell bekommt fertige Zahlen und
# formuliert, es rechnet nicht. Und weil ein Mittelwert und ein Stadtwert für das
# Modell gleich aussehen, bekommt der Kommentar überhaupt keine Zahlen.

ZAHL = re.compile(r"\d+(?:[.,]\d+)?")

KOMMENTAR_SYSTEM = (
    "Du schreibst zwei bis drei sachliche Sätze auf Deutsch zu einer Auswertung "
    "der Luftqualität. Nenne KEINE Messzahlen — die stehen in der Tabelle daneben. "
    "Ordne qualitativ ein: welche Stadt am stärksten belastet ist und welcher "
    "Schadstoff das Bild bestimmt. Kein Markdown, keine Aufzählung, keine "
    "Gesundheitsempfehlung."
)


def kommentieren(zeilen: list[dict], kennzahlen: dict) -> dict:
    """Kurze Einordnung des Ergebnisses, ohne jede Zahl.

    Zahlen im Text gelten hier immer als Verstoß - außer denen, die zu einem
    Namen gehören (PM10, PM2.5, NO₂, O₃, SO₂). Dadurch ist die Prüfung eine
    einfache Ja/Nein-Frage statt eines Abgleichs mit den Daten.
    """
    gueltig = [z for z in zeilen if z["ok"]]
    if not gueltig:
        return {"text": "", "protokoll": ["Keine Daten — kein Kommentar."], "quelle": "keiner"}

    erlaubt = {"10", "2.5", "2", "3", "5"} | {str(n) for n in range(0, 13)}

    auftrag = (
        "Auswertung:\n"
        + "\n".join(
            f"- {z['name']}: Stufe '{z['stufe']}', ausschlaggebend {z['treiber']}"
            for z in gueltig
        )
        + f"\n\nAm stärksten belastet: {gueltig[0]['name']}."
        + (
            "\nÜber einem EU-Grenzwert: "
            + "; ".join(f"{e['stadt']} ({', '.join(e['schadstoffe'])})" for e in kennzahlen["ueber_eu"])
            if kennzahlen.get("ueber_eu") else "\nKeine Stadt über einem EU-Grenzwert."
        )
    )

    notfall = (
        f"Am stärksten belastet ist {gueltig[0]['name']}, ausschlaggebend ist dort "
        f"{gueltig[0]['treiber']}. "
        + ("Keine der Städte liegt über einem EU-Grenzwert."
           if not kennzahlen.get("ueber_eu") else
           "Mindestens eine Stadt liegt über einem EU-Grenzwert.")
    )

    verlauf = [{"role": "system", "content": KOMMENTAR_SYSTEM}, {"role": "user", "content": auftrag}]
    protokoll: list[str] = []

    for _ in range(MAX_VERSUCHE):
        try:
            text = llm.chat(verlauf, temperature=0.3, max_tokens=250).get("content", "").strip()
        except Exception as fehler:
            protokoll.append(f"Modell nicht erreichbar ({type(fehler).__name__}).")
            return {"text": notfall, "protokoll": protokoll, "quelle": "harness"}

        text = re.sub(r"^#+ .*$", "", text, flags=re.MULTILINE).strip()
        verstoesse = sorted({z.replace(",", ".") for z in ZAHL.findall(text)} - erlaubt)
        if not verstoesse:
            return {"text": text, "protokoll": protokoll, "quelle": "modell"}

        protokoll.append(f"Zahlen im Kommentar verworfen: {', '.join(verstoesse)}.")
        verlauf += [
            {"role": "assistant", "content": text},
            {"role": "user", "content":
                "Der Kommentar darf keine Messzahlen enthalten. Diese müssen raus: "
                + ", ".join(verstoesse) + ". Schreibe ihn neu."},
        ]

    protokoll.append("Kein zahlenfreier Kommentar zustande gekommen — Harness-Text eingesetzt.")
    return {"text": notfall, "protokoll": protokoll, "quelle": "harness"}
