// Erfassung Wohnen und Eigentum (Übergabe v0.4.2, W4): geschlossener Kreis, nicht öffentlich verlinkt.
// Zweck: Für die Stadt gibt es keinen Mietspiegel. Eine Vergleichsgrundlage für tatsächlich gezahlte Mieten braucht
// Mietangaben von Mietenden und das Wissen, wer welche Gebäude vermietet. Beides wird getrennt erfasst (Formular A:
// Eigentum und Vermietung, durch das Team; Formular B: Mietangabe, freiwillig mit Einwilligung) und getrennt exportiert.
// Datenschutz: Jeder Eintrag wird beim Speichern mit dem öffentlichen Schlüssel der Prüfgruppe versiegelt (libsodium
// sealed box) und nur so in IndexedDB abgelegt; das Gerät kann ihn danach nicht mehr lesen. Namen von Privatpersonen
// werden zusätzlich für sich versiegelt. Kein Upload: Einträge verlassen das Gerät nur als Exportdatei.
// Unverschlüsselt bleiben je Eintrag nur Kennung, Art, Zeitpunkt und bei Formular A die Gebäudekennung (für die Markierung
// „erfasst“ auf der Karte). Sensible Felder sind per Konfiguration abschaltbar (privat_namen_aktiv, mietangaben_aktiv).
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const json = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const zahl = (v, d = 0) => Number(v).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
  const datum = (iso) => new Date(iso).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
  const SCHMAL = matchMedia("(max-width: 700px)");
  const ALG = "libsodium-sealedbox-x25519";

  // --- Ablage im Gerät (IndexedDB): eintraege (versiegelt), meta (Zugang) ------------------------------------
  let dbVersprechen = null;
  function db() {
    return (dbVersprechen ||= new Promise((ok, fehler) => {
      const r = indexedDB.open("wiz-erfassung", 1);
      r.onupgradeneeded = () => {
        r.result.createObjectStore("eintraege", { keyPath: "id" });
        r.result.createObjectStore("meta", { keyPath: "key" });
      };
      r.onsuccess = () => ok(r.result);
      r.onerror = () => fehler(r.error);
    }));
  }
  async function ablage(store, mode, fn) {
    const t = (await db()).transaction(store, mode);
    const r = fn(t.objectStore(store));
    return new Promise((ok, fehler) => {
      t.oncomplete = () => ok(r && "result" in r ? r.result : undefined);
      t.onerror = () => fehler(t.error);
    });
  }
  const alle = () => ablage("eintraege", "readonly", (s) => s.getAll());
  const ablegen = (store, x) => ablage(store, "readwrite", (s) => s.put(x));
  const loeschen = (store, id) => ablage(store, "readwrite", (s) => s.delete(id));
  const meta = (key) => ablage("meta", "readonly", (s) => s.get(key));

  // --- Einladungscode (wie tools/einladung.py) ----------------------------------------------------------------
  const ZEICHEN = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  const normieren = (c) => c.toUpperCase().replace(/[\s-]/g, "").replace(/O/g, "0").replace(/[IL]/g, "1");
  async function sha256(text) {
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  // --- Versiegeln mit dem öffentlichen Schlüssel der Prüfgruppe ------------------------------------------------
  let sodium = null;
  async function versiegeln(text, schl) {
    sodium ||= await window.sodium.ready.then(() => window.sodium);
    const V = sodium.base64_variants.ORIGINAL;
    return sodium.to_base64(sodium.crypto_box_seal(sodium.from_string(text), sodium.from_base64(schl.public_key, V)), V);
  }

  const BELEGE = { eigentuemer_website: "Website der Eigentümerin", handelsregister: "Handelsregister", beteiligungsbericht: "Beteiligungsbericht",
    bekanntmachung_stadt: "Bekanntmachung der Stadt", bauschild: "Bauschild", presse: "Presse",
    eigener_grundbuchauszug: "Eigener Grundbuchauszug (nur für ein eigenes Grundstück)", ortskenntnis: "Ortskenntnis" };
  const VERMIETET = { ja: "ja", teilweise: "teilweise", nein: "nein", unbekannt: "unbekannt" };
  const SICHERHEIT = { gesichert: "gesichert", wahrscheinlich: "wahrscheinlich", unklar: "unklar" };
  const AUSSTATTUNG = { balkon: "Balkon", einbaukueche: "Einbauküche", aufzug: "Aufzug", zentralheizung: "Zentralheizung", neubaustandard: "Neubaustandard" };
  const FLAECHE = [[40, "<40", "unter 40 m²"], [60, "40-59", "40 bis 59 m²"], [80, "60-79", "60 bis 79 m²"], [100, "80-99", "80 bis 99 m²"],
    [120, "100-119", "100 bis 119 m²"], [Infinity, ">=120", "120 m² und mehr"]];
  const BAUJAHR = { "<1919": "vor 1919", "1919-1948": "1919 bis 1948", "1949-1978": "1949 bis 1978", "1979-1990": "1979 bis 1990",
    "1991-2010": "1991 bis 2010", ">2010": "nach 2010", unbekannt: "unbekannt" };
  const auswahl = (name, werte, gewaehlt, typ = "radio") => Object.entries(werte).map(([v, t]) =>
    `<label class="wahlknopf"><input type="${typ}" name="${name}" value="${esc(v)}"${v === gewaehlt ? " checked" : ""}> <span>${esc(t)}</span></label>`).join("");

  async function start() {
    const [cfg, index, sEig, sMiete] = await Promise.all([json("stadt.json"), json("data/export/karte/gebaeude_index.json"),
      json("schemas/erfassung_eigentum.json"), json("schemas/mietangabe.json")]);
    const E = cfg.wohnen_eigentum, F = E.erfassung, G = cfg.gebaeude;
    const tafel = $("#tafel"), inhalt = $("#tafel-inhalt");
    const titel = (t) => { $("#tafel-titel").textContent = t; };
    const fokus = () => $("#tafel-titel").focus();

    if ("serviceWorker" in navigator) navigator.serviceWorker.register("erfassen-sw.js", { scope: "./erfassen" }).catch(() => {});
    const netz = () => { $("#netz").textContent = navigator.onLine ? "" : "Offline: Erfassen und Speichern funktionieren; die Hintergrundkarte fehlt."; };
    addEventListener("online", netz); addEventListener("offline", netz); netz();

    // Datenschutzhinweis
    const D = F.datenschutz;
    $("#datenschutz-inhalt").innerHTML = `<p class="meta">${esc(D.status)}</p><ul>${D.punkte.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>
      <dl class="fakten"><dt>Verantwortlich</dt><dd>${esc(D.verantwortlich || "noch nicht benannt").replace(/\n/g, "<br>")}</dd>
      <dt>Widerspruch und Löschung</dt><dd>${esc(D.kontakt_widerspruch || "noch nicht benannt").replace(/\n/g, "<br>")}</dd></dl>`;
    const dlg = $("#datenschutz");
    $("#knopf-datenschutz").addEventListener("click", () => dlg.showModal());
    dlg.querySelector("button").addEventListener("click", (e) => { e.preventDefault(); dlg.close(); });

    // Zugang über Einladungscode: Einträge {hash, bis} (früher nur der Hash). Widerrufene Codes (Eintrag entfernt) und
    // abgelaufene (bis vor heute) sperren die App beim nächsten Start mit aktueller Konfiguration.
    const heute = new Date().toISOString().slice(0, 10);
    const einladung = (hash) => F.einladungen.map((x) => (typeof x === "string" ? { hash: x } : x)).find((x) => x.hash === hash);
    const abgelaufen = (e) => Boolean(e && e.bis && e.bis < heute);
    // Probemodus: Formulare und Prüfungen wie echt, ohne Code; nichts wird gespeichert oder exportiert
    let probe = false;
    let zugang = await meta("zugang");
    const ez = zugang && einladung(zugang.hash);
    if (zugang && (!ez || abgelaufen(ez))) {
      await loeschen("meta", "zugang");
      zugang = null;
      zugangFormular(ez ? "Dieser Zugang ist abgelaufen. Bitte einen neuen Einladungscode eingeben." : "Dieser Zugang wurde widerrufen. Bitte einen neuen Einladungscode eingeben.");
    } else if (!zugang) zugangFormular();
    else hauptteil();

    function zugangFormular(meldung = "") {
      titel("Zugang");
      inhalt.innerHTML = `<p>Die Erfassung ist nur für das Team und eingeladene Personen. Bitte den Einladungscode eingeben.</p>
        ${meldung ? `<p class="fehler" role="alert">${esc(meldung)}</p>` : ""}
        <form id="zugang" novalidate><label class="feld">Einladungscode <input id="code" autocomplete="off" autocapitalize="characters" spellcheck="false"
          placeholder="XXXX-XXXX-XXXX-XXXX" required aria-describedby="code-hinweis"></label>
          <p id="code-hinweis" class="meta">Aus dem Code entsteht eine pseudonyme Erfasser-ID; ein Name wird nicht gespeichert.</p>
          <p id="code-fehler" class="fehler" role="alert" hidden></p>
          <button class="knopf" type="submit">Freischalten</button></form>
        <p><button type="button" class="link-btn" id="probe">Ohne Code ausprobieren</button></p>
        <p class="meta">Probe: Formulare und Prüfungen wie echt; nichts wird gespeichert oder exportiert.</p>`;
      $("#probe").addEventListener("click", () => {
        probe = true;
        zugang = { erfasser: "Probe" };
        $("#probe-band").hidden = false;
        document.body.classList.add("probe");
        hauptteil();
      });
      $("#zugang").addEventListener("submit", async (e) => {
        e.preventDefault();
        const c = normieren($("#code").value);
        const fehler = (t) => { const p = $("#code-fehler"); p.textContent = t; p.hidden = false; $("#code").setAttribute("aria-invalid", "true"); $("#code").focus(); };
        if (c.length !== 16 || [...c].some((z) => !ZEICHEN.includes(z))) return fehler("Der Code hat 16 Zeichen (Ziffern und Buchstaben).");
        const hash = await sha256(`wiz-einladung:${c}`);
        const e2 = einladung(hash);
        if (!e2) return fehler("Dieser Code ist nicht (mehr) gültig.");
        if (abgelaufen(e2)) return fehler(`Dieser Code ist abgelaufen (gültig bis ${e2.bis.split("-").reverse().join(".")}).`);
        zugang = { key: "zugang", hash, erfasser: `E-${(await sha256(`wiz-erfasser:${c}`)).slice(0, 8)}`, seit: new Date().toISOString() };
        await ablegen("meta", zugang);
        hauptteil();
      });
    }

    async function hauptteil() {
      $("#ortsteil-wahl").hidden = false;
      $("#knopf-eintraege").hidden = probe;
      const vorhanden = (index && index.ortsteile) || {};
      const sel = $("#ortsteil");
      sel.innerHTML = `<option value="">ganze Stadt</option>` + cfg.ortsteile.filter((o) => vorhanden[o.slug]).map((o) => `<option value="${esc(o.slug)}">${esc(o.name)}</option>`).join("");
      let gewaehlt = null;

      maplibregl.setWorkerUrl("vendor/maplibre/maplibre-gl-csp-worker.js");
      const protokoll = new pmtiles.Protocol();
      maplibregl.addProtocol("pmtiles", protokoll.tile);
      const kacheln = new URL("data/export/karte/gebaeude.pmtiles", location.href).href;
      const map = new maplibregl.Map({
        container: "karte", center: [cfg.karte.zentrum[1], cfg.karte.zentrum[0]], zoom: 14,
        style: { version: 8, sources: {
          basis: { type: "raster", tiles: [cfg.karte.hintergrund.grau], tileSize: 256, maxzoom: cfg.karte.hintergrund.max_zoom, attribution: cfg.karte.hintergrund.attribution },
          gebaeude: { type: "vector", url: `pmtiles://${kacheln}`, attribution: esc(G.attribution) } },
        layers: [
          { id: "hintergrund", type: "background", paint: { "background-color": "#f2f2f2" } },
          { id: "basis", type: "raster", source: "basis", paint: { "raster-saturation": -1, "raster-opacity": 0.9 } },
          { id: "flaeche", type: "fill", source: "gebaeude", "source-layer": "gebaeude", paint: { "fill-color": "#857a70", "fill-opacity": 0.7 } },
          { id: "erfasst", type: "fill", source: "gebaeude", "source-layer": "gebaeude", filter: ["in", ["get", "id"], ["literal", []]],
            paint: { "fill-color": "#2c7652", "fill-opacity": 0.9 } },
          { id: "umriss", type: "line", source: "gebaeude", "source-layer": "gebaeude", minzoom: 15, paint: { "line-color": "#1a1a1a", "line-width": 0.4, "line-opacity": 0.5 } },
          { id: "auswahl", type: "line", source: "gebaeude", "source-layer": "gebaeude", filter: ["==", ["get", "id"], ""], paint: { "line-color": "#b8352e", "line-width": 3 } },
        ] },
        attributionControl: { compact: true },
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      window.stadtmonitorErfassen = { map };  // für Prüfungen im Browser

      async function markieren() {
        const liste = await alle();
        $("#anzahl").textContent = zahl(liste.filter((x) => !x.exportiert).length);
        const ids = [...new Set(liste.filter((x) => x.typ === "eigentum").map((x) => x.gebaeude_id))];
        if (map.getLayer("erfasst")) map.setFilter("erfasst", ["in", ["get", "id"], ["literal", ids]]);
        return liste;
      }
      function gebiet() {
        const b = sel.value ? vorhanden[sel.value].kern : cfg.karte.bbox;
        map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: SCHMAL.matches ? { top: 150, bottom: 260, left: 20, right: 20 } : { top: 90, bottom: 40, left: 40, right: 460 },
          duration: 0, maxZoom: 17 });
      }
      // Gespeichert wird erst mit Schlüssel und benannter verantwortlicher Stelle: Einwilligung (Art. 13) und Information
      // der Eigentümer:innen (Art. 14 DSGVO) müssen sie nennen. Die Probe speichert nie.
      const stelle = Boolean(F.datenschutz.verantwortlich);
      const mieteAn = probe || E.mietangaben_aktiv;
      const speichernA = probe || (Boolean(F.schluessel) && stelle);
      const speichernB = speichernA;
      const ohneSchluessel = () => (probe ? `<p class="hinweis-kasten" role="note"><strong>Probe.</strong> Nichts wird gespeichert oder exportiert.</p>`
        : !F.schluessel ? `<p class="hinweis-kasten" role="note"><strong>Speichern noch nicht möglich.</strong>
        Der öffentliche Schlüssel der Prüfgruppe ist noch nicht hinterlegt; ohne ihn bleibt nichts im Gerät.</p>`
        : !stelle ? `<p class="hinweis-kasten" role="note"><strong>Speichern noch nicht möglich.</strong>
        Die verantwortliche Stelle ist noch nicht benannt; Einwilligung und Datenschutzhinweis müssen sie nennen.</p>` : "");

      async function uebersicht() {
        gewaehlt = null;
        map.setFilter("auswahl", ["==", ["get", "id"], ""]);
        titel("Gebäude antippen");
        inhalt.innerHTML = `${ohneSchluessel()}<p>Ein Gebäude auf der Karte antippen, dann Eigentum und Vermietung oder eine Mietangabe erfassen.
          Grün: im Gerät schon erfasst.</p><p class="meta">Erfasser-ID ${esc(zugang.erfasser)} · <span id="offline-stand">Offline-Stand wird geprüft</span></p>`;
        const offline = "caches" in window && await caches.match(kacheln).catch(() => null);
        const el = $("#offline-stand");
        if (el) el.textContent = offline ? "Gebäude offline verfügbar" : "Gebäude noch nicht offline gespeichert";
      }
      function gebaeudeKopf(p) {
        const ot = cfg.ortsteile.find((o) => o.slug === p.o);
        return `<dl class="fakten"><dt>Funktion</dt><dd>${esc(p.f || "nicht angegeben")}</dd>${ot ? `<dt>Ortsteil</dt><dd>${esc(ot.name)}</dd>` : ""}
          <dt>Kennung</dt><dd><code>${esc(p.id)}</code></dd></dl>`;
      }
      function gebaeude(p) {
        gewaehlt = p;
        map.setFilter("auswahl", ["==", ["get", "id"], p.id]);
        titel("Gebäude");
        inhalt.innerHTML = `${gebaeudeKopf(p)}${ohneSchluessel()}
          <p class="knoepfe"><button type="button" class="knopf" id="zu-a">Eigentum und Vermietung erfassen</button>
          <button type="button" class="knopf" id="zu-b"${mieteAn ? "" : " disabled aria-describedby=\"b-aus\""}>Mietangabe erfassen</button></p>
          ${mieteAn ? "" : '<p id="b-aus" class="meta">Mietangaben sind noch nicht freigegeben (Datenschutzfragen offen).</p>'}
          <button type="button" class="link-btn" id="zurueck">Zurück zur Übersicht</button>`;
        $("#zu-a").addEventListener("click", () => formularA(p));
        if (mieteAn) $("#zu-b").addEventListener("click", () => formularB(p));
        $("#zurueck").addEventListener("click", () => { uebersicht(); fokus(); });
        if (SCHMAL.matches) tafel.scrollTop = 0;
        fokus();
      }

      // Fehler anzeigen: Liste oben mit Sprungmarken, Felder als ungültig markiert
      function fehlerZeigen(form, fehler) {
        form.querySelectorAll("[aria-invalid]").forEach((x) => x.removeAttribute("aria-invalid"));
        const box = $(".fehlerliste", form);
        if (!fehler.length) { box.hidden = true; return false; }
        box.hidden = false;
        box.innerHTML = `<p><strong>Bitte prüfen:</strong></p><ul>${fehler.map((f) => `<li>${esc(f.feld)}: ${esc(f.text)}</li>`).join("")}</ul>`;
        for (const f of fehler) { const el = form.elements[f.name]; const x = el && (el.length && !el.tagName ? el[0] : el); if (x && x.setAttribute) x.setAttribute("aria-invalid", "true"); }
        box.focus();
        return true;
      }
      const FELDNAMEN = { kategorie: "Eigentum", vermietet: "Vermietet", beleg_art: "Beleg", beleg_url: "Beleg-Adresse", sicherheit: "Sicherheit",
        name_juristische_person: "Name", lage_hinweis: "Lage", bemerkung: "Bemerkung", nettokalt_eur: "Nettokaltmiete", wohnflaeche_klasse: "Wohnfläche",
        wohnflaeche_m2: "Wohnfläche in m²", baujahr_klasse: "Baujahr", vertragsbeginn_jahr: "Vertragsbeginn", letzte_erhoehung_jahr: "Letzte Erhöhung",
        einwilligung: "Einwilligung", erfassungsweg: "Erfassungsweg", vermieter_schluessel: "Vermieter" };
      const schemaFehler = (s, rec) => ErfassenPruefung.schema(s, rec).map((f) => {
        const name = f.pfad.split(/[.[]/)[0] === "objekt" ? f.pfad.split(".")[1] : f.pfad.split(/[.[]/)[0];
        return { name, feld: FELDNAMEN[name] || name, text: f.text };
      });

      async function speichern(typ, rec, gebaeudeId) {
        if (probe) return;
        const schl = F.schluessel;
        const eintrag = { id: rec.erfassung_id || rec.angabe_id, typ, erstellt: rec.erfasst_am, exportiert: null, alg: ALG, key_id: schl.key_id,
          ciphertext: await versiegeln(JSON.stringify(rec), schl) };
        if (typ === "eigentum") eintrag.gebaeude_id = gebaeudeId;
        await ablegen("eintraege", eintrag);
        await markieren();
      }
      function gespeichert(text, code = null) {
        titel("Gespeichert");
        inhalt.innerHTML = `${probe ? `<p class="erfolg" role="status">Probe: Die Angaben sind gültig. Nichts wurde gespeichert.</p>`
          : `<p class="erfolg" role="status">${esc(text)} Der Eintrag ist verschlüsselt im Gerät; lesen kann ihn nur die Prüfgruppe.</p>`}
          ${code && !probe ? `<div class="widerruf"><p>Widerrufscode für diese Angabe:</p><p class="code" id="widerrufscode">${esc(code)}</p>
            <p class="meta">Bitte notieren oder fotografieren. Mit diesem Code lässt sich die Angabe jederzeit löschen lassen; die App zeigt ihn nur jetzt.</p></div>` : ""}
          <p class="knoepfe"><button type="button" class="knopf" id="weiter">Nächstes Gebäude</button>
          ${probe ? "" : '<button type="button" class="knopf" id="zu-eintraege">Einträge und Export</button>'}</p>`;
        $("#weiter").addEventListener("click", () => { uebersicht(); fokus(); });
        if (!probe) $("#zu-eintraege").addEventListener("click", eintraege);
        fokus();
      }

      // --- Formular A: Eigentum und Vermietung ---------------------------------------------------------------
      function formularA(p) {
        titel("Eigentum und Vermietung");
        const kat = E.kategorien.map((k) => [k.code, k.titel]);
        inhalt.innerHTML = `${gebaeudeKopf(p)}<form id="form-a" novalidate>
          <div class="fehlerliste" tabindex="-1" role="alert" hidden></div>
          <fieldset class="kacheln"><legend>Wem gehört das Gebäude?</legend>${auswahl("kategorie", Object.fromEntries(kat), null)}</fieldset>
          <p class="meta">GbR und Einzelkaufleute gelten als Privatpersonen.</p>
          <div id="feld-jp" hidden><label class="feld">Name (Unternehmen, Genossenschaft, öffentliche Hand, Kirche)
            <input name="name_juristische_person" maxlength="120" autocomplete="off"></label></div>
          <div id="feld-privat" hidden>${E.privat_namen_aktiv
            ? `<label class="feld">Name der Privatperson <span class="meta">(wird sofort verschlüsselt, nicht veröffentlicht)</span>
                <input name="name_privat" autocomplete="off" spellcheck="false"></label>
                <p class="meta">Nur zur Prüfung und zum Erkennen von Dubletten. Keine Namen aus Grundbuchauszügen Dritter, keine Klingelschilder.</p>`
            : `<p class="hinweis-kasten">Namen von Privatpersonen werden noch nicht erfasst (nicht freigegeben). Die Kategorie genügt.</p>`}</div>
          <fieldset class="kacheln klein"><legend>Werden Wohnungen vermietet?</legend>${auswahl("vermietet", VERMIETET, "unbekannt")}</fieldset>
          <label class="feld">Beleg <select name="beleg_art"><option value="">bitte wählen</option>${Object.entries(BELEGE).map(([v, t]) => `<option value="${v}">${esc(t)}</option>`).join("")}</select></label>
          <label class="feld">Adresse des Belegs <span class="meta">(optional)</span> <input name="beleg_url" type="url" inputmode="url" placeholder="https://…"></label>
          <fieldset class="kacheln klein"><legend>Wie sicher ist die Angabe?</legend>${auswahl("sicherheit", SICHERHEIT, "wahrscheinlich")}</fieldset>
          <label class="feld">Lage <span class="meta">(optional; Straße ohne Hausnummer oder Bezeichnung)</span> <input name="lage_hinweis" maxlength="80" autocomplete="off"></label>
          <label class="feld">Bemerkung <span class="meta">(optional; keine Namen, keine Kontaktdaten, keine Hausnummern)</span>
            <textarea name="bemerkung" maxlength="200" rows="3"></textarea></label>
          <p class="knoepfe"><button class="knopf" type="submit"${speichernA ? "" : " disabled"}>${probe ? "Prüfen (Probe)" : "Verschlüsselt speichern"}</button>
            <button class="link-btn" type="button" id="abbrechen">Abbrechen</button></p></form>`;
        const form = $("#form-a");
        form.addEventListener("change", () => {
          const k = (form.elements.kategorie.value || "");
          $("#feld-jp").hidden = !k || k === "privat" || k === "unklar";
          $("#feld-privat").hidden = k !== "privat";
        });
        $("#abbrechen").addEventListener("click", () => gebaeude(p));
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const w = (n) => (form.elements[n] ? String(form.elements[n].value || "").trim() : "");
          const k = w("kategorie"), jp = k && k !== "privat" && k !== "unklar";
          const rec = { erfassung_id: crypto.randomUUID(), objekt: { typ: "gebaeude", id: p.id }, kategorie: k || undefined, beleg_art: w("beleg_art") || undefined,
            sicherheit: w("sicherheit"), vermietet: w("vermietet"), erfasst_am: new Date().toISOString(), erfasser: zugang.erfasser, app_version: F.app_version };
          const ot = cfg.ortsteile.find((o) => o.slug === p.o);
          if (ot) rec.objekt.gemarkung = ot.gemarkung;
          if (w("lage_hinweis")) rec.objekt.lage_hinweis = w("lage_hinweis");
          if (w("beleg_url")) rec.beleg_url = w("beleg_url");
          if (w("bemerkung")) rec.bemerkung = w("bemerkung");
          const name = w("name_juristische_person").replace(/\s+/g, " ");
          if (jp && name) { rec.name_juristische_person = name; rec.vermieter_schluessel = `JP:${name}`; }
          if (k === "privat") rec.vermieter_schluessel = "V-neu";
          Object.keys(rec).forEach((x) => rec[x] === undefined && delete rec[x]);
          const fehler = schemaFehler(sEig, rec);
          for (const [n, ohneZiffern] of [["lage_hinweis", true], ["bemerkung", false]]) {
            const t = ErfassenPruefung.freitext(w(n), { ohneZiffern });
            if (t) fehler.push({ name: n, feld: FELDNAMEN[n], text: t });
          }
          if (fehlerZeigen(form, fehler)) return;
          if (k === "privat" && E.privat_namen_aktiv && w("name_privat") && !probe) {
            rec.name_privat_enc = { alg: ALG, key_id: F.schluessel.key_id, ciphertext: await versiegeln(w("name_privat"), F.schluessel) };
            form.elements.name_privat.value = "";
          }
          await speichern("eigentum", rec, p.id);
          gespeichert("Eigentum und Vermietung gespeichert.");
        });
        fokus();
      }

      // --- Formular B: Mietangabe (freiwillig, mit Einwilligung) -----------------------------------------------
      function formularB(p) {
        titel("Mietangabe");
        const W = F.einwilligung;
        // Stelle und Kontakt aus stadt.json in den versionierten Text; ohne Stelle speichert die App ohnehin nicht
        const stelleName = (F.datenschutz.verantwortlich || "").split("\n")[0] || "die verantwortliche Stelle (noch nicht benannt)";
        const wText = W.text.replace("{stelle}", stelleName).replace("{kontakt}", F.datenschutz.kontakt_widerspruch || "der Kontaktadresse im Datenschutzhinweis");
        inhalt.innerHTML = `${gebaeudeKopf(p)}<form id="form-b" novalidate>
          <div class="fehlerliste" tabindex="-1" role="alert" hidden></div>
          <fieldset class="einwilligung"><legend>Einwilligung</legend><p>${esc(wText)}</p>
            <p class="meta">Fassung ${esc(W.version)} · ${esc(W.status)} · <button type="button" class="link-btn" id="zu-datenschutz">Datenschutzhinweis öffnen</button></p>
            <label class="wahlknopf"><input type="checkbox" name="einwilligung" value="ja"> <span>Ich willige ein.</span></label></fieldset>
          <fieldset class="kacheln klein"><legend>Wer füllt aus?</legend>${auswahl("erfassungsweg", { selbst: "Mieter:in selbst", im_gespraech_mit_team: "im Gespräch mit dem Team" }, "selbst")}</fieldset>
          <p class="meta">Keine Wohnungsnummer, kein Stockwerk, keine Namen von Mietenden.</p>
          <label class="feld">Nettokaltmiete im Monat (€) <input name="nettokalt_eur" type="number" inputmode="decimal" min="50" max="5000" step="0.01" required></label>
          <label class="feld">Wohnfläche in m² <span class="meta">(nur für den Preis je m²; danach gelöscht)</span>
            <input name="wohnflaeche_m2" type="number" inputmode="decimal" min="10" max="400" step="0.1" required></label>
          <label class="feld">Wohnfläche <select name="wohnflaeche_klasse" required><option value="">bitte wählen</option>
            ${FLAECHE.map(([, v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("")}</select></label>
          <p class="meta" id="je-m2" aria-live="polite"></p>
          <label class="feld">Baujahr des Gebäudes <select name="baujahr_klasse">${Object.entries(BAUJAHR).map(([v, t]) => `<option value="${esc(v)}"${v === "unbekannt" ? " selected" : ""}>${esc(t)}</option>`).join("")}</select></label>
          <label class="feld">Jahr des Vertragsbeginns <input name="vertragsbeginn_jahr" type="number" inputmode="numeric" min="1950" max="2030" required></label>
          <label class="feld">Jahr der letzten Erhöhung <span class="meta">(optional)</span> <input name="letzte_erhoehung_jahr" type="number" inputmode="numeric" min="1950" max="2030"></label>
          <fieldset class="kacheln klein"><legend>Ausstattung <span class="meta">(optional)</span></legend>${auswahl("ausstattung", AUSSTATTUNG, null, "checkbox")}</fieldset>
          <label class="feld">Vermieter <span class="meta">(optional; nur Unternehmen, Genossenschaft oder öffentliche Hand, keine Privatpersonen)</span>
            <input name="vermieter_jp" maxlength="120" autocomplete="off"></label>
          ${speichernB ? "" : ohneSchluessel()}
          <p class="knoepfe"><button class="knopf" type="submit"${speichernB ? "" : " disabled"}>${probe ? "Prüfen (Probe)" : "Verschlüsselt speichern"}</button>
            <button class="link-btn" type="button" id="abbrechen">Abbrechen</button></p></form>`;
        const form = $("#form-b");
        let zeitpunkt = null;
        $("#zu-datenschutz").addEventListener("click", () => $("#datenschutz").showModal());
        form.elements.einwilligung.addEventListener("change", (e) => { zeitpunkt = e.target.checked ? new Date().toISOString() : null; });
        form.addEventListener("input", () => {
          const m2 = parseFloat(form.elements.wohnflaeche_m2.value), eur = parseFloat(form.elements.nettokalt_eur.value);
          if (m2 >= 10) form.elements.wohnflaeche_klasse.value = FLAECHE.find(([g]) => m2 < g)[1];
          $("#je-m2").textContent = m2 >= 10 && eur > 0 ? `entspricht ${zahl(eur / m2, 2)} € je m² (zur Kontrolle)` : "";
        });
        $("#abbrechen").addEventListener("click", () => gebaeude(p));
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const w = (n) => String(form.elements[n].value || "").trim();
          const nummer = (n) => (w(n) === "" ? undefined : Number(w(n)));
          const weg = form.elements.erfassungsweg.value;
          const rec = { angabe_id: crypto.randomUUID(), gebaeude_id: p.id, nettokalt_eur: nummer("nettokalt_eur"), wohnflaeche_klasse: w("wohnflaeche_klasse") || undefined,
            wohnflaeche_m2: nummer("wohnflaeche_m2"), baujahr_klasse: w("baujahr_klasse"), vertragsbeginn_jahr: nummer("vertragsbeginn_jahr"),
            letzte_erhoehung_jahr: nummer("letzte_erhoehung_jahr"), erfasst_am: new Date().toISOString(), erfassungsweg: weg };
          const aus = [...form.querySelectorAll('input[name="ausstattung"]:checked')].map((x) => x.value);
          if (aus.length) rec.ausstattung = aus;
          if (zeitpunkt && form.elements.einwilligung.checked) rec.einwilligung = { erteilt: true, textversion: W.version, zeitpunkt };
          if (weg === "im_gespraech_mit_team") rec.erfasser = zugang.erfasser;
          const v = w("vermieter_jp").replace(/\s+/g, " ");
          if (v) rec.vermieter_schluessel = `JP:${v}`;
          Object.keys(rec).forEach((x) => rec[x] === undefined && delete rec[x]);
          const fehler = schemaFehler(sMiete, rec);
          const t = ErfassenPruefung.freitext(v);
          if (t) fehler.push({ name: "vermieter_jp", feld: "Vermieter", text: t });
          if (fehlerZeigen(form, fehler)) return;
          await speichern("miete", rec);
          form.reset();
          // Widerrufscode: die ersten 8 Zeichen der zufälligen Kennung (tools/pruefen.py loeschen --code)
          const c = rec.angabe_id.replace(/-/g, "").slice(0, 8).toUpperCase();
          gespeichert("Mietangabe gespeichert.", `${c.slice(0, 4)}-${c.slice(4)}`);
        });
        fokus();
      }

      // --- Einträge und Export -----------------------------------------------------------------------------
      async function eintraege() {
        const liste = await markieren();
        titel("Einträge und Export");
        const art = { eigentum: "Eigentum und Vermietung", miete: "Mietangaben" };
        const block = (typ) => {
          const x = liste.filter((e) => e.typ === typ), offen = x.filter((e) => !e.exportiert);
          return `<section class="exportblock"><h3>${art[typ]}</h3><p>${zahl(x.length)} im Gerät, davon ${zahl(offen.length)} noch nicht exportiert.</p>
            <p><button type="button" class="knopf" data-export="${typ}"${offen.length ? "" : " disabled"}>Exportieren (${zahl(offen.length)})</button></p></section>`;
        };
        const exportiert = liste.filter((e) => e.exportiert).length;
        inhalt.innerHTML = `<p>Export als verschlüsselte Datei je Formular; Sie geben sie selbst an die Prüfgruppe weiter. Es gibt keinen automatischen Upload.</p>
          ${block("eigentum")}${block("miete")}
          <section class="exportblock"><h3>Exportierte Einträge</h3><p>${zahl(exportiert)} exportiert. Erst löschen, wenn die Prüfgruppe die Datei erhalten hat.</p>
            <p><button type="button" class="knopf" id="loeschen"${exportiert ? "" : " disabled"}>Exportierte löschen (${zahl(exportiert)})</button></p></section>
          <p id="export-meldung" role="status"></p>
          <details class="unter"><summary>Liste im Gerät</summary><ul class="liste">${liste.sort((a, b) => b.erstellt.localeCompare(a.erstellt))
            .map((e) => `<li>${esc(art[e.typ])}, ${esc(datum(e.erstellt))} · ${e.exportiert ? `exportiert ${esc(datum(e.exportiert))}` : "nicht exportiert"} · verschlüsselt</li>`).join("") || "<li>keine</li>"}</ul></details>
          <button type="button" class="link-btn" id="zurueck">Zurück zur Karte</button>`;
        inhalt.querySelectorAll("[data-export]").forEach((b) => b.addEventListener("click", () => exportieren(b.dataset.export)));
        $("#loeschen").addEventListener("click", async () => {
          if (!confirm("Exportierte Einträge im Gerät löschen? Das geht nicht rückgängig.")) return;
          for (const e of (await alle()).filter((x) => x.exportiert)) await loeschen("eintraege", e.id);
          await eintraege();
          $("#export-meldung").textContent = "Exportierte Einträge gelöscht.";
        });
        $("#zurueck").addEventListener("click", () => { uebersicht(); fokus(); });
        fokus();
      }
      async function exportieren(typ) {
        const offen = (await alle()).filter((e) => e.typ === typ && !e.exportiert);
        if (!offen.length) return;
        const jetzt = new Date().toISOString();
        const datei = { format: "wiz-stadtmonitor-erfassung", version: 1, typ, alg: ALG, erfasser: zugang.erfasser, erstellt: jetzt, app_version: F.app_version,
          anzahl: offen.length, eintraege: offen.map((e) => ({ id: e.id, erstellt: e.erstellt, key_id: e.key_id, ciphertext: e.ciphertext })) };
        const name = `${typ === "miete" ? "mieten" : "eigentum"}_${zugang.erfasser}_${jetzt.slice(0, 10)}.bin`;
        const blob = new Blob([JSON.stringify(datei)], { type: "application/octet-stream" });
        const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: name });
        document.body.append(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 10000);
        for (const e of offen) await ablegen("eintraege", { ...e, exportiert: jetzt });
        await eintraege();
        const datei2 = new File([blob], name, { type: "application/octet-stream" });
        const teilen = navigator.canShare && navigator.canShare({ files: [datei2] });
        $("#export-meldung").innerHTML = `${esc(name)} gespeichert (${zahl(offen.length)} ${offen.length === 1 ? "Eintrag" : "Einträge"}).${teilen ? ' <button type="button" class="link-btn" id="teilen">Datei teilen</button>' : ""}`;
        if (teilen) $("#teilen").addEventListener("click", () => navigator.share({ files: [datei2], title: name }).catch(() => {}));
      }

      $("#knopf-eintraege").addEventListener("click", eintraege);
      sel.addEventListener("change", gebiet);
      map.on("load", async () => {
        gebiet();
        await markieren();
        await uebersicht();
        map.on("click", (e) => {
          const f = map.queryRenderedFeatures(e.point, { layers: ["erfasst", "flaeche"] })[0];
          if (f) gebaeude(f.properties);
        });
        for (const ebene of ["flaeche", "erfasst"]) {
          map.on("mouseenter", ebene, () => { map.getCanvas().style.cursor = "pointer"; });
          map.on("mouseleave", ebene, () => { map.getCanvas().style.cursor = ""; });
        }
      });
    }
  }
  start().catch((e) => { document.querySelector("#tafel-inhalt").textContent = `Die Erfassung konnte nicht geladen werden (${e.message}).`; });
})();
