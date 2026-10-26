// Frühere 3D-Ansicht: weiter zur Seite „Wohnen und Eigentum“ (2D und 3D), Parameter bleiben erhalten.
(function () {
  "use strict";
  const p = new URLSearchParams(location.search);
  p.set("ansicht", "3d");
  location.replace(`wohnen.html?${p}`);
})();
