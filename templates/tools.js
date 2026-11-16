// The shopping list and "What can I cook?" pages. Both read the parsed ingredients
// in search-index.js (see ingredients.py): each line's shopping name, aisle,
// amount and unit. Lists and pantry picks are kept in this browser only.
(function () {
  var index = window.FIELD_KITCHEN_INDEX || [];
  // Supermarket sections in walking order, and the rules that sort a typed item into one
  // (from ingredients.py, via search-index.js).
  var SHOP = window.FIELD_KITCHEN_SHOP || { aisles: ["Other"], ingredients: [], groceries: [] };
  var AISLES = SHOP.aisles;
  var RULES = SHOP.ingredients.map(function (r) { return [new RegExp(r[0], "i"), r[1], r[2], r[3]]; });
  var HINTS = SHOP.groceries.map(function (r) { return [new RegExp(r[0], "i"), r[1]]; });
  // "garlic" -> the recipes' own Garlic, so it merges with them; "ravioli" -> Dairy & fridge;
  // anything unknown -> Other, under the name as typed.
  function sortItem(text) {
    var name = text.trim().replace(/\s+/g, " ");
    name = name.charAt(0).toUpperCase() + name.slice(1);
    for (var i = 0; i < RULES.length; i++) {
      if (RULES[i][0].test(name)) return { name: RULES[i][1], aisle: RULES[i][2], staple: RULES[i][3] };
    }
    for (var j = 0; j < HINTS.length; j++) {
      if (HINTS[j][0].test(name)) return { name: name, aisle: HINTS[j][1], staple: false };
    }
    return { name: name, aisle: AISLES[AISLES.length - 1], staple: false };
  }
  var GLYPHS = [[0.125, "⅛"], [0.25, "¼"], [1 / 3, "⅓"], [0.5, "½"], [2 / 3, "⅔"], [0.75, "¾"]];

  function stored(key, fallback) {
    try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function store(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* works for this visit only */ }
    document.dispatchEvent(new Event("fk-list-changed"));
  }
  function byUrl(url) { return index.filter(function (r) { return r.url === url; })[0]; }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function frac(n) {
    var whole = Math.floor(n), rest = n - whole, best = null, gap = 0.1;
    GLYPHS.forEach(function (g) { if (Math.abs(rest - g[0]) < gap) { best = g; gap = Math.abs(rest - g[0]); } });
    if (rest < 0.07) return String(whole);
    if (rest > 0.93) return String(whole + 1);
    return best ? (whole || "") + best[1] : String(Math.round(n * 10) / 10);
  }
  function metric(q) { return q >= 100 ? Math.round(q / 5) * 5 : Math.round(q); }
  // One amount in a friendly unit: 1500 g -> 1.5 kg, 9 tsp -> 3 tbsp. Whole items
  // (eggs, onions, cloves) round up, since you can't buy a third of an egg.
  function amount(q, u) {
    if (u === "g") return q >= 1000 ? Math.round(q / 100) / 10 + " kg" : metric(q) + " g";
    if (u === "ml") return q >= 1000 ? Math.round(q / 100) / 10 + " l" : metric(q) + " ml";
    if (u === "tsp") return q >= 3 && Math.abs(q / 3 - Math.round(q / 1.5) / 2) < 0.01 ? frac(q / 3) + " tbsp" : frac(q) + " tsp";
    if (u === "cm") return Math.ceil(q) + " cm";
    var whole = q > 1 ? Math.ceil(q - 0.05) : 0;
    return (whole ? String(whole) : frac(q)) + (u ? " " + (whole > 1 ? u : u.replace(/s$/, "")) : "");
  }

  // ---- Shopping list ----
  var aislesBox = document.querySelector(".list-aisles");
  if (aislesBox) {
    var recipesBox = document.querySelector(".list-recipes");
    var empty = document.querySelector(".list-empty");
    var actions = document.querySelector(".list-actions");
    var summary = document.querySelector(".list-summary");
    var lines = [];

    var build = function () {
      var picked = stored("fk-list", []).filter(function (x) { return byUrl(x.url); });
      var extras = stored("fk-list-extra", []);
      var checked = stored("fk-list-checked", {});
      recipesBox.textContent = ""; aislesBox.textContent = ""; lines = [];
      var anything = picked.length > 0 || extras.length > 0;
      empty.hidden = anything;
      actions.hidden = !anything;
      if (!anything) { summary.textContent = "One list for everything you plan to cook."; ideas(); return; }

      // Recipes on the list: one compact card, a row per recipe with its servings and toppings.
      if (picked.length) recipesBox.appendChild(el("h2", "", "For " + picked.length + " recipe" + (picked.length === 1 ? "" : "s")));
      picked.forEach(function (x) {
        var r = byUrl(x.url);
        var chip = el("div", "list-recipe");
        var head = el("div", "list-recipe-head");
        var a = el("a", "", r.title); a.href = r.url;
        head.appendChild(a);
        head.appendChild(el("span", "", "Serves " + x.serves));
        var s = el("div", "list-recipe-opts", (x.options || []).length ? "+ " + x.options.join(", ") : "");
        var rm = el("button", "", "×"); rm.type = "button"; rm.setAttribute("aria-label", "Remove " + r.title);
        rm.addEventListener("click", function () {
          store("fk-list", stored("fk-list", []).filter(function (y) { return y.url !== x.url; }));
          build();
        });
        var body = el("div", "list-recipe-body");
        body.appendChild(head);
        if (s.textContent) body.appendChild(s);
        chip.appendChild(body); chip.appendChild(rm);
        recipesBox.appendChild(chip);
      });

      // Merge every ingredient line by shopping name, then by unit.
      var items = {};
      picked.forEach(function (x) {
        var r = byUrl(x.url), ratio = x.serves / (r.serves || 1);
        // The recipe's own lines, plus those of any topping options picked on its page.
        var wanted = r.ingredients.slice();
        (r.options || []).forEach(function (o) {
          if ((x.options || []).indexOf(o.name) !== -1) wanted = wanted.concat(o.ingredients);
        });
        wanted.forEach(function (ing) {
          if (!ing.n || ing.n === "Water") return;
          var it = items[ing.n] || (items[ing.n] = { name: ing.n, aisle: ing.a, staple: ing.s, units: {}, some: false, from: [] });
          if (ing.q === null) it.some = true;
          else {
            // "1 clove" and "4 cloves" are the same unit.
            var unit = (ing.u || "").replace(/^(clove|stick|sprig|piece|stalk|rasher)$/, "$1s");
            it.units[unit] = (it.units[unit] || 0) + ing.q * ratio;
          }
          if (it.from.indexOf(r.title) === -1) it.from.push(r.title);
        });
      });
      // Things typed straight onto the list join the same sections (and merge with a recipe's
      // line of the same name, so "garlic" doesn't appear twice).
      extras.forEach(function (x) {
        var sorted = sortItem(x);
        var it = items[sorted.name] || (items[sorted.name] = { name: sorted.name, aisle: sorted.aisle, staple: sorted.staple, units: {}, some: false, from: [] });
        it.extra = true;
        it.some = it.some || !Object.keys(it.units).length;
        if (it.from.indexOf("Added by you") === -1) it.from.push("Added by you");
      });
      // Items removed from the list (already in the cupboard, or not wanted) stay hidden
      // until the list is cleared; ticked items drop into "In the trolley" at the bottom.
      var removed = stored("fk-list-removed", {});
      var all = Object.keys(items).map(function (k) { return items[k]; }).filter(function (it) { return !removed[it.name]; });
      var toBuy = all.filter(function (it) { return !checked[it.name]; });
      var got = all.filter(function (it) { return checked[it.name]; });
      var groups = AISLES.map(function (a) {
        return { name: a, items: toBuy.filter(function (it) { return it.aisle === a && !it.staple; }) };
      });
      groups.push({ name: "Pantry staples: check you have", items: toBuy.filter(function (it) { return it.staple; }) });
      groups.push({ name: "In the trolley", items: got, done: true });
      var setChecked = function (name, on) {
        var c = stored("fk-list-checked", {});
        if (on) c[name] = true; else delete c[name];
        store("fk-list-checked", c);
        build();
      };
      var remove = function (name) {
        // A typed item is simply deleted; a recipe's item is hidden until "Show removed items".
        var kept = stored("fk-list-extra", []).filter(function (x) { return sortItem(x).name !== name; });
        if (kept.length !== stored("fk-list-extra", []).length) {
          store("fk-list-extra", kept);
          if (!items[name].from.some(function (f) { return f !== "Added by you"; })) { build(); return; }
        }
        var r = stored("fk-list-removed", {});
        r[name] = true;
        store("fk-list-removed", r);
        build();
      };
      groups.forEach(function (g) {
        if (!g.items.length) return;
        g.items.sort(function (a, b) { return a.name.localeCompare(b.name); });
        var section = el("section", "aisle" + (g.done ? " aisle-done" : ""));
        section.appendChild(el("h2", "", g.done ? g.name + " (" + g.items.length + ")" : g.name));
        var ul = el("ul");
        g.items.forEach(function (it) {
          var amounts = Object.keys(it.units).map(function (u) { return amount(it.units[u], u); });
          if (it.some && amounts.length) amounts.push("plus some");
          var on = !!checked[it.name];
          var li = el("li", on ? "done" : "");
          var tick = el("button", "tick"); tick.type = "button";
          tick.setAttribute("aria-pressed", String(on));
          tick.setAttribute("aria-label", (on ? "Put back: " : "Got ") + it.name);
          var body = el("div");
          body.appendChild(el("strong", "", it.name));
          if (amounts.length) body.appendChild(el("span", "amount", amounts.join(" + ")));
          var recipes = it.from.filter(function (f) { return f !== "Added by you"; });
          body.appendChild(el("small", "", (recipes.length ? "For " + recipes.join(", ") : "") +
            (it.extra ? (recipes.length ? " · added by you" : "Added by you") : "")));
          var rm = el("button", "list-remove", "×"); rm.type = "button";
          rm.setAttribute("aria-label", "Remove " + it.name + " from the list");
          rm.title = "Remove from the list";
          tick.addEventListener("click", function () { setChecked(it.name, !on); });
          rm.addEventListener("click", function () { remove(it.name); });
          li.appendChild(tick); li.appendChild(body); li.appendChild(rm);
          ul.appendChild(li);
        });
        section.appendChild(ul);
        aislesBox.appendChild(section);
      });
      // Shared or copied lists: still to buy first, then what's already in the trolley.
      toBuy.concat(got).forEach(function (it) {
        var amounts = Object.keys(it.units).map(function (u) { return amount(it.units[u], u); });
        lines.push((checked[it.name] ? "✓ " : "▢ ") + it.name + (amounts.length ? ": " + amounts.join(" + ") : ""));
      });
      var hiddenCount = Object.keys(items).length - all.length;
      summary.textContent = (toBuy.length ? toBuy.length + " to buy" : "Everything's in the trolley") +
        (got.length ? " · " + got.length + " in the trolley" : "");
      restore.hidden = !hiddenCount;
      restore.textContent = "Show " + hiddenCount + " removed item" + (hiddenCount === 1 ? "" : "s");
    };

    // Empty list: offer a few recipes to start from (favourites first, then a random pick).
    var ideas = function () {
      var box = document.querySelector(".list-ideas"), ul = box.querySelector("ul");
      var pool = stored("fk-favs", []).map(byUrl).filter(Boolean);
      var rest = index.filter(function (r) { return pool.indexOf(r) === -1; });
      while (pool.length < 3 && rest.length) pool.push(rest.splice(Math.floor(Math.random() * rest.length), 1)[0]);
      ul.textContent = "";
      pool.slice(0, 3).forEach(function (r) {
        var li = el("li"), text = el("div"), a = el("a", "", r.title);
        a.href = r.url;
        text.appendChild(a);
        text.appendChild(el("span", "", r.cuisine + " · " + r.category));
        var add = el("button", "pill pill-outline pill-sm", "+ Add");
        add.type = "button";
        add.setAttribute("aria-label", "Add " + r.title + " to the shopping list");
        add.addEventListener("click", function () {
          store("fk-list", stored("fk-list", []).concat([{ url: r.url, serves: r.serves }]));
          build();
        });
        li.appendChild(text); li.appendChild(add);
        ul.appendChild(li);
      });
      box.hidden = !pool.length;
    };

    // The rarely used actions live behind "…".
    var more = document.querySelector(".list-more");
    var moreToggle = more.querySelector(".list-more-toggle"), moreMenu = more.querySelector(".list-more-menu");
    var setMore = function (open) { moreMenu.hidden = !open; moreToggle.setAttribute("aria-expanded", String(open)); };
    moreToggle.addEventListener("click", function () { setMore(moreMenu.hidden); });
    document.addEventListener("click", function (e) { if (!more.contains(e.target)) setMore(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMore(false); });
    var restore = document.querySelector(".list-restore");
    restore.addEventListener("click", function () { setMore(false); store("fk-list-removed", {}); build(); });
    document.querySelector(".list-clear").addEventListener("click", function () {
      setMore(false);
      if (!window.confirm("Clear the whole shopping list?")) return;
      store("fk-list", []); store("fk-list-checked", {}); store("fk-list-removed", {}); store("fk-list-extra", []); build();
    });
    // Add anything else to the list: it's sorted into its section as you add it, with
    // suggestions as you type (what you've added before, every ingredient in the book, and
    // everyday groceries).
    var addForm = document.querySelector(".list-add");
    var addInput = addForm.querySelector("input");
    var suggestBox = addForm.querySelector(".list-suggest");
    addForm.hidden = false;
    var known = [];
    (function () {
      var seen = {};
      SHOP.ingredients.forEach(function (r) { if (!r[3] && !seen[r[1]]) { seen[r[1]] = 1; known.push(r[1]); } });
      (SHOP.suggestions || []).forEach(function (n) { if (!seen[n]) { seen[n] = 1; known.push(n); } });
    })();
    var addItem = function (text) {
      text = text.trim();
      if (!text) return;
      var extras = stored("fk-list-extra", []);
      var name = sortItem(text).name;
      if (!extras.some(function (x) { return sortItem(x).name === name; })) extras.push(text);
      store("fk-list-extra", extras);
      // Remember it, most recent first, so it's suggested first next time.
      var history = stored("fk-list-history", []).filter(function (h) { return h.toLowerCase() !== text.toLowerCase(); });
      history.unshift(text.charAt(0).toUpperCase() + text.slice(1));
      store("fk-list-history", history.slice(0, 30));
      // Adding something back undoes an earlier "remove" of it.
      var removed = stored("fk-list-removed", {}); delete removed[name]; store("fk-list-removed", removed);
      addInput.value = "";
      closeSuggest();
      build();
      addInput.focus();
    };
    var active = -1, shown = [];
    var closeSuggest = function () {
      suggestBox.hidden = true; suggestBox.textContent = ""; shown = []; active = -1;
      addInput.setAttribute("aria-expanded", "false"); addInput.removeAttribute("aria-activedescendant");
    };
    var setActive = function (i) {
      active = i;
      [].forEach.call(suggestBox.children, function (li, k) { li.setAttribute("aria-selected", String(k === i)); });
      if (i >= 0) addInput.setAttribute("aria-activedescendant", "suggest-" + i); else addInput.removeAttribute("aria-activedescendant");
    };
    var suggest = function () {
      var q = addInput.value.trim().toLowerCase();
      var onList = {};
      stored("fk-list-extra", []).forEach(function (x) { onList[sortItem(x).name.toLowerCase()] = 1; });
      var history = stored("fk-list-history", []);
      var pool = history.concat(known.filter(function (n) {
        return !history.some(function (h) { return h.toLowerCase() === n.toLowerCase(); });
      })).filter(function (n) { return !onList[sortItem(n).name.toLowerCase()]; });
      // Empty box: just what you've added before. Typing: names starting with it, then containing it.
      shown = !q ? history.filter(function (n) { return !onList[sortItem(n).name.toLowerCase()]; }).slice(0, 6)
        : pool.filter(function (n) { return n.toLowerCase().indexOf(q) === 0; })
            .concat(pool.filter(function (n) { var i = n.toLowerCase().indexOf(q); return i > 0; })).slice(0, 6);
      suggestBox.textContent = "";
      if (!shown.length) { closeSuggest(); return; }
      shown.forEach(function (n, i) {
        var li = el("li");
        li.id = "suggest-" + i;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", "false");
        li.appendChild(el("span", "", n));
        li.appendChild(el("small", "", sortItem(n).aisle));
        // pointerdown, so the tap lands before the box loses focus.
        li.addEventListener("pointerdown", function (e) { e.preventDefault(); addItem(n); });
        suggestBox.appendChild(li);
      });
      suggestBox.hidden = false;
      addInput.setAttribute("aria-expanded", "true");
      setActive(-1);
    };
    addInput.addEventListener("input", suggest);
    addInput.addEventListener("focus", suggest);
    addInput.addEventListener("blur", function () { setTimeout(closeSuggest, 100); });
    addInput.addEventListener("keydown", function (e) {
      if (suggestBox.hidden) return;
      if (e.key === "ArrowDown") { e.preventDefault(); setActive(Math.min(active + 1, shown.length - 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setActive(Math.max(active - 1, -1)); }
      if (e.key === "Escape") closeSuggest();
    });
    addForm.addEventListener("submit", function (e) {
      e.preventDefault();
      addItem(active >= 0 ? shown[active] : addInput.value);
    });
    build();
  }

  // ---- What can I cook? ----
  var pantry = document.querySelector(".pantry");
  if (pantry) {
    var chips = [].slice.call(pantry.querySelectorAll("[data-ingredient]"));
    var groups = [].slice.call(pantry.querySelectorAll(".pantry-group"));
    var search = pantry.querySelector(".pantry-search");
    var query = search.querySelector("input");
    var noneFound = pantry.querySelector(".pantry-none");
    var picks = document.querySelector(".picks");
    var jump = document.querySelector(".matches-jump");
    var matchList = document.querySelector(".match-list");
    var none = document.querySelector(".matches-empty");
    var have = stored("fk-fridge", []);
    var opened = [];
    search.hidden = false;

    // Only the common ingredients show until an aisle is opened or searched; anything
    // already picked always stays in view so it can be unticked.
    var show = function () {
      var q = query.value.trim().toLowerCase(), any = false;
      groups.forEach(function (g, gi) {
        var more = g.querySelector(".pantry-more"), tucked = 0, shown = 0;
        [].forEach.call(g.querySelectorAll("[data-ingredient]"), function (c) {
          var name = c.getAttribute("data-ingredient");
          var visible = q ? name.toLowerCase().indexOf(q) !== -1
            : !c.classList.contains("rare") || opened.indexOf(gi) !== -1 || have.indexOf(name) !== -1;
          if (!q && c.classList.contains("rare") && have.indexOf(name) === -1) tucked++;
          c.hidden = !visible;
          if (visible) shown++;
        });
        g.hidden = !shown;
        any = any || shown > 0;
        more.hidden = !!q || !tucked;
        more.textContent = opened.indexOf(gi) !== -1 ? "Show fewer" : "+" + tucked + " more";
      });
      noneFound.hidden = any;
    };

    var rank = function () {
      store("fk-fridge", have);
      document.querySelector(".pantry-clear").hidden = !have.length;  // nothing to clear yet
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(have.indexOf(c.getAttribute("data-ingredient")) !== -1)); });
      show();
      picks.textContent = "";
      picks.hidden = !have.length;
      have.forEach(function (name) {
        var b = el("button", "chip", name + " ×");
        b.type = "button"; b.setAttribute("aria-label", "Remove " + name);
        b.addEventListener("click", function () { toggle(name); });
        picks.appendChild(b);
      });
      matchList.textContent = "";
      jump.hidden = true;
      if (!have.length) { none.hidden = false; none.textContent = "Pick a few ingredients to see what you can make."; return; }
      var results = index.map(function (r) {
        var need = [];
        r.ingredients.forEach(function (i) { if (i.n && !i.s && need.indexOf(i.n) === -1) need.push(i.n); });
        var got = need.filter(function (n) { return have.indexOf(n) !== -1; });
        var missing = need.filter(function (n) { return have.indexOf(n) === -1; });
        return { r: r, got: got, missing: missing, score: need.length ? got.length / need.length : 0 };
      }).filter(function (m) { return m.got.length; })
        // Closest to cookable first: the biggest share of the recipe already in hand.
        .sort(function (a, b) { return b.score - a.score || b.got.length - a.got.length || a.missing.length - b.missing.length; })
        .slice(0, 12);
      none.hidden = results.length > 0;
      if (!results.length) none.textContent = "Nothing uses those yet. Try adding a few more.";
      jump.hidden = !results.length;
      jump.textContent = "See " + results.length + (results.length === 1 ? " match" : " matches");
      results.forEach(function (m) {
        var li = el("li", "match");
        var a = el("a", "", m.r.title); a.href = m.r.url;
        var where = el("span", "match-where", m.r.cuisine + " · " + m.r.category);
        var bar = el("div", "match-bar"); var fill = el("span"); fill.style.width = Math.round(m.score * 100) + "%"; bar.appendChild(fill);
        var detail = el("p", "match-detail", m.missing.length
          ? "You have " + m.got.length + " of " + (m.got.length + m.missing.length) + ". Missing: " + m.missing.join(", ")
          : "You have everything!");
        li.appendChild(a); li.appendChild(where); li.appendChild(bar); li.appendChild(detail);
        matchList.appendChild(li);
      });
    };
    var toggle = function (name) {
      var i = have.indexOf(name);
      if (i === -1) have.push(name); else have.splice(i, 1);
      rank();
    };
    chips.forEach(function (c) {
      c.addEventListener("click", function () { toggle(c.getAttribute("data-ingredient")); });
    });
    groups.forEach(function (g, gi) {
      g.querySelector(".pantry-more").addEventListener("click", function () {
        var i = opened.indexOf(gi);
        if (i === -1) opened.push(gi); else opened.splice(i, 1);
        show();
      });
    });
    query.addEventListener("input", show);
    if ("IntersectionObserver" in window) {
      // No need for the shortcut once the matches themselves are on screen.
      new IntersectionObserver(function (entries) {
        jump.classList.toggle("away", entries[0].isIntersecting);
      }).observe(document.querySelector(".matches"));
    }
    query.addEventListener("keydown", function (e) {
      // Enter picks the only (or first) ingredient found, then clears the box for the next.
      if (e.key !== "Enter") return;
      e.preventDefault();
      var first = chips.filter(function (c) { return !c.hidden; })[0];
      if (first && query.value.trim()) { toggle(first.getAttribute("data-ingredient")); query.value = ""; show(); }
    });
    document.querySelector(".pantry-clear").addEventListener("click", function () { have = []; query.value = ""; rank(); });
    rank();
  }
})();
