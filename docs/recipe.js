// Recipe pages: tick-off ingredients and steps, highlight where an ingredient is
// used, the serving scaler, the phone Ingredients/Method switch, "Add to shopping
// list", and the full-screen step-by-step cooking view with timers and voice.
(function () {
  var page = document.querySelector(".recipe-page");
  if (!page) return;
  var url = page.getAttribute("data-url");
  var entry = (window.FIELD_KITCHEN_INDEX || []).filter(function (r) { return r.url === url; })[0];
  var ingredientsPanel = page.querySelector(".ingredients-panel");
  var methodPanel = page.querySelector(".method-panel");
  var title = page.querySelector(".recipe-hero h1").textContent;

  function stored(key, fallback, area) {
    try { var v = (area || localStorage).getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function store(key, value, area) {
    try { (area || localStorage).setItem(key, JSON.stringify(value)); } catch (e) { /* storage blocked: works for this visit */ }
  }

  // Remember recently opened recipes for the command palette.
  var recent = stored("fk-recent", []).filter(function (u) { return u !== url; });
  recent.unshift(url);
  store("fk-recent", recent.slice(0, 6));

  // ---- Ingredients: tick box + name ----
  var ingredients = [].slice.call(ingredientsPanel.querySelectorAll("ul > li"));
  var parsed = entry && entry.ingredients.length === ingredients.length ? entry.ingredients : [];
  ingredients.forEach(function (li, i) {
    var text = document.createElement("span");
    text.className = "ing-text";
    while (li.firstChild) text.appendChild(li.firstChild);
    var tick = document.createElement("button");
    tick.type = "button";
    tick.className = "tick";
    tick.setAttribute("aria-label", "Got it: " + text.textContent);
    tick.setAttribute("aria-pressed", "false");
    li.appendChild(tick);
    li.appendChild(text);
    li.setAttribute("data-original", text.textContent);
    if (parsed[i] && parsed[i].p) li.setAttribute("data-pattern", parsed[i].p);
    if (parsed[i] && parsed[i].n) li.setAttribute("data-name", parsed[i].n);
  });

  // ---- Method: numbered steps grouped by stage ----
  var steps = [];
  var stage = "";
  [].forEach.call(methodPanel.children, function (el) {
    if (el.tagName === "H5") stage = el.textContent;
    if (el.tagName === "OL") {
      [].forEach.call(el.children, function (li, n) {
        var num = document.createElement("button");
        num.type = "button";
        num.className = "step-num";
        num.textContent = n + 1;
        num.setAttribute("aria-label", "Mark step " + (n + 1) + " done");
        num.setAttribute("aria-pressed", "false");
        var text = document.createElement("div");
        text.className = "step-text";
        while (li.firstChild) text.appendChild(li.firstChild);
        li.appendChild(num);
        li.appendChild(text);
        steps.push({ li: li, stage: stage, n: n + 1, text: text });
      });
    }
    if (el.tagName === "SECTION") stage = "";  // topping options: not part of the main run-through
  });

  // ---- Ticks, kept for this visit ----
  var doneKey = "fk-done:" + url;
  var tickables = ingredients.concat(steps.map(function (s) { return s.li; }));
  function saveTicks() {
    store(doneKey, tickables.map(function (li, i) { return li.classList.contains("done") ? i : -1; })
      .filter(function (i) { return i >= 0; }), sessionStorage);
  }
  function setDone(li, on) {
    li.classList.toggle("done", on);
    var b = li.querySelector(".tick, .step-num");
    if (b) b.setAttribute("aria-pressed", String(on));
  }
  stored(doneKey, [], sessionStorage).forEach(function (i) { if (tickables[i]) setDone(tickables[i], true); });
  tickables.forEach(function (li) {
    li.querySelector(".tick, .step-num").addEventListener("click", function (e) {
      e.stopPropagation();
      setDone(li, !li.classList.contains("done"));
      saveTicks();
    });
  });

  // ---- Where is it used? ----
  function patternOf(li) {
    var p = li.getAttribute("data-pattern");
    return p ? new RegExp(p, "i") : null;
  }
  function stepsUsing(li) {
    var rx = patternOf(li);
    return rx ? steps.filter(function (s) { return rx.test(s.text.textContent); }) : [];
  }
  function ingredientsIn(text) {
    return ingredients.filter(function (li) { var rx = patternOf(li); return rx && rx.test(text); });
  }
  function clearFocus() {
    page.classList.remove("focusing");
    [].forEach.call(page.querySelectorAll(".focus, .uses"), function (el) { el.classList.remove("focus", "uses"); });
    [].forEach.call(page.querySelectorAll(".used-in"), function (el) { el.remove(); });
  }
  // "Curry paste (the day before...)" -> "Curry paste 3"; no stages -> "step 3".
  function stepLabel(s) { return (s.stage ? s.stage.split("(")[0].trim() + " " : "step ") + s.n; }
  ingredients.forEach(function (li) {
    li.querySelector(".ing-text").addEventListener("click", function () {
      var was = li.classList.contains("focus");
      clearFocus();
      if (was) return;
      var used = stepsUsing(li);
      page.classList.add("focusing");
      li.classList.add("focus");
      used.forEach(function (s) { s.li.classList.add("uses"); });
      var note = document.createElement("small");
      note.className = "used-in";
      note.textContent = used.length ? "Used in " + used.map(stepLabel).join(", ") : "Not named in the method";
      li.appendChild(note);
    });
  });
  steps.forEach(function (s) {
    s.text.addEventListener("click", function () {
      var was = s.li.classList.contains("focus");
      clearFocus();
      if (was) return;
      page.classList.add("focusing");
      s.li.classList.add("focus");
      ingredientsIn(s.text.textContent).forEach(function (li) { li.classList.add("uses"); });
    });
  });

  // ---- Serving scaler ----
  var FRACTIONS = { "½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3, "⅛": 0.125 };
  var GLYPHS = [[0.125, "⅛"], [0.25, "¼"], [1 / 3, "⅓"], [0.5, "½"], [2 / 3, "⅔"], [0.75, "¾"]];
  var NUMBER = /(\d+(?:\.\d+)?)?\s?([½¼¾⅓⅔⅛])?/g;
  // Only amounts followed by a unit (or the count at the very start of a line) are
  // scaled; sizes like "5 cm" and counts mid-sentence are left alone.
  var UNIT = /^\s*(?:[–-]\s*[\d.½¼¾⅓⅔⅛]+\s*)?(kg|g|ml|l|litres?|cups?|tbsp|tsp|oz|lb)\b/;
  function value(whole, frac) { return (whole ? parseFloat(whole) : 0) + (frac ? FRACTIONS[frac] : 0); }
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
  var scaler = page.querySelector(".scaler");
  var base = scaler ? parseInt(scaler.getAttribute("data-base"), 10) : 1;
  var serves = base;
  if (scaler) {
    var output = scaler.querySelector("output");
    var down = scaler.querySelector(".scale-down");
    var note = ingredientsPanel.querySelector(".scale-note");
    var apply = function () {
      var ratio = serves / base;
      output.textContent = serves;
      down.disabled = serves <= 1;
      note.hidden = ratio === 1;
      ingredients.forEach(function (li) {
        var original = li.getAttribute("data-original");
        var text = li.querySelector(".ing-text");
        if (ratio === 1) { text.textContent = original; li.classList.remove("scaled"); return; }
        var result = scaleLine(original, ratio);
        text.textContent = result.text;
        li.classList.toggle("scaled", result.changed);
      });
    };
    down.addEventListener("click", function () { if (serves > 1) { serves--; apply(); } });
    scaler.querySelector(".scale-up").addEventListener("click", function () { serves++; apply(); });
  }

  // ---- Phone: Ingredients / Method switch ----
  var tabs = page.querySelector(".recipe-tabs");
  var layout = page.querySelector(".recipe-layout");
  tabs.hidden = false;
  layout.classList.add("tabbed");
  [].forEach.call(tabs.querySelectorAll("[data-tab]"), function (b) {
    b.addEventListener("click", function () {
      layout.setAttribute("data-tab", b.getAttribute("data-tab"));
      [].forEach.call(tabs.querySelectorAll("[data-tab]"), function (x) { x.setAttribute("aria-selected", String(x === b)); });
    });
  });

  // ---- Add to shopping list ----
  var addButton = page.querySelector(".add-to-list");
  if (entry) {
    addButton.hidden = false;
    var label = addButton.lastChild;
    var syncAdd = function () {
      var inList = stored("fk-list", []).some(function (x) { return x.url === url; });
      label.textContent = inList ? "In your shopping list" : "Add to shopping list";
      addButton.classList.toggle("added", inList);
    };
    addButton.addEventListener("click", function () {
      var items = stored("fk-list", []).filter(function (x) { return x.url !== url; });
      if (!addButton.classList.contains("added")) items.push({ url: url, serves: serves });
      store("fk-list", items);
      document.dispatchEvent(new Event("fk-list-changed"));
      syncAdd();
    });
    syncAdd();
  }

  // ---- Timers ----
  var tray = null;
  var timers = [];
  var audio = null;
  function chime() {
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.35, 0.7].forEach(function (t) {
        var o = audio.createOscillator(), g = audio.createGain();
        o.frequency.value = 880; o.connect(g); g.connect(audio.destination);
        g.gain.setValueAtTime(0.0001, audio.currentTime + t);
        g.gain.exponentialRampToValueAtTime(0.3, audio.currentTime + t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + t + 0.3);
        o.start(audio.currentTime + t); o.stop(audio.currentTime + t + 0.32);
      });
    } catch (e) { /* no sound available; the flashing timer still shows */ }
    if (navigator.vibrate) navigator.vibrate([300, 150, 300, 150, 300]);
  }
  function clock(ms) {
    var s = Math.max(0, Math.ceil(ms / 1000)), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
    return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(s % 60).padStart(2, "0");
  }
  function renderTimers() {
    if (!tray) {
      tray = document.createElement("div");
      tray.className = "timer-tray";
      tray.setAttribute("aria-live", "polite");
      document.body.appendChild(tray);
    }
    tray.textContent = "";
    timers.forEach(function (t) {
      var row = document.createElement("div");
      row.className = "timer" + (t.done ? " ringing" : "");
      var name = document.createElement("span"); name.textContent = t.label;
      var time = document.createElement("strong"); time.textContent = t.done ? "Done!" : clock(t.end - Date.now());
      var x = document.createElement("button"); x.type = "button"; x.textContent = t.done ? "OK" : "×";
      x.setAttribute("aria-label", "Dismiss " + t.label + " timer");
      x.addEventListener("click", function () { timers.splice(timers.indexOf(t), 1); renderTimers(); });
      row.appendChild(name); row.appendChild(time); row.appendChild(x);
      tray.appendChild(row);
    });
    tray.hidden = !timers.length;
  }
  setInterval(function () {
    if (!timers.length) return;
    timers.forEach(function (t) {
      if (!t.done && Date.now() >= t.end) { t.done = true; chime(); }
    });
    renderTimers();
  }, 1000);
  function startTimer(minutes, label) {
    timers.push({ label: label, end: Date.now() + minutes * 60000, done: false });
    renderTimers();
  }
  var DURATION = /(\d+(?:\.\d+)?[½¼¾]?|[½¼¾])(?:\s*[–-]\s*(\d+(?:\.\d+)?))?\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|hr)\b/gi;
  function durations(text) {
    var out = [], m;
    DURATION.lastIndex = 0;
    while ((m = DURATION.exec(text))) {
      var raw = m[1], frac = FRACTIONS[raw.slice(-1)] || 0;
      var n = (frac ? (parseFloat(raw.slice(0, -1)) || 0) + frac : parseFloat(raw));
      var unit = m[3].toLowerCase();
      var minutes = /^s/.test(unit) ? n / 60 : /^h/.test(unit) ? n * 60 : n;
      if (minutes > 0) out.push({ minutes: minutes, label: m[0] });
    }
    return out;
  }

  // ---- Step-by-step cooking view ----
  var startButton = page.querySelector(".start-cooking");
  if (!steps.length) return;
  startButton.hidden = false;
  var view = null, at = 0, wakeLock = null, listening = false, recognition = null;
  var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  function speak(text) {
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = "en-AU";
    speechSynthesis.speak(u);
  }
  function lockScreen() {
    if ("wakeLock" in navigator) navigator.wakeLock.request("screen").then(function (l) { wakeLock = l; }).catch(function () {});
  }
  function showStep(i) {
    at = Math.max(0, Math.min(steps.length - 1, i));
    var s = steps[at];
    view.querySelector(".cv-stage").textContent = s.stage;
    view.querySelector(".cv-count").textContent = "Step " + (at + 1) + " of " + steps.length;
    view.querySelector(".cv-bar span").style.width = ((at + 1) / steps.length * 100) + "%";
    var text = view.querySelector(".cv-text");
    text.textContent = s.text.textContent;
    text.classList.remove("enter"); void text.offsetWidth; text.classList.add("enter");
    var uses = view.querySelector(".cv-uses");
    uses.textContent = "";
    ingredientsIn(s.text.textContent).forEach(function (li) {
      var chip = document.createElement("span");
      chip.textContent = li.getAttribute("data-name") || li.querySelector(".ing-text").textContent.split(/,|\(/)[0].trim();
      uses.appendChild(chip);
    });
    uses.hidden = !uses.childNodes.length;
    var timerBox = view.querySelector(".cv-timers");
    timerBox.textContent = "";
    durations(s.text.textContent).forEach(function (d) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "pill pill-outline";
      b.textContent = "⏱ Start " + d.label + " timer";
      b.addEventListener("click", function () { startTimer(d.minutes, (s.stage ? s.stage + ": " : "") + d.label); });
      timerBox.appendChild(b);
    });
    view.querySelector(".cv-prev").disabled = at === 0;
    view.querySelector(".cv-next").textContent = at === steps.length - 1 ? "Finish" : "Next →";
    if (listening) speak(s.text.textContent);
  }
  function next() { if (at === steps.length - 1) closeView(); else showStep(at + 1); }
  function prev() { showStep(at - 1); }
  function setListening(on) {
    listening = on && !!Recognition;
    var b = view && view.querySelector(".cv-voice");
    if (b) b.setAttribute("aria-pressed", String(listening));
    if (listening) {
      recognition = new Recognition();
      recognition.lang = "en-AU";
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.onresult = function (e) {
        var said = e.results[e.results.length - 1][0].transcript.toLowerCase();
        if (/\b(next|done|okay next)\b/.test(said)) next();
        else if (/\b(back|previous|go back)\b/.test(said)) prev();
        else if (/\b(repeat|again|what)\b/.test(said)) speak(steps[at].text.textContent);
        else if (/\btimer\b/.test(said)) { var t = view.querySelector(".cv-timers button"); if (t) t.click(); }
        else if (/\b(stop|close|exit)\b/.test(said)) closeView();
      };
      recognition.onend = function () { if (listening) { try { recognition.start(); } catch (e) {} } };
      try { recognition.start(); } catch (e) { listening = false; }
      speak(steps[at].text.textContent);
    } else if (recognition) {
      recognition.onend = null;
      try { recognition.stop(); } catch (e) {}
      recognition = null;
      if ("speechSynthesis" in window) speechSynthesis.cancel();
    }
  }
  function openView() {
    view = document.createElement("div");
    view.className = "cook-view";
    view.setAttribute("role", "dialog");
    view.setAttribute("aria-modal", "true");
    view.setAttribute("aria-label", "Cooking " + title);
    view.innerHTML =
      '<header class="cv-head"><span class="cv-title"></span>' +
      '<button type="button" class="cv-voice" aria-pressed="false" hidden>🎤 Hands-free</button>' +
      '<button type="button" class="cv-close" aria-label="Close">×</button></header>' +
      '<div class="cv-bar"><span></span></div>' +
      '<div class="cv-body"><p class="cv-stage"></p><p class="cv-count"></p><p class="cv-text" aria-live="polite"></p>' +
      '<div class="cv-uses"></div><div class="cv-timers"></div></div>' +
      '<footer class="cv-foot"><button type="button" class="pill pill-outline cv-prev">← Back</button>' +
      '<p class="cv-hint"></p><button type="button" class="pill pill-solid cv-next">Next →</button></footer>';
    view.querySelector(".cv-title").textContent = title;
    view.querySelector(".cv-hint").textContent = Recognition
      ? "Swipe, use the arrow keys, or turn on hands-free and say “next”, “back”, “repeat” or “timer”."
      : "Swipe or use the arrow keys to move between steps.";
    document.body.appendChild(view);
    document.documentElement.classList.add("cooking");
    var voice = view.querySelector(".cv-voice");
    voice.hidden = !Recognition;
    voice.addEventListener("click", function () { setListening(!listening); });
    view.querySelector(".cv-close").addEventListener("click", closeView);
    view.querySelector(".cv-next").addEventListener("click", next);
    view.querySelector(".cv-prev").addEventListener("click", prev);
    var x0 = null;
    view.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    view.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 60) { if (dx < 0) next(); else prev(); }
      x0 = null;
    });
    lockScreen();
    var firstUndone = steps.findIndex(function (s) { return !s.li.classList.contains("done"); });
    showStep(firstUndone < 0 ? 0 : firstUndone);
    view.querySelector(".cv-next").focus();
  }
  function closeView() {
    if (!view) return;
    // Steps you've moved past count as done on the page.
    steps.slice(0, at).forEach(function (s) { setDone(s.li, true); });
    saveTicks();
    setListening(false);
    view.remove(); view = null;
    document.documentElement.classList.remove("cooking");
    if (wakeLock) { wakeLock.release(); wakeLock = null; }
    startButton.focus();
  }
  startButton.addEventListener("click", openView);
  document.addEventListener("keydown", function (e) {
    if (!view) return;
    if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); next(); }
    if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
    if (e.key === "Escape") closeView();
  });
  // The browser drops the wake lock when the tab is hidden; take it back on return.
  document.addEventListener("visibilitychange", function () {
    if (view && document.visibilityState === "visible") lockScreen();
  });
})();
