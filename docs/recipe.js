// Recipe page tools: the serving scaler and cook mode (screen kept awake,
// larger text, tap ingredients and steps to tick them off).
(function () {
  var article = document.querySelector(".recipe.solo");
  var tools = article && article.querySelector(".recipe-tools");
  if (!tools) return;
  tools.hidden = false;

  // Items under a ## heading (h4) up to the next one.
  function itemsAfter(cls) {
    var h = article.querySelector("h4." + cls);
    var out = [];
    for (var el = h && h.nextElementSibling; el && el.tagName !== "H4"; el = el.nextElementSibling) {
      if (el.tagName === "UL" || el.tagName === "OL") out = out.concat([].slice.call(el.children));
    }
    return out;
  }
  var ingredients = itemsAfter("part-ingredients");
  var steps = itemsAfter("part-method").concat(itemsAfter("part-topping-options"));

  // ---- Serving scaler ----
  var FRACTIONS = { "½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3, "⅛": 0.125 };
  var GLYPHS = [[0.125, "⅛"], [0.25, "¼"], [1 / 3, "⅓"], [0.5, "½"], [2 / 3, "⅔"], [0.75, "¾"]];
  var NUMBER = /(\d+(?:\.\d+)?)?\s?([½¼¾⅓⅔⅛])?/g;
  // Only amounts followed by a unit (or the count at the very start of a line) are
  // scaled; sizes like "5 cm" and counts mid-sentence are left alone.
  var UNIT = /^\s*(?:[–-]\s*[\d.½¼¾⅓⅔⅛]+\s*)?(kg|g|ml|l|litres?|cups?|tbsp|tsp|oz|lb)\b/;

  function value(whole, frac) {
    return (whole ? parseFloat(whole) : 0) + (frac ? FRACTIONS[frac] : 0);
  }
  function friendly(n) {
    var whole = Math.floor(n), rest = n - whole, best = null, bestGap = 0.1;
    GLYPHS.forEach(function (g) { var gap = Math.abs(rest - g[0]); if (gap < bestGap) { best = g; bestGap = gap; } });
    if (rest < 0.07) return String(whole || GLYPHS[0][1]);
    if (rest > 0.93) return String(whole + 1);
    if (!best) return String(Math.round(n * 10) / 10);
    return (whole ? whole : "") + best[1];
  }
  function format(n, unit) {
    if (unit === "g" || unit === "ml") {
      if (n >= 100) return String(Math.round(n / 5) * 5);
      if (n >= 10) return String(Math.round(n));
      return String(Math.round(n * 10) / 10);
    }
    if (unit === "kg" || unit === "l" || /^litre/.test(unit || "")) return String(Math.round(n * 100) / 100);
    return friendly(n);
  }
  function scaleLine(text, ratio) {
    var changed = false;
    // A line that opens with a bare count ("1 whole chicken, about 1.5 kg") scales the
    // count only: later weights describe the size of each one.
    var countOnly = false;
    var out = text.replace(NUMBER, function (match, whole, frac, offset) {
      if (!whole && !frac) return match;
      var unit = UNIT.exec(text.slice(offset + match.length));
      if (offset === 0 && !unit) countOnly = true;
      else if (countOnly || !unit) return match;
      changed = true;
      var trailing = /\s$/.test(match) ? " " : "";
      return format(value(whole, frac) * ratio, unit && unit[1]) + trailing;
    });
    // "(1 cup)" doubled should read "(2 cups)".
    out = out.replace(/(^|[^\d.])((?:[2-9]|\d{2,})[½¼¾⅓⅔⅛]?|1[½¼¾⅓⅔⅛]) cup\b/g, "$1$2 cups");
    return { text: out, changed: changed };
  }

  var scaler = tools.querySelector(".scaler");
  var note = article.querySelector(".scale-note");
  if (scaler) {
    var base = parseInt(scaler.getAttribute("data-base"), 10);
    var serves = base;
    var output = scaler.querySelector("output");
    var down = scaler.querySelector(".scale-down");
    ingredients.forEach(function (li) { li.setAttribute("data-original", li.textContent); });
    var apply = function () {
      var ratio = serves / base;
      output.textContent = serves;
      down.disabled = serves <= 1;
      note.hidden = ratio === 1;
      ingredients.forEach(function (li) {
        var original = li.getAttribute("data-original");
        if (ratio === 1) { li.textContent = original; li.classList.remove("scaled"); return; }
        var result = scaleLine(original, ratio);
        li.textContent = result.text;
        li.classList.toggle("scaled", result.changed);
      });
    };
    down.addEventListener("click", function () { if (serves > 1) { serves--; apply(); } });
    scaler.querySelector(".scale-up").addEventListener("click", function () { serves++; apply(); });
  }

  // ---- Cook mode ----
  var toggle = tools.querySelector(".cook-toggle");
  var key = "fk-done:" + location.pathname;
  var wakeLock = null;
  var bar = null;
  var all = ingredients.concat(steps);
  all.forEach(function (li) { li.classList.add("tickable"); });

  function saved() {
    try { return JSON.parse(sessionStorage.getItem(key) || "[]"); } catch (e) { return []; }
  }
  function save() {
    var done = all.map(function (li, i) { return li.classList.contains("done") ? i : -1; })
      .filter(function (i) { return i >= 0; });
    try { sessionStorage.setItem(key, JSON.stringify(done)); } catch (e) { /* private mode: ticks just won't persist */ }
  }
  function lockScreen() {
    if (!("wakeLock" in navigator)) return Promise.resolve(false);
    return navigator.wakeLock.request("screen").then(function (lock) { wakeLock = lock; return true; })
      .catch(function () { return false; });
  }
  function setCooking(on) {
    document.documentElement.classList.toggle("cook-mode", on);
    toggle.setAttribute("aria-pressed", String(on));
    if (on) {
      saved().forEach(function (i) { if (all[i]) all[i].classList.add("done"); });
      bar = document.createElement("div");
      bar.className = "cook-bar";
      bar.setAttribute("role", "status");
      var label = document.createElement("span");
      label.textContent = "Cook mode: tap items to tick them off";
      var exit = document.createElement("button");
      exit.type = "button";
      exit.textContent = "Done";
      exit.addEventListener("click", function () { setCooking(false); });
      bar.appendChild(label);
      bar.appendChild(exit);
      document.body.appendChild(bar);
      lockScreen().then(function (ok) {
        label.textContent = ok ? "Cook mode: screen stays on, tap items to tick them off"
                               : "Cook mode: tap items to tick them off";
      });
    } else {
      if (bar) { bar.remove(); bar = null; }
      if (wakeLock) { wakeLock.release(); wakeLock = null; }
    }
  }
  toggle.addEventListener("click", function () { setCooking(!document.documentElement.classList.contains("cook-mode")); });
  all.forEach(function (li) {
    li.addEventListener("click", function () {
      if (!document.documentElement.classList.contains("cook-mode")) return;
      li.classList.toggle("done");
      save();
    });
  });
  // The browser drops the wake lock when the tab is hidden; take it back on return.
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible" && document.documentElement.classList.contains("cook-mode")) lockScreen();
  });
})();
