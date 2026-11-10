// Einladungskarten (Ausgabestelle): Kartenliste öffnen, Karten mit QR-Code drucken, Karten sperren, Liste speichern.
// Codes wie tools/einladung.py (16 Zeichen, Hash „wiz-einladung:“, Erfasser-ID „wiz-erfasser:“). Der QR-Code öffnet
// erfassen.html#code=…&bis=…&schluessel=KENNUNG~SCHLÜSSEL; die App speichert Code und öffentlichen Schlüssel im Gerät.
// Die Kartenliste (wiz-kartenliste-1) enthält nur Erfasser-ID, Hash, Ausgabe, Ablauf und Sperre; die Codes stehen nur auf
// den gedruckten Karten. Nichts wird gesendet (connect-src 'none') oder im Browser gespeichert.
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const ZEICHEN = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  const FORMAT = "wiz-kartenliste-1";
  let L = null, geaendert = false;

  async function sha256(text) {
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  const heute = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const datumDe = (iso) => (iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}` : "");
  function bisDatum(iso, monate) {  // wie einladung.bis_datum
    const [j, m, t] = iso.split("-").map(Number);
    const g = j * 12 + (m - 1) + monate;
    return `${Math.floor(g / 12)}-${String((g % 12) + 1).padStart(2, "0")}-${String(Math.min(t, 28)).padStart(2, "0")}`;
  }
  function neuerCode() {
    const z = crypto.getRandomValues(new Uint8Array(16));
    return [...z].map((b) => ZEICHEN[b & 31]).join("").match(/.{4}/g).join("-");  // 32 Zeichen: jedes Byte ergibt gleichverteilt eines
  }
  function speichern(name, text) {
    const url = URL.createObjectURL(new Blob([text], { type: "application/json;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function melden(el, text, art = "erfolg") { el.className = art; el.textContent = text; el.focus?.(); }
  function drucken(html) {
    const d = $("#druck");
    d.innerHTML = html;
    document.body.classList.add("drucken");
    const weg = () => { document.body.classList.remove("drucken"); d.innerHTML = ""; removeEventListener("afterprint", weg); };
    addEventListener("afterprint", weg);
    print();
  }
  function qrSvg(text) {
    const q = qrcode(0, "M");
    q.addData(text, "Byte");
    q.make();
    return q.createSvgTag({ cellSize: 4, margin: 4, scalable: true });
  }
  const adresse = () => {
    const basis = document.querySelector('meta[name="wiz-site-url"]')?.content || new URL("../", location.href).href;  // Seite liegt in /intern/
    return basis.replace(/\/?$/, "/") + "erfassen.html";
  };
  const link = (code, bis) => `${adresse()}#code=${code}&bis=${bis}&schluessel=${L.key_id}~${L.public_key.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")}`;

  function lesen(text) {
    let d;
    try { d = JSON.parse(text); } catch { d = null; }
    if (!d || d.format !== FORMAT || !/^[\w-]{1,40}$/.test(d.key_id || "") || !/^[A-Za-z0-9+/]{43}=$/.test(d.public_key || "") || !Array.isArray(d.karten))
      throw new Error("Das ist nicht die Liste der Einladungskarten. Bitte wähl die Datei „kartenliste.json“.");
    return d;
  }
  const status = (k) => (k.widerrufen ? `gesperrt seit ${datumDe(k.widerrufen)}` : k.gueltig_bis < heute() ? "abgelaufen" : "gültig");

  function anzeigen() {
    $("#karten tbody").innerHTML = L.karten.map((k, i) => `<tr><td><code>${esc(k.erfasser_id)}</code></td><td>${datumDe(k.ausgegeben)}</td>
      <td>${datumDe(k.gueltig_bis)}</td><td>${esc(status(k))}</td>
      <td>${k.widerrufen ? "" : `<button type="button" class="knopf klein-knopf" data-sperren="${i}">Sperren<span class="visually-hidden"> (${esc(k.erfasser_id)})</span></button>`}</td></tr>`).join("")
      || `<tr><td colspan="5">Noch keine Karten.</td></tr>`;
    $("#ungespeichert").textContent = geaendert ? "Du hast etwas geändert. Bitte sichere die Liste jetzt." : "";
  }

  $("#f-liste").addEventListener("change", async () => {
    const f = $("#f-liste").files[0], st = $("#oeffnen-status");
    if (!f) return;
    try {
      L = lesen(await f.text());
      geaendert = false;
      anzeigen();
      const n = L.karten.length, g = L.karten.filter((k) => status(k) === "gültig").length;
      melden(st, `Liste geöffnet: ${n} Karten, davon ${g} gültig.`);
      Schritte.frei("oeffnen", true);
    } catch (err) {
      L = null; Schritte.sperren("oeffnen");
      melden(st, err.message, "fehler");
    }
  });

  $("#form-neu").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const a = $("#anzahl"), st = $("#neu-status"), n = Number(a.value);
    a.removeAttribute("aria-invalid");
    if (!Number.isInteger(n) || n < 1 || n > 50) { a.setAttribute("aria-invalid", "true"); return melden(st, "Bitte gib eine Zahl zwischen 1 und 50 ein.", "fehler"); }
    const ab = heute(), bis = bisDatum(ab, Number(L.gueltig_monate) || 12);
    const neu = [];
    for (let i = 0; i < n; i++) {
      const code = neuerCode(), c = code.replace(/-/g, "");
      neu.push({ code, erfasser_id: `E-${(await sha256(`wiz-erfasser:${c}`)).slice(0, 8)}`, hash: await sha256(`wiz-einladung:${c}`) });
    }
    L.karten.push(...neu.map((x) => ({ erfasser_id: x.erfasser_id, hash: x.hash, ausgegeben: ab, gueltig_bis: bis, widerrufen: "" })));
    geaendert = true;
    anzeigen();
    melden(st, `${n} Karten erstellt. Das Druckfenster öffnet sich. Wenn alles gedruckt ist: weiter zum Sichern.`);
    drucken(`<div class="blatt">${neu.map((x) => `<div class="karte" data-link="${esc(link(x.code, bis))}"><div class="karte-qr">${qrSvg(link(x.code, bis))}</div>
<div><p><strong>Einladung: Erfassung Wohnen und Eigentum</strong></p>
<ol><li>QR-Code mit der Kamera Ihres Handys scannen.</li><li>Die Seite öffnet sich, Sie sind angemeldet.</li>
<li>Im Browsermenü „Zum Startbildschirm hinzufügen“ wählen.</li></ol>
<p>Gültig bis ${datumDe(bis)} · Karte ${esc(x.erfasser_id)}</p><p class="klein">Karte nicht weitergeben und nicht fotografieren lassen.</p></div></div>`).join("")}</div>
<div class="blatt liste"><h1>Ausgegebene Karten vom ${datumDe(ab)} (für deine Unterlagen)</h1>
<p>Diese Liste bleibt bei der Ausgabestelle. Nicht an die Prüfgruppe geben.</p>
<table><thead><tr><th>Karte</th><th>Gültig bis</th><th>Erhalten von (Name)</th></tr></thead>
<tbody>${neu.map((x) => `<tr><td>${esc(x.erfasser_id)}</td><td>${datumDe(bis)}</td><td></td></tr>`).join("")}</tbody></table></div>`);
  });

  $("#karten").addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-sperren]");
    if (!b) return;
    const k = L.karten[Number(b.dataset.sperren)];
    if (!confirm(`Karte ${k.erfasser_id} sperren? Das lässt sich nicht rückgängig machen.`)) return;
    k.widerrufen = heute();
    geaendert = true;
    anzeigen();
    melden($("#sperren-status"), `Karte ${k.erfasser_id} gesperrt. Bitte danach die Liste sichern und der Prüfgruppe schicken.`);
  });

  $("#speichern").addEventListener("click", () => {
    if (!L) return;
    L.gespeichert = new Date().toISOString().slice(0, 19) + "Z";
    speichern("kartenliste.json", JSON.stringify(L, null, 1));
    geaendert = false;
    anzeigen();
  });
  addEventListener("beforeunload", (ev) => { if (geaendert) { ev.preventDefault(); ev.returnValue = ""; } });
})();
