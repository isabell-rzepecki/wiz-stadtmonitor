// Schritt für Schritt (interner Bereich): Von den Abschnitten <section class="schritt" data-schritt="…" data-wege="…">
// ist immer nur einer zu sehen, mit „Zurück“, „Weiter“ und „Schritt 2 von 4“. Welche Abschnitte zur Aufgabe gehören,
// steht in data-wege; die Aufgabe kommt aus ?aufgabe=… (sonst data-standard am Rahmen). Ein Abschnitt mit
// data-warten lässt „Weiter“ gesperrt, bis die Seite ihn mit Schritte.frei(name) freigibt (zum Beispiel nach dem Öffnen).
(() => {
  "use strict";
  const rahmen = document.querySelector("[data-assistent]");
  if (!rahmen) return;
  const gefragt = new URLSearchParams(location.search).get("aufgabe");
  const alle = [...rahmen.querySelectorAll("section.schritt[data-schritt]")];
  const wege = new Set(alle.flatMap((s) => (s.dataset.wege || "").split(/\s+/).filter(Boolean)));
  const aufgabe = wege.has(gefragt) ? gefragt : rahmen.dataset.standard;
  const schritte = alle.filter((s) => (s.dataset.wege || "").split(/\s+/).includes(aufgabe));
  for (const s of alle) if (!schritte.includes(s)) s.hidden = true;  // bleibt im Dokument, die Seite greift darauf zu
  const frei = new Set(schritte.filter((s) => !("warten" in s.dataset)).map((s) => s.dataset.schritt));

  const anzeige = document.createElement("p");
  anzeige.className = "fortschritt";
  rahmen.prepend(anzeige);
  const nav = document.createElement("nav");
  nav.className = "schritt-nav";
  nav.setAttribute("aria-label", "Schritte");
  nav.innerHTML = '<button type="button" class="knopf" data-zurueck>‹ Zurück</button><button type="button" class="knopf gross" data-weiter>Weiter ›</button>';
  rahmen.append(nav);
  const zurueck = nav.querySelector("[data-zurueck]"), weiter = nav.querySelector("[data-weiter]");
  let jetzt = 0;

  function zeigen(i, fokus = true) {
    jetzt = Math.max(0, Math.min(i, schritte.length - 1));
    schritte.forEach((s, n) => { s.hidden = n !== jetzt; });
    const s = schritte[jetzt], h = s.querySelector("h2");
    anzeige.textContent = schritte.length > 1 ? `Schritt ${jetzt + 1} von ${schritte.length}` : "";
    zurueck.hidden = jetzt === 0;
    weiter.hidden = jetzt === schritte.length - 1;
    weiter.disabled = !frei.has(s.dataset.schritt);
    if (fokus && h) { h.tabIndex = -1; h.focus({ preventScroll: true }); scrollTo({ top: 0 }); }
  }
  zurueck.addEventListener("click", () => zeigen(jetzt - 1));
  weiter.addEventListener("click", () => zeigen(jetzt + 1));

  window.Schritte = {
    aufgabe,
    // Abschnitt erledigt: „Weiter“ wird möglich; mit weiter=true geht es gleich zum nächsten Schritt
    frei(name, weitergehen = false) {
      frei.add(name);
      const i = schritte.findIndex((s) => s.dataset.schritt === name);
      if (weitergehen && i === jetzt) zeigen(jetzt + 1); else zeigen(jetzt, false);
    },
    sperren(name) { frei.delete(name); zeigen(jetzt, false); },
    gehe(name) { const i = schritte.findIndex((s) => s.dataset.schritt === name); if (i >= 0) zeigen(i); },
    get aktuell() { return schritte[jetzt].dataset.schritt; },
  };
  zeigen(0, false);
})();
