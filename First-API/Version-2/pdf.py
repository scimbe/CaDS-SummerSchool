"""HTML -> PDF, ohne Python-Bibliothek.

Ein PDF zu erzeugen braucht keine Extra-Abhängigkeit: Jeder installierte Browser
kann drucken. Wir probieren der Reihe nach, was auf dem System vorhanden ist,
und geben im Notfall wenigstens die HTML-Datei zurück.
"""
import shutil
import subprocess
from pathlib import Path

CHROME_PFADE = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def _chrome() -> str | None:
    for pfad in CHROME_PFADE:
        if Path(pfad).exists():
            return pfad
        gefunden = shutil.which(pfad)
        if gefunden:
            return gefunden
    return None


def html_zu_pdf(html_datei: Path, pdf_datei: Path) -> tuple[bool, str]:
    """Gibt (erfolg, verwendetes_werkzeug) zurück."""
    html_datei = html_datei.resolve()
    pdf_datei = pdf_datei.resolve()

    # 1. Browser im Headless-Modus - fast immer vorhanden, beste Darstellung.
    browser = _chrome()
    if browser:
        befehl = [
            browser, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_datei}",
            html_datei.as_uri(),
        ]
        ergebnis = subprocess.run(befehl, capture_output=True, timeout=120)
        if pdf_datei.exists() and pdf_datei.stat().st_size > 1000:
            return True, Path(browser).name

    # 2. WeasyPrint, falls installiert (pip install weasyprint).
    if shutil.which("weasyprint"):
        subprocess.run(["weasyprint", str(html_datei), str(pdf_datei)], capture_output=True, timeout=120)
        if pdf_datei.exists():
            return True, "weasyprint"

    # 3. wkhtmltopdf.
    if shutil.which("wkhtmltopdf"):
        subprocess.run(["wkhtmltopdf", str(html_datei), str(pdf_datei)], capture_output=True, timeout=120)
        if pdf_datei.exists():
            return True, "wkhtmltopdf"

    # 4. macOS-Bordmittel - kann kein modernes CSS, aber erzeugt ein lesbares PDF.
    if shutil.which("cupsfilter"):
        with pdf_datei.open("wb") as ziel:
            subprocess.run(["cupsfilter", str(html_datei)], stdout=ziel, stderr=subprocess.DEVNULL, timeout=120)
        if pdf_datei.exists() and pdf_datei.stat().st_size > 1000:
            return True, "cupsfilter"

    return False, "keines"
