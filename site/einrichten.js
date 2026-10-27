// Einrichtung der Erfassung (Issue 53): Schlüssel der Prüfgruppe, Papiersicherung und Einladungscodes, nur im Browser.
// Dateiformate wie tools/pruefgruppe.py (Schlüsseldatei Version 2, Sicherung „WIZPG1“) und tools/einladung.py (Codes,
// Register); die Python-Werkzeuge lesen alles, was hier entsteht. Nichts wird gesendet (connect-src 'none') oder im
// Browser gespeichert; Geheimnisse liegen nur im Arbeitsspeicher dieses Fensters.
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const meta = (n) => document.querySelector(`meta[name="${n}"]`)?.content || "";
  const ALG = "libsodium-sealedbox-x25519";
  // Argon2id „moderat“ wie nacl.pwhash.argon2id.OPSLIMIT_MODERATE / MEMLIMIT_MODERATE in tools/pruefgruppe.py
  const OPS = 3, MEM = 268435456;
  const ZEICHEN = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  const KOPF = ["erfasser_id", "hash", "ausgegeben", "gueltig_bis", "widerrufen"];
  let sodium = null, V = null;
  let schluessel = null;      // {datei, oeffentlich} nach Schritt 1
  let codes = null;           // {karten, register, eintraege} nach Schritt 2
  let wiederhergestellt = null;

  // --- Hilfen ------------------------------------------------------------------------------------------------
  async function sha256(text) {
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  const b64 = (u8) => sodium.to_base64(u8, V);
  const unb64 = (s) => sodium.from_base64(s, V);
  const heute = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const datumDe = (iso) => `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}`;
  function speichern(name, text, typ = "application/json") {
    const url = URL.createObjectURL(new Blob([text], { type: `${typ};charset=utf-8` }));
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  // Meldung unter dem Formular; die Knöpfe zum Speichern und Drucken erscheinen nur nach Erfolg
  function melden(el, text, art = "erfolg", ergebnis = null) {
    el.className = art; el.textContent = text; el.focus();
    if (ergebnis) $(ergebnis).hidden = art !== "erfolg";
  }
  function drucken(html) {
    const d = $("#druck");
    d.innerHTML = html;
    document.body.classList.add("drucken");
    const weg = () => { document.body.classList.remove("drucken"); d.innerHTML = ""; window.removeEventListener("afterprint", weg); };
    window.addEventListener("afterprint", weg);
    window.print();
  }
  const oeffentlicheDatei = (inhalt) => JSON.stringify({ format: "wiz-einrichtung-1", erstellt: new Date().toISOString().slice(0, 19) + "Z", ...inhalt }, null, 1);

  // --- Schritt 1: Schlüssel (wie pruefgruppe._neues_paar und _schuetzen) ---------------------------------------
  async function schluesselErzeugen(passphrase) {
    const paar = sodium.crypto_box_keypair();
    const pub = b64(paar.publicKey);
    const key_id = `pg-${heute().replaceAll("-", "")}-${(await sha256Bytes(paar.publicKey)).slice(0, 8)}`;
    const salz = sodium.randombytes_buf(sodium.crypto_pwhash_SALTBYTES);
    const k = sodium.crypto_pwhash(sodium.crypto_secretbox_KEYBYTES, passphrase, salz, OPS, MEM, sodium.crypto_pwhash_ALG_ARGON2ID13);
    const nonce = sodium.randombytes_buf(sodium.crypto_secretbox_NONCEBYTES);
    const box = sodium.crypto_secretbox_easy(paar.privateKey, nonce, k);
    const ct = new Uint8Array(nonce.length + box.length); ct.set(nonce); ct.set(box, nonce.length);  // wie PyNaCl SecretBox.encrypt
    const oeffentlich = { key_id, alg: ALG, public_key: pub };
    const datei = { version: 2, ...oeffentlich, secret_enc: { kdf: "argon2id", opslimit: OPS, memlimit: MEM, salt: b64(salz), ciphertext: b64(ct) },
      frueher: [], gesperrt: [] };
    sodium.memzero(paar.privateKey); sodium.memzero(k);
    return { datei, oeffentlich };
  }
  async function sha256Bytes(u8) {
    const h = await crypto.subtle.digest("SHA-256", u8);
    return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  // Selbsttest: mit der Passphrase entsperren, öffentlichen Teil nachrechnen, versiegeln und wieder öffnen
  function entsperren(datei, passphrase) {
    const e = datei.secret_enc;
    const k = sodium.crypto_pwhash(sodium.crypto_secretbox_KEYBYTES, passphrase, unb64(e.salt), e.opslimit, e.memlimit, sodium.crypto_pwhash_ALG_ARGON2ID13);
    const ct = unb64(e.ciphertext), n = sodium.crypto_secretbox_NONCEBYTES;
    try {
      return sodium.crypto_secretbox_open_easy(ct.slice(n), ct.slice(0, n), k);
    } catch {
      return null;
    } finally {
      sodium.memzero(k);
    }
  }
  function selbsttest(datei, passphrase) {
    const geheim = entsperren(datei, passphrase);
    if (!geheim) return false;
    const pub = sodium.crypto_scalarmult_base(geheim);
    const probe = sodium.crypto_box_seal(sodium.from_string("Probe"), pub);
    const ok = b64(pub) === datei.public_key && sodium.to_string(sodium.crypto_box_seal_open(probe, pub, geheim)) === "Probe";
    sodium.memzero(geheim);
    return ok;
  }

  // --- Papiersicherung (wie pruefgruppe.ausdruck_zeilen und aus_ausdruck) ---------------------------------------
  const nr3 = (i) => String(i).padStart(3, "0");
  async function sicherungZeilen(datei) {
    const roh = btoa(JSON.stringify(datei));
    const stuecke = roh.match(/.{1,60}/g);
    const kopf = `WIZPG1:${stuecke.length}:${(await sha256(roh)).slice(0, 16)}`;
    return Promise.all([kopf, ...stuecke].map(async (t, i) => `${nr3(i)} ${t} ${(await sha256(nr3(i) + t)).slice(0, 4)}`));
  }
  function qrSvg(text) {
    const q = qrcode(0, "M");
    q.addData(text, "Byte");
    q.make();
    return q.createSvgTag({ cellSize: 4, margin: 4, scalable: true });
  }
  async function sicherungBlatt(datei) {
    const zeilen = await sicherungZeilen(datei);
    const bloecke = [];
    for (let i = 0; i < zeilen.length; i += 5) bloecke.push(zeilen.slice(i, i + 5));
    const qr = bloecke.map((b) => `<figure>${qrSvg(b.join("\n"))}<figcaption>Zeilen ${b[0].slice(0, 3)}–${b.at(-1).slice(0, 3)}</figcaption></figure>`).join("");
    return `<h1>Sicherung der Schlüsseldatei der Prüfgruppe</h1>
<p>Erstellt ${datumDe(heute())}. Schlüssel: ${esc(datei.key_id)}.</p>
<p>Nur mit der Passphrase nutzbar; die Passphrase liegt getrennt. Wiederherstellen: QR-Codes scannen oder Zeilen abtippen und auf der
Einrichtungsseite (Schritt 3) einfügen, oder als Textdatei mit <code>python tools/pruefen.py schluessel-zurueck TEXTDATEI ZIEL</code>.</p>
${qr}<pre>${esc(zeilen.join("\n"))}</pre>`;
  }
  async function ausZeilen(text) {
    const gelesen = new Map();
    for (const z of text.split(/\r?\n/)) {
      const m = z.match(/^\s*(\d{3})\s+(\S+)\s+([0-9a-f]{4})\s*$/);
      if (!m) continue;
      if ((await sha256(m[1] + m[2])).slice(0, 4) !== m[3]) throw new Error(`Zeile ${m[1]}: Prüfziffern passen nicht (Tippfehler?).`);
      gelesen.set(Number(m[1]), m[2]);
    }
    const kopf = (gelesen.get(0) || "").split(":");
    if (kopf.length !== 3 || kopf[0] !== "WIZPG1") throw new Error("Zeile 000 fehlt oder ist keine Sicherung der Prüfgruppe.");
    const n = Number(kopf[1]);
    const fehlen = [];
    for (let i = 1; i <= n; i++) if (!gelesen.has(i)) fehlen.push(nr3(i));
    if (fehlen.length) throw new Error(`Es fehlen Zeilen: ${fehlen.join(", ")}.`);
    const roh = Array.from({ length: n }, (_, i) => gelesen.get(i + 1)).join("");
    if ((await sha256(roh)).slice(0, 16) !== kopf[2]) throw new Error("Die Zeilen ergeben nicht die gesicherte Datei (Prüfsumme).");
    const d = JSON.parse(atob(roh));
    if (d.version !== 2 || !d.secret_enc || !d.public_key) throw new Error("Keine Schlüsseldatei der Prüfgruppe (Version 2).");
    return d;
  }

  // --- Schritt 2: Codes (wie einladung.neu, code_hash, erfasser_id, bis_datum) ------------------------------------
  function neuerCode() {
    const z = crypto.getRandomValues(new Uint8Array(16));
    const roh = [...z].map((b) => ZEICHEN[b & 31]).join("");  // 32 Zeichen: jedes Byte ergibt gleichverteilt eines
    return roh.match(/.{4}/g).join("-");
  }
  const normieren = (c) => c.toUpperCase().replace(/[\s-]/g, "").replace(/O/g, "0").replace(/[IL]/g, "1");
  function bisDatum(iso, monate) {
    const [j, m, t] = iso.split("-").map(Number);
    const gesamt = j * 12 + (m - 1) + monate;
    return `${Math.floor(gesamt / 12)}-${String((gesamt % 12) + 1).padStart(2, "0")}-${String(Math.min(t, 28)).padStart(2, "0")}`;
  }
  function registerLesen(text) {
    const zeilen = text.trim().split(/\r?\n/);
    if (!zeilen.length || zeilen[0].split("\t").join(",") !== KOPF.join(",")) throw new Error("Das Register hat nicht die erwarteten Spalten.");
    return zeilen.slice(1).filter(Boolean).map((z) => Object.fromEntries(z.split("\t").map((w, i) => [KOPF[i], w ?? ""])));
  }
  async function codesErzeugen(anzahl, register) {
    const monate = Number(meta("wiz-einladung-monate")) || 12;
    const ab = heute(), bis = bisDatum(ab, monate);
    const neu = [];
    for (let i = 0; i < anzahl; i++) {
      const c = neuerCode(), n = normieren(c);
      neu.push({ code: c, erfasser_id: `E-${(await sha256(`wiz-erfasser:${n}`)).slice(0, 8)}`, hash: await sha256(`wiz-einladung:${n}`), bis });
    }
    const zeilen = [...register, ...neu.map((x) => ({ erfasser_id: x.erfasser_id, hash: x.hash, ausgegeben: ab, gueltig_bis: x.bis, widerrufen: "" }))];
    return { neu, register: [KOPF.join("\t"), ...zeilen.map((z) => KOPF.map((k) => z[k] || "").join("\t"))].join("\n") + "\n",
      eintraege: neu.map((x) => ({ hash: x.hash, bis: x.bis })) };
  }
  function kartenBlatt(neu) {
    const basis = meta("wiz-site-url") || new URL("./", location.href).href;
    const adresse = basis.replace(/\/?$/, "/") + "erfassen.html";
    return `<p>Ausschneiden und persönlich übergeben. Wer welche Erfasser-ID erhält, nur in den Unterlagen der Ausgabestelle notieren.</p>` +
      neu.map((x) => `<div class="karte"><p><strong>Einladung zur Erfassung Wohnen und Eigentum</strong></p>
<p class="code">${esc(x.code)}</p><p>Gültig bis ${datumDe(x.bis)}. Erfasser-ID ${esc(x.erfasser_id)}.</p>
<p>Erfassungsseite: <strong>${esc(adresse)}</strong></p>
<p>Code in der App eingeben, dann diesen Zettel vernichten. Nicht abfotografieren, nicht weitergeben.</p></div>`).join("");
  }

  // --- Oberfläche ------------------------------------------------------------------------------------------------
  function netz() { $("#netz").textContent = navigator.onLine ? "Hinweis: Das Gerät ist mit dem Netz verbunden. Die Seite sendet nichts; sicherer ist es trotzdem, jetzt das Netz zu trennen." : ""; }
  addEventListener("online", netz); addEventListener("offline", netz); netz();

  $("#form-schluessel").addEventListener("submit", async (e) => {
    e.preventDefault();
    const p1 = $("#pass1"), p2 = $("#pass2"), st = $("#schluessel-status");
    p1.removeAttribute("aria-invalid"); p2.removeAttribute("aria-invalid");
    if (p1.value.length < 12) { p1.setAttribute("aria-invalid", "true"); return melden(st, "Die Passphrase braucht mindestens 12 Zeichen.", "fehler", "#ergebnis-schluessel"); }
    if (p1.value !== p2.value) { p2.setAttribute("aria-invalid", "true"); return melden(st, "Die beiden Eingaben stimmen nicht überein.", "fehler", "#ergebnis-schluessel"); }
    const knopf = $("#knopf-schluessel");
    knopf.disabled = true; knopf.textContent = "Wird erzeugt …";
    await new Promise((r) => setTimeout(r, 30));  // Anzeige aktualisieren; Argon2id braucht einige Sekunden
    try {
      const s = await schluesselErzeugen(p1.value);
      if (!selbsttest(s.datei, p1.value)) throw new Error("Selbsttest fehlgeschlagen.");
      schluessel = s;
      p1.value = ""; p2.value = "";
      melden(st, `Schlüssel ${s.oeffentlich.key_id} erzeugt. Selbsttest bestanden: Die Passphrase öffnet ihn, Versiegeln und Öffnen funktionieren.`, "erfolg", "#ergebnis-schluessel");
    } catch (err) {
      melden(st, `Fehler: ${err.message}`, "fehler", "#ergebnis-schluessel");
    } finally {
      knopf.disabled = false; knopf.textContent = "Schlüssel erzeugen";
    }
  });
  $("#speichern-schluessel").addEventListener("click", () => speichern(`pg_${schluessel.datei.key_id}.json`, JSON.stringify(schluessel.datei)));
  $("#drucken-sicherung").addEventListener("click", async () => drucken(await sicherungBlatt(schluessel.datei)));
  $("#speichern-oeffentlich-schluessel").addEventListener("click", () =>
    speichern(`einrichtung_schluessel_${schluessel.oeffentlich.key_id}.json`, oeffentlicheDatei({ schluessel: schluessel.oeffentlich })));

  $("#form-codes").addEventListener("submit", async (e) => {
    e.preventDefault();
    const a = $("#anzahl"), st = $("#codes-status");
    const n = Number(a.value);
    a.removeAttribute("aria-invalid");
    if (!Number.isInteger(n) || n < 1 || n > 50) { a.setAttribute("aria-invalid", "true"); return melden(st, "Bitte eine Anzahl zwischen 1 und 50 angeben.", "fehler", "#ergebnis-codes"); }
    try {
      const f = $("#register-datei").files[0];
      const register = f ? registerLesen(await f.text()) : [];
      codes = await codesErzeugen(n, register);
      melden(st, `${n} Codes erzeugt (Erfasser-IDs ${codes.neu.map((x) => x.erfasser_id).join(", ")}).${register.length ? ` Register um ${n} Zeilen ergänzt.` : ""} Jetzt die Karten drucken.`, "erfolg", "#ergebnis-codes");
    } catch (err) {
      melden(st, `Fehler: ${err.message}`, "fehler", "#ergebnis-codes");
    }
  });
  $("#drucken-codes").addEventListener("click", () => drucken(kartenBlatt(codes.neu)));
  $("#speichern-register").addEventListener("click", () => speichern(`einladungen_register_${heute()}.tsv`, codes.register, "text/tab-separated-values"));
  $("#speichern-oeffentlich-codes").addEventListener("click", () =>
    speichern(`einrichtung_codes_${heute()}_${codes.neu[0].erfasser_id}.json`, oeffentlicheDatei({ einladungen: codes.eintraege })));

  $("#form-sicherung").addEventListener("submit", async (e) => {
    e.preventDefault();
    const st = $("#sicherung-status"), pass = $("#pass-pruef");
    wiederhergestellt = null;
    try {
      const d = await ausZeilen($("#zeilen").value);
      let text = `Sicherung vollständig und unbeschädigt: Schlüssel ${d.key_id}.`;
      if (pass.value) {
        const knopf = $("#knopf-sicherung");
        knopf.disabled = true;
        await new Promise((r) => setTimeout(r, 30));
        const ok = selbsttest(d, pass.value);
        knopf.disabled = false;
        if (!ok) { pass.value = ""; return melden(st, `${text} Die Passphrase öffnet ihn aber nicht.`, "fehler", "#ergebnis-sicherung"); }
        text += " Die Passphrase öffnet ihn.";
      }
      pass.value = "";
      wiederhergestellt = d;
      melden(st, text, "erfolg", "#ergebnis-sicherung");
    } catch (err) {
      melden(st, err.message, "fehler", "#ergebnis-sicherung");
    }
  });
  $("#speichern-wiederhergestellt").addEventListener("click", () => speichern(`pg_${wiederhergestellt.key_id}.json`, JSON.stringify(wiederhergestellt)));

  // Fenster schließen oder neu laden: Geheimnisse aus dem Speicher nehmen
  addEventListener("pagehide", () => { schluessel = null; codes = null; wiederhergestellt = null; });

  window.sodium.ready.then(() => {
    sodium = window.sodium; V = sodium.base64_variants.ORIGINAL;
    for (const id of ["#knopf-schluessel", "#knopf-codes", "#knopf-sicherung"]) $(id).disabled = false;
    $("#laden").remove();
  });
})();
