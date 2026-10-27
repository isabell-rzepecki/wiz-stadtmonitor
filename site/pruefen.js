// Prüfung der Erfassungen im Browser (Prüfseite, Schritt 1): Sitzung öffnen, Eingang, Prüfen, Freigeben, Verwerfen.
// Gleiche Regeln und Dateien wie tools/pruefgruppe.py (Schluessel, Arbeit) und tools/pruefen.py (einlesen, pruefen,
// freigeben, verwerfen); eine Bestandsdatei lässt sich abwechselnd hier und mit Python bearbeiten. Nichts wird gesendet
// (connect-src 'none') oder im Browser gespeichert; der entschlüsselte Bestand liegt nur im Arbeitsspeicher dieses Fensters.
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const K = JSON.parse($("#konfig").textContent || "{}");
  const ALG = "libsodium-sealedbox-x25519", FORMAT = "wiz-stadtmonitor-erfassung";
  const JP_KATEGORIEN = new Set((K.kategorien || []).filter((k) => k !== "privat" && k !== "unklar"));
  const KOPF_REGISTER = ["erfasser_id", "hash", "ausgegeben", "gueltig_bis", "widerrufen"];
  const PRUEFER = /^P-[\w-]{1,20}$/;
  let sodium = null, V = null;
  let S = null;  // Sitzung: {schl, d, pruefer, register, protokoll, protokollAlt, einlesen, geaendert}

  // --- Hilfen wie in Python ---------------------------------------------------------------------------------------
  const jetzt = () => new Date().toISOString().slice(0, 19) + "+00:00";  // pg.jetzt()
  const heute = () => new Date().toISOString().slice(0, 10);
  // name_normieren: casefold, Satzzeichen zu Leerraum, Leerraum vereinheitlicht
  const nameNormieren = (n) => n.toLowerCase().replace(/ß/g, "ss").replace(/[^\p{L}\p{N}_ ]/gu, " ").split(/\s+/).filter(Boolean).join(" ");
  // round(x, 2) wie Python: kaufmännisch auf dem exakten Binärwert, genaue Hälften zur geraden Ziffer
  function runden2(x) {
    if (Number.isInteger(x * 8) && !Number.isInteger(x * 4)) {
      const unten = Math.floor(x * 100);
      return (unten % 2 === 0 ? unten : unten + 1) / 100;
    }
    return Number(x.toFixed(2));
  }
  function speichern(name, text, typ = "application/octet-stream") {
    const url = URL.createObjectURL(new Blob([text], { type: typ }));
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function melden(el, text, art = "erfolg") { el.className = art; el.textContent = text; el.focus?.(); }
  const tsv = (kopf, zeilen) => [kopf, ...zeilen].map((z) => z.map((w) => String(w ?? "").replace(/[\t\n]/g, " ")).join("\t")).join("\n") + "\n";
  function tsvLesen(text, kopf) {
    const z = text.replace(/\r/g, "").split("\n").filter(Boolean);
    const k = (z[0] || "").split("\t");
    if (kopf && kopf.some((x) => !k.includes(x))) throw new Error(`Spalten fehlen: erwartet ${kopf.join(", ")}`);
    return z.slice(1).map((l) => Object.fromEntries(l.split("\t").map((w, i) => [k[i], w])));
  }

  // --- Schlüssel (wie pruefgruppe.Schluessel) -------------------------------------------------------------------
  function entsperren(enc, passphrase) {
    const k = sodium.crypto_pwhash(sodium.crypto_secretbox_KEYBYTES, passphrase, sodium.from_base64(enc.salt, V), enc.opslimit, enc.memlimit,
      sodium.crypto_pwhash_ALG_ARGON2ID13);
    const ct = sodium.from_base64(enc.ciphertext, V), n = sodium.crypto_secretbox_NONCEBYTES;
    try { return sodium.crypto_secretbox_open_easy(ct.slice(n), ct.slice(0, n), k); } catch { return null; } finally { sodium.memzero(k); }
  }
  function schluesselLaden(d, passphrase) {
    if (d.version !== 2 && !("secret_key" in d)) throw new Error("Keine Schlüsseldatei der Prüfgruppe.");
    const paare = new Map();
    for (const e of [d, ...(d.frueher || [])]) {
      const geheim = "secret_key" in e ? sodium.from_base64(e.secret_key, V) : entsperren(e.secret_enc, passphrase);
      if (!geheim) throw new Error("Passphrase falsch oder Schlüsseldatei beschädigt.");
      const pk = sodium.crypto_scalarmult_base(geheim);
      if (sodium.to_base64(pk, V) !== e.public_key) throw new Error("Schlüsseldatei beschädigt: öffentlicher und privater Teil passen nicht zusammen.");
      paare.set(e.key_id, { pk, sk: geheim });
    }
    const gesperrt = new Set(d.gesperrt || []);
    return {
      key_id: d.key_id, paare, gesperrt,
      kennt: (id) => paare.has(id) && !gesperrt.has(id),
      // ohne Kennung zuerst der aktuelle, dann frühere Schlüssel
      oeffnen(ctB64, id = null) {
        const ct = sodium.from_base64(ctB64.trim(), V);
        const kand = id ? [paare.get(id)] : [paare.get(d.key_id), ...[...paare].filter(([i]) => i !== d.key_id).map(([, p]) => p)];
        for (const p of kand) { try { return sodium.crypto_box_seal_open(ct, p.pk, p.sk); } catch { /* nächster */ } }
        throw new Error("mit keinem Schlüssel der Prüfgruppe zu öffnen");
      },
      versiegeln: (bytes) => sodium.to_base64(sodium.crypto_box_seal(bytes, paare.get(d.key_id).pk), V),
    };
  }

  // --- Bestand (wie pruefgruppe.Arbeit) ----------------------------------------------------------------------------
  const verlauf = (aktion, datensatz = "") => { S.d.verlauf.push({ zeit: jetzt(), pruefer: S.pruefer, aktion, datensatz }); S.geaendert = true; };
  const freigegeben = (e) => e.status === "offen" && !e.konflikt && new Set(e.freigaben).size >= 2;
  function nameOeffnen(id, zweck) {
    const enc = S.d.eintraege[id].datensatz.name_privat_enc;
    if (!enc) return null;
    S.protokoll.push([jetzt(), S.pruefer, id, zweck]);
    return sodium.to_string(S.schl.oeffnen(enc.ciphertext, S.schl.paare.has(enc.key_id) ? enc.key_id : null));
  }
  function aendern(e, feld, wert) {  // Änderung am Eintrag: bisherige Freigaben gelten nicht mehr
    if ((e[feld] ?? null) !== wert) { e[feld] = wert; e.freigaben = []; S.geaendert = true; }
  }

  // --- Einlesen (wie pruefen.einlesen) ----------------------------------------------------------------------------
  function einladungPruefen(z, erfasstAm) {
    if (!z) return "Erfasser-ID nicht im Einladungsregister";
    const tag = erfasstAm.slice(0, 10);
    if (tag < z.ausgegeben) return "vor Ausgabe des Einladungscodes erfasst";
    if (z.widerrufen && tag > z.widerrufen) return `nach Widerruf des Einladungscodes (${z.widerrufen}) erfasst`;
    if (tag > z.gueltig_bis) return `nach Ablauf des Einladungscodes (${z.gueltig_bis}) erfasst`;
    return null;
  }
  function minimieren(rec) {  // Miete und Fläche werden zum Preis je m², beide Ausgangswerte verworfen
    const r = { ...rec };
    if (r.wohnflaeche_m2) { r.eur_je_m2 = runden2(r.nettokalt_eur / r.wohnflaeche_m2); delete r.nettokalt_eur; delete r.wohnflaeche_m2; }
    return r;
  }
  function einlesen(dateien) {  // [{name, inhalt}]
    const P = window.ErfassenPruefung, zeilen = [];
    let neu = 0;
    for (const { name, inhalt } of dateien) {
      let d;
      try { d = JSON.parse(inhalt); } catch { d = null; }
      if (!d || d.format !== FORMAT || d.version !== 1 || !(d.typ in K.schemas) || d.alg !== ALG)
        throw new Error(`${name}: keine Exportdatei der Erfassung (Format, Version, Typ oder Verfahren unbekannt).`);
      for (const e of d.eintraege) {
        let grund = null, rec = null;
        if (S.schl.gesperrt.has(e.key_id)) grund = `gesperrter Schlüssel (${e.key_id})`;
        else if (!S.schl.kennt(e.key_id)) grund = `anderer Schlüssel (${e.key_id})`;
        else {
          try { rec = JSON.parse(sodium.to_string(S.schl.oeffnen(e.ciphertext, e.key_id))); } catch { grund = "nicht entschlüsselbar"; }
        }
        if (!grund) {
          const f = P.schema(K.schemas[d.typ], rec);
          if (f.length) grund = "Schema: " + f.slice(0, 3).map((x) => `${x.pfad || "–"}: ${x.text}`).join("; ");
          else if ((rec.erfassung_id || rec.angabe_id) !== e.id) grund = "Kennung passt nicht zum Eintrag";
        }
        if (!grund && d.typ === "eigentum") grund = P.freitext(rec.objekt.lage_hinweis, { ohneZiffern: true }) || P.freitext(rec.bemerkung);
        if (!grund && d.typ === "miete" && (rec.vermieter_schluessel || "").startsWith("V-")) grund = "Vermieter-Schlüssel V-… darf in Mietangaben nicht stehen";
        if (!grund && S.register) grund = einladungPruefen(S.register.get(d.erfasser), rec.erfasst_am);
        if (!grund && d.typ === "eigentum" && (S.d.sperrliste || []).includes(rec.objekt.id)) grund = "Widerspruch zu diesem Gebäude (Sperrliste)";
        if (!grund && e.id in S.d.eintraege) { zeilen.push([e.id, d.typ, "schon im Bestand", name]); continue; }
        if (grund) { zeilen.push([e.id, d.typ, `abgewiesen: ${grund}`, name]); continue; }
        if (d.typ === "miete") rec = minimieren(rec);
        S.d.eintraege[e.id] = { typ: d.typ, datensatz: rec, quelle: name, erfasser: d.erfasser ?? null, eingelesen: jetzt(), status: "offen",
          konflikt: null, freigaben: [], vermieter: null };
        verlauf("eingelesen", e.id);
        neu++;
        zeilen.push([e.id, d.typ, "aufgenommen", name]);
      }
    }
    return { neu, zeilen };
  }

  // --- Prüfen (wie pruefen.pruefen) -------------------------------------------------------------------------------
  function pruefen() {
    const E = S.d.eintraege;
    const aktiv = Object.entries(E).filter(([, e]) => e.status === "offen");
    const eig = aktiv.filter(([, e]) => e.typ === "eigentum");
    const nachZeit = (l) => [...l].sort((a, b) => (a[1].datensatz.erfasst_am < b[1].datensatz.erfasst_am ? -1 : a[1].datensatz.erfasst_am > b[1].datensatz.erfasst_am ? 1 : 0));
    // 1. Vermieter-Schlüssel: juristische Personen über den normierten Namen, Privatpersonen über den (entschlüsselten) Namen
    const jpNamen = new Map();
    for (const [, e] of nachZeit(eig)) {
      const r = e.datensatz;
      if (JP_KATEGORIEN.has(r.kategorie) && r.name_juristische_person) {
        const n = nameNormieren(r.name_juristische_person);
        if (!jpNamen.has(n)) jpNamen.set(n, `JP:${r.name_juristische_person.split(/\s+/).filter(Boolean).join(" ")}`);
        aendern(e, "vermieter", jpNamen.get(n));
      } else if (r.kategorie !== "privat") aendern(e, "vermieter", null);
    }
    const bekannt = new Map();
    for (const [i, e] of eig) {
      if (e.datensatz.kategorie === "privat" && (e.vermieter || "").startsWith("V-") && e.datensatz.name_privat_enc) {
        const n = nameNormieren(nameOeffnen(i, "Abgleich Vermieter-Schlüssel"));
        if (!bekannt.has(n)) bekannt.set(n, e.vermieter);
      }
    }
    for (const [i, e] of nachZeit(eig)) {
      if (e.datensatz.kategorie !== "privat" || (e.vermieter || "").startsWith("V-")) continue;
      const name = nameOeffnen(i, "Abgleich Vermieter-Schlüssel");
      const n = name ? nameNormieren(name) : null;
      if (n && bekannt.has(n)) aendern(e, "vermieter", bekannt.get(n));
      else {
        aendern(e, "vermieter", `V-${String(S.d.vermieter_naechste).padStart(3, "0")}`);
        S.d.vermieter_naechste += 1;
        if (n) bekannt.set(n, e.vermieter);
      }
    }
    // 2. Eigentum je Gebäude: gleiche Angaben = Dublette (ältere verworfen), abweichende = Konflikt
    const jeGeb = new Map();
    for (const [i, e] of eig) { const g = e.datensatz.objekt.id; if (!jeGeb.has(g)) jeGeb.set(g, []); jeGeb.get(g).push(i); }
    for (const ids of jeGeb.values()) {
      ids.sort((a, b) => (E[a].datensatz.erfasst_am < E[b].datensatz.erfasst_am ? -1 : E[a].datensatz.erfasst_am > E[b].datensatz.erfasst_am ? 1 : 0));
      const merkmal = (i) => JSON.stringify([E[i].datensatz.kategorie, E[i].vermieter ?? null, E[i].datensatz.vermietet ?? null]);
      if (new Set(ids.map(merkmal)).size === 1) {
        for (const i of ids.slice(0, -1)) {
          E[i].status = "verworfen"; E[i].konflikt = `Dublette von ${ids.at(-1)}`;
          verlauf("Dublette verworfen", i);
        }
        aendern(E[ids.at(-1)], "konflikt", null);
      } else for (const i of ids) aendern(E[i], "konflikt", `abweichende Angaben zum Gebäude (${ids.length} Einträge)`);
    }
    // 3. Mietangaben: Vermieter über das Gebäude (nur juristische Person, geprüfter Eintrag), mögliche Dubletten
    const jpJeGeb = new Map();
    for (const [, e] of eig) if (e.status === "offen" && !e.konflikt && (e.vermieter || "").startsWith("JP:")) jpJeGeb.set(e.datensatz.objekt.id, e.vermieter);
    const gruppen = new Map();
    for (const [i, e] of aktiv) {
      if (e.typ !== "miete") continue;
      const r = e.datensatz;
      let eigen = r.vermieter_schluessel;
      eigen = eigen ? (jpNamen.get(nameNormieren(eigen.slice(3))) ?? eigen) : null;
      aendern(e, "vermieter", eigen || (jpJeGeb.get(r.gebaeude_id) ?? null));
      const key = JSON.stringify([r.gebaeude_id, "eur_je_m2" in r ? r.eur_je_m2 : r.nettokalt_eur ?? null, r.vertragsbeginn_jahr, r.wohnflaeche_klasse]);
      if (!gruppen.has(key)) gruppen.set(key, []);
      gruppen.get(key).push(i);
    }
    for (const ids of gruppen.values()) for (const i of ids) aendern(E[i], "konflikt", ids.length > 1 ? `mögliche Dublette (${ids.length} gleiche Angaben)` : null);
    verlauf("geprüft");
  }
  function freigeben(ids) {  // ids = null: alle, die freigegeben werden können
    let n = 0;
    for (const [i, e] of Object.entries(S.d.eintraege)) {
      if ((ids === null || ids.includes(i)) && e.status === "offen" && !e.konflikt && !e.freigaben.includes(S.pruefer)) {
        e.freigaben.push(S.pruefer); verlauf("freigegeben", i); n++;
      }
    }
    return n;
  }
  function verwerfen(i, grund) {
    const e = S.d.eintraege[i];
    Object.assign(e, { status: "verworfen", konflikt: `verworfen: ${grund}`, freigaben: [] });
    verlauf(`verworfen (${grund})`, i);
  }
  function pruefliste() {  // ohne Namen von Privatpersonen und ohne Mietbeträge (wie die Prüfliste in Python)
    const E = Object.entries(S.d.eintraege).sort((a, b) => (a[1].typ + (a[1].datensatz.erfasst_am || "")).localeCompare(b[1].typ + (b[1].datensatz.erfasst_am || "")));
    return E.map(([i, e]) => [i, e.typ, e.typ === "eigentum" ? e.datensatz.objekt.id : e.datensatz.gebaeude_id, e.datensatz.kategorie || "",
      e.vermieter || "", e.status, e.konflikt || "", new Set(e.freigaben).size, freigegeben(e) ? "ja" : "nein", e.name_oeffentlich ?? ""]);
  }

  // --- Oberfläche --------------------------------------------------------------------------------------------------
  function anzeigen() {
    const E = Object.values(S.d.eintraege);
    const zahl = (f) => E.filter(f).length;
    $("#stand").innerHTML = [["Schlüssel", S.schl.key_id], ["Prüfer-ID", S.pruefer],
      ["Einträge", `${E.length} (Eigentum ${zahl((e) => e.typ === "eigentum")}, Mietangaben ${zahl((e) => e.typ === "miete")})`],
      ["Offen ohne Hinweis", zahl((e) => e.status === "offen" && !e.konflikt)], ["Mit Hinweis", zahl((e) => e.status === "offen" && e.konflikt)],
      ["Verworfen", zahl((e) => e.status === "verworfen")], ["Zweimal freigegeben", zahl(freigegeben)],
      ["Register", S.register ? `${S.register.size} Erfasser-IDs` : "nicht geladen: Einladungscodes werden nicht geprüft"],
      ["Zugriffe auf Namen in dieser Sitzung", S.protokoll.length]]
      .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("");
    document.querySelectorAll(".pruefer-id").forEach((x) => { x.textContent = S.pruefer; });
    const angaben = (e) => {
      const r = e.datensatz;
      return e.typ === "eigentum" ? [r.kategorie, r.vermietet && `vermietet: ${r.vermietet}`, r.beleg_art, r.sicherheit, r.name_juristische_person].filter(Boolean).join(" · ")
        : [`${String(r.eur_je_m2 ?? "").replace(".", ",")} €/m²`, r.wohnflaeche_klasse, r.baujahr_klasse, r.vertragsbeginn_jahr].filter(Boolean).join(" · ");
    };
    $("#liste tbody").innerHTML = Object.entries(S.d.eintraege).map(([i, e]) => {
      const kann = e.status === "offen";
      return `<tr class="${e.status === "verworfen" ? "verworfen" : freigegeben(e) ? "frei" : ""}">
        <td>${kann ? `<input type="checkbox" value="${esc(i)}" aria-label="Eintrag ${esc(i.slice(0, 8))} auswählen">` : ""}</td>
        <td><code>${esc(i.slice(0, 8))}</code></td><td>${e.typ === "eigentum" ? "Eigentum" : "Miete"}</td>
        <td>${esc(e.typ === "eigentum" ? e.datensatz.objekt.id : e.datensatz.gebaeude_id)}</td><td>${esc(angaben(e))}</td>
        <td>${esc(e.vermieter || "")}</td><td>${esc(e.status)}</td><td>${esc(e.konflikt || "")}</td>
        <td>${esc([...new Set(e.freigaben)].join(", ") || "–")}</td></tr>`;
    }).join("") || `<tr><td colspan="9">Noch keine Einträge.</td></tr>`;
    $("#ungespeichert").textContent = S.geaendert ? "Es gibt Änderungen, die noch nicht als Bestandsdatei gespeichert sind." : "";
    $("#speichern-protokoll").disabled = !S.protokoll.length;
  }
  const ausgewaehlt = () => [...document.querySelectorAll("#liste tbody input:checked")].map((x) => x.value);
  async function dateiText(input) { const f = input.files[0]; return f ? { name: f.name, inhalt: await f.text() } : null; }

  function netz() { $("#netz").textContent = navigator.onLine ? "Hinweis: Das Gerät ist mit dem Netz verbunden. Die Seite sendet nichts; sicherer ist es trotzdem, das Netz zu trennen." : ""; }
  addEventListener("online", netz); addEventListener("offline", netz); netz();

  $("#form-oeffnen").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const st = $("#oeffnen-status"), knopf = $("#knopf-oeffnen");
    const pruefer = $("#f-pruefer").value.trim();
    if (!PRUEFER.test(pruefer)) { $("#f-pruefer").setAttribute("aria-invalid", "true"); return melden(st, "Prüfer-ID im Format P-… angeben (pseudonym, kein Name).", "fehler"); }
    $("#f-pruefer").removeAttribute("aria-invalid");
    const sd = await dateiText($("#f-schluessel"));
    if (!sd) return melden(st, "Bitte die Schlüsseldatei auswählen.", "fehler");
    knopf.disabled = true; knopf.textContent = "Wird geöffnet …";
    await new Promise((r) => setTimeout(r, 30));  // Argon2id braucht einige Sekunden
    try {
      const schl = schluesselLaden(JSON.parse(sd.inhalt), $("#f-pass").value);
      const bd = await dateiText($("#f-bestand"));
      const d = bd ? JSON.parse(sodium.to_string(schl.oeffnen(bd.inhalt))) : { version: 1, eintraege: {}, vermieter_naechste: 1, verlauf: [] };
      if (d.version !== 1 || typeof d.eintraege !== "object") throw new Error("Keine Bestandsdatei der Prüfgruppe.");
      const rd = await dateiText($("#f-register"));
      const register = rd ? new Map(tsvLesen(rd.inhalt, KOPF_REGISTER).map((z) => [z.erfasser_id, z])) : null;
      const pd = await dateiText($("#f-protokoll"));
      S = { schl, d, pruefer, register, protokoll: [], protokollAlt: pd ? tsvLesen(pd.inhalt, ["zeit", "pruefer", "datensatz", "zweck"]) : [],
        einlesen: [], geaendert: !bd };
      $("#f-pass").value = "";
      $("#sitzung").hidden = false;
      anzeigen();
      melden(st, `Geöffnet: ${bd ? `Bestand mit ${Object.keys(d.eintraege).length} Einträgen` : "neuer Bestand"}, Schlüssel ${schl.key_id}.`);
    } catch (err) {
      melden(st, `Fehler: ${err.message.includes("mit keinem Schlüssel") ? "Die Bestandsdatei passt nicht zu diesem Schlüssel." : err.message}`, "fehler");
    } finally {
      knopf.disabled = false; knopf.textContent = "Öffnen";
    }
  });

  $("#form-pruefer").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const p = $("#f-pruefer2").value.trim();
    if (!PRUEFER.test(p)) return melden($("#pruefer-status"), "Prüfer-ID im Format P-… angeben.", "fehler");
    S.pruefer = p; $("#f-pruefer2").value = "";
    melden($("#pruefer-status"), `Jetzt prüft ${p}. Freigaben werden unter dieser ID vermerkt.`);
    anzeigen();
  });

  $("#form-eingang").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const st = $("#eingang-status");
    const dateien = await Promise.all([...$("#f-exporte").files].map(async (f) => ({ name: f.name, inhalt: await f.text() })));
    if (!dateien.length) return melden(st, "Bitte Exportdateien auswählen.", "fehler");
    try {
      const { neu, zeilen } = einlesen(dateien);
      S.einlesen.push(...zeilen);
      $("#eingang-tabelle tbody").innerHTML = zeilen.map((z) => `<tr><td><code>${esc(z[0].slice(0, 8))}</code></td><td>${esc(z[1])}</td><td>${esc(z[2])}</td><td>${esc(z[3])}</td></tr>`).join("");
      $("#eingang-ergebnis").hidden = false;
      $("#f-exporte").value = "";
      anzeigen();
      melden(st, `${neu} aufgenommen, ${zeilen.filter((z) => z[2].startsWith("abgewiesen")).length} abgewiesen, ${zeilen.filter((z) => z[2] === "schon im Bestand").length} schon im Bestand. Danach „Prüfen“.`);
    } catch (err) {
      melden(st, `Fehler: ${err.message}`, "fehler");
    }
  });
  $("#speichern-einlesebericht").addEventListener("click", () => speichern(`einlesen_${heute()}.tsv`, tsv(["id", "typ", "ergebnis", "datei"], S.einlesen), "text/tab-separated-values"));

  $("#knopf-pruefen").addEventListener("click", () => {
    pruefen(); anzeigen();
    const E = Object.values(S.d.eintraege);
    melden($("#pruefen-status"), `Geprüft: ${E.filter((e) => e.status === "offen" && !e.konflikt).length} ohne Hinweis, ${E.filter((e) => e.status === "offen" && e.konflikt).length} mit Hinweis (bitte ansehen und verwerfen oder in der Erfassung klären).`);
  });
  $("#knopf-alle").addEventListener("click", () => { const n = freigeben(null); anzeigen(); melden($("#pruefen-status"), `${n} Einträge von ${S.pruefer} freigegeben.`); });
  $("#knopf-auswahl-frei").addEventListener("click", () => {
    const ids = ausgewaehlt();
    if (!ids.length) return melden($("#pruefen-status"), "Bitte Einträge auswählen.", "fehler");
    const n = freigeben(ids); anzeigen(); melden($("#pruefen-status"), `${n} Einträge von ${S.pruefer} freigegeben.`);
  });
  $("#knopf-verwerfen").addEventListener("click", () => {
    const ids = ausgewaehlt(), grund = $("#f-grund").value.trim();
    if (!ids.length) return melden($("#pruefen-status"), "Bitte Einträge auswählen.", "fehler");
    if (!grund) { $("#f-grund").setAttribute("aria-invalid", "true"); return melden($("#pruefen-status"), "Bitte einen Grund angeben.", "fehler"); }
    $("#f-grund").removeAttribute("aria-invalid");
    ids.forEach((i) => verwerfen(i, grund)); $("#f-grund").value = "";
    anzeigen(); melden($("#pruefen-status"), `${ids.length} Einträge verworfen.`);
  });
  $("#speichern-pruefliste").addEventListener("click", () => speichern(`pruefung_${heute()}.tsv`,
    tsv(["id", "typ", "gebaeude", "kategorie", "vermieter", "status", "konflikt", "freigaben", "freigegeben", "name_oeffentlich"], pruefliste()), "text/tab-separated-values"));

  $("#speichern-bestand").addEventListener("click", () => {
    speichern("bestand.sealed", S.schl.versiegeln(sodium.from_string(JSON.stringify(S.d))));
    S.geaendert = false; anzeigen();
  });
  $("#speichern-protokoll").addEventListener("click", () => speichern("namenzugriff.tsv",
    tsv(["zeit", "pruefer", "datensatz", "zweck"], [...S.protokollAlt.map((z) => [z.zeit, z.pruefer, z.datensatz, z.zweck]), ...S.protokoll]), "text/tab-separated-values"));
  $("#knopf-beenden").addEventListener("click", () => {
    if (S?.geaendert && !confirm("Der Bestand ist noch nicht gespeichert. Trotzdem beenden?")) return;
    S = null; location.reload();
  });
  addEventListener("beforeunload", (ev) => { if (S?.geaendert) { ev.preventDefault(); ev.returnValue = ""; } });
  addEventListener("pagehide", () => { S = null; });

  window.sodium.ready.then(() => {
    sodium = window.sodium; V = sodium.base64_variants.ORIGINAL;
    $("#knopf-oeffnen").disabled = false;
    $("#laden").remove();
  });
})();
