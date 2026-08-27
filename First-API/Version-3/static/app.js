/* Oberfläche für Version-3.
 *
 * Vanilla JavaScript, kein Framework, kein Build-Schritt. Der ganze Zustand der
 * Anwendung ist EIN Objekt - derselbe Plan, den auch das Sprachmodell ausfüllt.
 * Formular und Modell schreiben in dasselbe Feld; das ist der Grund, warum man
 * jederzeit von Hand übernehmen kann.
 */

const SCHADSTOFFE = {
  pm10: "Feinstaub PM10",
  pm25: "Feinstaub PM2.5",
  no2: "Stickstoffdioxid NO₂",
  o3: "Ozon O₃",
  so2: "Schwefeldioxid SO₂",
};

const HEBEL_TEXT = {
  0: "Das Modell läuft gar nicht. Du füllst den Plan selbst aus — der schnellste und zuverlässigste Weg, wenn du weißt, was du willst.",
  1: "Das Modell schlägt einen Plan vor. Du siehst ihn, kannst ihn ändern, und nichts läuft, bevor du auf „Ausführen“ drückst. Voreinstellung.",
  2: "Das Modell schlägt vor und führt sofort aus. Praktisch zum schnellen Ausprobieren — du siehst das Ergebnis, bevor du den Plan gelesen hast.",
};

const BEISPIELE = [
  "Feinstaub in den drei größten Städten Bayerns",
  "Wo ist die Ozonbelastung am höchsten? Norddeutschland",
  "Stickstoffdioxid im Ruhrgebiet als Tabelle",
  "Vergleiche Hamburg und München, mit Einordnung",
];

/* Der gesamte Zustand: genau die Felder aus HARNESS.md. */
let plan = {
  staedte: ["hamburg", "berlin", "muenchen", "koeln", "stuttgart"],
  schadstoffe: ["pm10", "pm25", "no2", "o3", "so2"],
  sortierung: "belastung_absteigend",
  darstellung: "balken",
  // Leer lassen: Der Server bildet die Überschrift aus der Auswahl. Nur wenn das
  // Modell einen eigenen Titel liefert, steht hier einer - bis das Formular ihn
  // wieder überschreibt.
  titel: "",
  kommentar: false,
};

/* Jede Änderung am Formular macht einen Modell-Titel ungültig - die Überschrift
   soll zu dem passen, was tatsächlich angezeigt wird. */
function titelZuruecksetzen() { plan.titel = ""; }

let staedteKatalog = [];
let stufe = 1;

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/* ------------------------------------------------------------- Aufbau --- */

async function start() {
  $("hebel-text").textContent = HEBEL_TEXT[stufe];

  $("beispiele").innerHTML = BEISPIELE
    .map((b) => `<button class="chip" data-beispiel="${esc(b)}">${esc(b)}</button>`).join("");
  $("beispiele").onclick = (e) => {
    const b = e.target.closest("[data-beispiel]");
    if (b) { $("prompt").value = b.dataset.beispiel; $("prompt").focus(); }
  };

  $("schadstoffe").innerHTML = Object.entries(SCHADSTOFFE).map(([k, name]) =>
    `<label><input type="checkbox" value="${k}" ${plan.schadstoffe.includes(k) ? "checked" : ""}>
       ${esc(name)}</label>`).join("");
  $("schadstoffe").onchange = () => {
    plan.schadstoffe = [...$("schadstoffe").querySelectorAll("input:checked")].map((i) => i.value);
    titelZuruecksetzen(); planAnzeigen();
  };

  document.querySelectorAll(".hebel-stufe").forEach((b) => {
    b.onclick = () => setzeStufe(Number(b.dataset.stufe));
  });

  $("darstellung").onclick = (e) => {
    const b = e.target.closest("button[data-wert]");
    if (!b) return;
    plan.darstellung = b.dataset.wert;
    $("darstellung").querySelectorAll("button").forEach((x) => x.classList.toggle("aktiv", x === b));
    planAnzeigen();
  };

  $("sortierung").onchange = (e) => { plan.sortierung = e.target.value; planAnzeigen(); };
  $("kommentar").onchange = (e) => { plan.kommentar = e.target.checked; planAnzeigen(); };
  $("plan-knopf").onclick = planErzeugen;
  $("run-knopf").onclick = () => ausfuehren();

  $("prompt").onkeydown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") planErzeugen();
  };

  document.querySelectorAll(".reiter button").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".reiter button").forEach((x) => x.classList.toggle("aktiv", x === b));
      document.querySelectorAll(".reiter-inhalt").forEach((d) => { d.hidden = d.id !== b.dataset.reiter; });
    };
  });

  const antwort = await fetch("/api/staedte").then((r) => r.json());
  staedteKatalog = antwort.staedte || [];
  baueStaedteSuche();
  staedteAnzeigen();
  planAnzeigen();

  fetch("/api/harness").then((r) => r.json())
    .then((d) => { $("regeln-anzeige").textContent = d.text; });

  await ausAdresse();
}

/* Beispiele lassen sich verlinken:
     ?stufe=0&darstellung=karten&staedte=hamburg,koeln   -> Formularweg, läuft sofort
     ?stufe=2&prompt=Ozon%20im%20Ruhrgebiet              -> Modellweg, läuft sofort
   Praktisch für Kursunterlagen: Ein Link zeigt genau einen Zustand. */
async function ausAdresse() {
  const p = new URLSearchParams(location.search);
  if (![...p.keys()].length) return;

  if (p.has("stufe")) setzeStufe(Number(p.get("stufe")));
  if (p.has("staedte")) plan.staedte = p.get("staedte").split(",").filter(Boolean).slice(0, 8);
  if (p.has("schadstoffe")) plan.schadstoffe = p.get("schadstoffe").split(",").filter((k) => k in SCHADSTOFFE);
  if (p.has("darstellung")) plan.darstellung = p.get("darstellung");
  if (p.has("sortierung")) plan.sortierung = p.get("sortierung");
  if (p.has("kommentar")) plan.kommentar = p.get("kommentar") === "1";
  formularAusPlan();

  if (p.has("prompt")) {
    $("prompt").value = p.get("prompt");
    await planErzeugen();
  } else {
    await ausfuehren();
  }
}

function setzeStufe(neu) {
  stufe = neu;
  document.querySelectorAll(".hebel-stufe").forEach((b) => {
    const an = Number(b.dataset.stufe) === stufe;
    b.classList.toggle("aktiv", an);
    b.setAttribute("aria-checked", String(an));
  });
  $("hebel-text").textContent = HEBEL_TEXT[stufe];
  $("prompt-feld").dataset.aus = stufe === 0 ? "ja" : "nein";
  $("plan-knopf").textContent = stufe === 2 ? "Plan erzeugen und ausführen" : "Plan erzeugen";
}

/* -------------------------------------------------------- Städteauswahl -- */

function baueStaedteSuche() {
  const suche = $("staedte-suche");
  const box = $("staedte-vorschlaege");

  const zeichnen = () => {
    const q = suche.value.trim().toLowerCase();
    if (!q) { box.hidden = true; return; }
    const treffer = staedteKatalog
      .filter((s) => !plan.staedte.includes(s.slug))
      .filter((s) => s.name.toLowerCase().includes(q) || s.slug.includes(q))
      .slice(0, 8);
    box.innerHTML = treffer.length
      ? treffer.map((s) =>
          `<button class="vorschlag" data-slug="${s.slug}">
             <span>${esc(s.name)}</span><span class="land">${esc(s.land)}</span></button>`).join("")
      : `<div class="vorschlag"><span class="land">Keine Stadt gefunden</span></div>`;
    box.hidden = false;
  };

  suche.oninput = zeichnen;
  suche.onfocus = zeichnen;
  box.onclick = (e) => {
    const b = e.target.closest("[data-slug]");
    if (!b) return;
    if (plan.staedte.length >= 8) { melde("Höchstens acht Städte — siehe HARNESS.md."); return; }
    plan.staedte.push(b.dataset.slug);
    suche.value = ""; box.hidden = true;
    titelZuruecksetzen(); staedteAnzeigen(); planAnzeigen();
  };
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#staedte-suche, #staedte-vorschlaege")) box.hidden = true;
  });
}

function staedteAnzeigen() {
  const name = (slug) => (staedteKatalog.find((s) => s.slug === slug) || {}).name || slug;
  $("staedte-gewaehlt").innerHTML = plan.staedte.map((slug) =>
    `<button class="chip chip-gewaehlt" data-weg="${slug}">${esc(name(slug))}<span class="weg">×</span></button>`
  ).join("") || `<span class="hilfe">Keine Stadt gewählt.</span>`;
  $("staedte-zaehler").textContent = `${plan.staedte.length}/8`;
  $("staedte-gewaehlt").onclick = (e) => {
    const b = e.target.closest("[data-weg]");
    if (!b) return;
    plan.staedte = plan.staedte.filter((s) => s !== b.dataset.weg);
    titelZuruecksetzen(); staedteAnzeigen(); planAnzeigen();
  };
}

function planAnzeigen() {
  $("plan-anzeige").textContent = JSON.stringify(plan, null, 2);
}

function formularAusPlan() {
  $("sortierung").value = plan.sortierung;
  $("kommentar").checked = !!plan.kommentar;
  $("schadstoffe").querySelectorAll("input").forEach((i) => {
    i.checked = plan.schadstoffe.includes(i.value);
  });
  $("darstellung").querySelectorAll("button").forEach((b) => {
    b.classList.toggle("aktiv", b.dataset.wert === plan.darstellung);
  });
  staedteAnzeigen();
  planAnzeigen();
}

/* --------------------------------------------------------- Serveraufrufe - */

function melde(text, laeuft = false) {
  const s = $("status");
  s.hidden = false;
  s.textContent = text;
  s.classList.toggle("laeuft", laeuft);
}

async function planErzeugen() {
  const prompt = $("prompt").value.trim();
  if (!prompt) { melde("Schreibe zuerst eine Anfrage."); return; }

  $("plan-knopf").disabled = true;
  melde("Das Modell füllt den Plan aus …", true);
  try {
    const antwort = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    }).then((r) => r.json());

    plan = antwort.plan;
    formularAusPlan();
    korrekturenAnzeigen(antwort.protokoll, antwort);

    if (stufe === 2) {
      await ausfuehren();
    } else {
      melde("Plan steht. Prüfe ihn links und drücke „Ausführen“.");
    }
  } catch (fehler) {
    melde("Der Plan konnte nicht erzeugt werden: " + fehler.message);
  } finally {
    $("plan-knopf").disabled = false;
  }
}

async function ausfuehren() {
  if (!plan.staedte.length) { melde("Wähle mindestens eine Stadt."); return; }
  $("run-knopf").disabled = true;
  melde("Daten werden geholt …", true);
  try {
    const daten = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan }),
    }).then((r) => r.json());

    plan = daten.plan;
    formularAusPlan();
    if (daten.protokoll && daten.protokoll.length) korrekturenAnzeigen(daten.protokoll);
    ergebnisAnzeigen(daten);
  } catch (fehler) {
    melde("Abruf fehlgeschlagen: " + fehler.message);
  } finally {
    $("run-knopf").disabled = false;
  }
}

function korrekturenAnzeigen(protokoll, extra) {
  const liste = [...(protokoll || [])];
  if (extra && extra.quelle === "notfall") liste.push("Der Plan kam nicht vom Modell, sondern vom Harness.");
  if (extra && extra.versuche > 1) liste.push(`Das Modell brauchte ${extra.versuche} Versuche.`);
  $("korrektur-feld").hidden = liste.length === 0;
  $("korrekturen").innerHTML = liste.map((z) => `<li>${esc(z)}</li>`).join("");
}

/* ------------------------------------------------------------- Ansichten - */

function ergebnisAnzeigen(daten) {
  const { zeilen, kennzahlen, plan: p } = daten;
  $("status").hidden = true;

  $("titel").hidden = false;
  $("titel").textContent = p.titel;

  if (daten.kommentar && daten.kommentar.text) {
    $("kommentar-text").hidden = false;
    $("kommentar-text").innerHTML = esc(daten.kommentar.text) +
      `<span class="herkunft">${daten.kommentar.quelle === "modell"
        ? "Formuliert vom Sprachmodell, geprüft vom Harness: keine Zahlen erlaubt."
        : "Vom Harness geschrieben, weil das Modell die Zahlenregel verletzt hat."}` +
      (daten.kommentar.protokoll?.length ? " " + esc(daten.kommentar.protokoll.join(" ")) : "") +
      `</span>`;
  } else {
    $("kommentar-text").hidden = true;
  }

  const stufen = Object.entries(kennzahlen.stufen_verteilung || {})
    .map(([s, n]) => `${n}× ${s}`).join(", ");
  $("kennzahlen").innerHTML = [
    kachel(kennzahlen.anzahl, "Städte"),
    kennzahlen.hoechste ? kachel(kennzahlen.hoechste, "am stärksten belastet") : "",
    stufen ? kachel(stufen, "Einstufungen") : "",
    kachel((kennzahlen.ueber_eu || []).length, "über EU-Grenzwert"),
  ].join("");

  const ansicht = { balken: alsBalken, tabelle: alsTabelle, karten: alsKarten }[p.darstellung];
  $("darstellung-ziel").innerHTML =
    ansicht(zeilen.filter((z) => z.ok), p) +
    zeilen.filter((z) => !z.ok).map((z) =>
      `<div class="fehlzeile"><b>${esc(z.name)}</b>: ${esc(z.fehler)}</div>`).join("");

  const q = daten.attribution || {};
  $("quelle").hidden = false;
  $("quelle").innerHTML =
    `Quelle: ${esc(q.text || "Umweltbundesamt (UBA)")} · Lizenz ` +
    `<a href="${esc(q.license_url || "")}">DL-DE BY 2.0</a> · abgerufen über infranode.dev · ` +
    `Alle Zahlen von der API, in Python eingestuft — nicht vom Sprachmodell.`;

  $("rohdaten-anzeige").textContent = JSON.stringify(daten.rohdaten, null, 2);
}

const kachel = (wert, name) =>
  `<div class="kennzahl"><span class="wert">${esc(wert)}</span><span class="name">${esc(name)}</span></div>`;

const kopfzeile = (z) =>
  `<div class="stadtkopf">
     <span class="stadtname">${esc(z.name)}</span>
     <span class="marke" style="background:${z.farbe}">${esc(z.stufe)}</span>
     <span class="treiber">ausschlaggebend: ${esc(z.treiber)} · Index ${z.belastungsindex.toFixed(2)}</span>
   </div>`;

function alsBalken(zeilen) {
  return zeilen.map((z) => `
    <div class="stadtzeile">
      ${kopfzeile(z)}
      ${z.werte.map((w) => `
        <div class="balken-zeile">
          <span class="balken-name">${esc(w.name)}</span>
          <span class="balken-bahn"><span class="balken-fuell"
                style="width:${w.balken}%;background:${w.farbe}"></span></span>
          <span class="balken-wert">${w.wert}<span class="einheit"> ${esc(w.einheit)}</span></span>
        </div>`).join("")}
    </div>`).join("");
}

function alsTabelle(zeilen, p) {
  const spalten = p.schadstoffe.filter((k) =>
    zeilen.some((z) => z.werte.some((w) => w.schluessel === k)));
  return `<table>
    <thead><tr><th>Stadt</th><th>Einstufung</th>
      ${spalten.map((k) => `<th class="zahl">${esc(SCHADSTOFFE[k])}</th>`).join("")}
      <th class="zahl">Index</th></tr></thead>
    <tbody>${zeilen.map((z) => `<tr>
      <td><b>${esc(z.name)}</b></td>
      <td><span class="marke" style="background:${z.farbe}">${esc(z.stufe)}</span></td>
      ${spalten.map((k) => {
        const w = z.werte.find((x) => x.schluessel === k);
        return w ? `<td class="zahl ${w.ueber_eu ? "ueber" : ""}">${w.wert}</td>` : `<td class="zahl">–</td>`;
      }).join("")}
      <td class="zahl">${z.belastungsindex.toFixed(2)}</td></tr>`).join("")}
    </tbody></table>
    <p class="quelle">Rot bedeutet: über dem EU-Grenzwert. Der Index setzt den schlechtesten
    Einzelwert ins Verhältnis zur Obergrenze der Stufe „gut“ — 1,00 ist genau die Grenze zu „mäßig“.</p>`;
}

function alsKarten(zeilen) {
  return `<div class="karten">${zeilen.map((z) => `
    <div class="karte">
      <div class="karte-kopf" style="background:${z.farbe}">
        <div class="name">${esc(z.name)}</div>
        <div class="stufe">${esc(z.stufe)} · ${esc(z.treiber)}</div>
      </div>
      <div class="karte-rumpf">
        ${z.werte.map((w) => `<div class="karte-wert">
            <span>${esc(w.name)}</span>
            <span class="zahl" style="color:${w.farbe}">${w.wert} <small>${esc(w.einheit)}</small></span>
          </div>`).join("")}
      </div>
      <div class="karte-fuss">UBA-Station ${esc(z.station || "?")} · Index ${z.belastungsindex.toFixed(2)}</div>
    </div>`).join("")}</div>`;
}

start();
