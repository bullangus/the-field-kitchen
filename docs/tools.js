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
      if (window.FieldKitchenNames) { FieldKitchenNames.swap(aislesBox, true); FieldKitchenNames.swap(recipesBox, true); }
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
    // everyday groceries). Typing a basic or recipe offers the whole meal, which goes on
    // as a recipe card with all its ingredients.
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
    var mealNamed = function (text) {
      var t = text.trim().toLowerCase();
      return index.filter(function (r) { return r.title.toLowerCase() === t; })[0];
    };
    var addMeal = function (r) {
      var list = stored("fk-list", []).filter(function (x) { return x.url !== r.url; });
      list.push({ url: r.url, serves: r.serves });
      store("fk-list", list);
      addInput.value = "";
      closeSuggest();
      build();
      addInput.focus();
    };
    var addItem = function (text) {
      text = text.trim();
      if (!text) return;
      var meal = mealNamed(text);
      if (meal) { addMeal(meal); return; }
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
      var items = !q ? history.filter(function (n) { return !onList[sortItem(n).name.toLowerCase()]; }).slice(0, 6)
        : pool.filter(function (n) { return n.toLowerCase().indexOf(q) === 0; })
            .concat(pool.filter(function (n) { var i = n.toLowerCase().indexOf(q); return i > 0; })).slice(0, 6);
      // Meals first (basics before recipes), from two letters typed, then single items.
      var listed = stored("fk-list", []).map(function (x) { return x.url; });
      var meals = q.length < 2 ? [] : index.filter(function (r) {
        return r.meal && listed.indexOf(r.url) === -1 && r.title.toLowerCase().indexOf(q) !== -1;
      }).sort(function (a, b) { return (b.basic ? 1 : 0) - (a.basic ? 1 : 0) || a.title.localeCompare(b.title); }).slice(0, 3);
      shown = meals.map(function (r) { return { meal: r }; }).concat(items.map(function (n) { return { item: n }; })).slice(0, 7);
      suggestBox.textContent = "";
      if (!shown.length) { closeSuggest(); return; }
      shown.forEach(function (o, i) {
        var li = el("li");
        li.id = "suggest-" + i;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", "false");
        li.appendChild(el("span", "", o.meal ? o.meal.title : o.item));
        li.appendChild(el("small", "", o.meal ? (o.meal.basic ? "Basic" : "Recipe") + " · " + o.meal.ingredients.filter(function (x) { return x.n && !x.s; }).length + " items" : sortItem(o.item).aisle));
        // pointerdown, so the tap lands before the box loses focus.
        li.addEventListener("pointerdown", function (e) { e.preventDefault(); pick(o); });
        suggestBox.appendChild(li);
      });
      if (window.FieldKitchenNames) FieldKitchenNames.swap(suggestBox, true);
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
    var pick = function (o) { if (o.meal) addMeal(o.meal); else addItem(o.item); };
    addForm.addEventListener("submit", function (e) {
      e.preventDefault();
      if (active >= 0) pick(shown[active]); else addItem(addInput.value);
    });
    build();
  }

  // ---- Week plans ----
  // Ready-made plans come from the build; "Build your own" fills the nights around the
  // dinners you're craving with the same rules (FIELD_KITCHEN_SHOP.plan). Leaving out
  // ingredients reworks the ready-made plans here in the browser with those rules too. Any
  // plan goes on the shopping list at the household size, with extra of its lunch dinners
  // if asked, and shows what sharing its fresh food saves in the reader's country.
  var plans = document.querySelector(".plans");
  if (plans) {
    var RULES = SHOP.plan || {};
    var size = RULES.size || 5;
    var people = stored("fk-people", 4);
    var extra = stored("fk-lunches", false);
    var avoid = stored("fk-avoid", { groups: [], items: [] });
    // What's ticked on "What can I cook?": already in the kitchen, so plans that use it cost less.
    var have = stored("fk-fridge", []);
    var peopleBox = document.querySelector(".plan-people");
    var sizeChips = [].slice.call(peopleBox.querySelectorAll("[data-people]"));
    var extraBox = peopleBox.querySelector(".plan-extra input");
    var serverCards = [].slice.call(plans.querySelectorAll(".plan"));
    var boxIcon = plans.querySelector(".plan-leftovers svg"), plusIcon = plans.querySelector(".plan-add svg");
    var cards = [];
    var joinAnd = function (a) { return a.length === 1 ? a[0] : a.slice(0, -1).join(", ") + " and " + a[a.length - 1]; };
    var urlsOf = function (card, attr) { return JSON.parse(card.getAttribute(attr || "data-urls")); };

    // -- Leaving things out --
    var avoidRules = (RULES.avoid || []).map(function (a) {
      return { label: a[0], tag: a[1].charAt(0) === "#" ? a[1].slice(1) : null, rx: a[1].charAt(0) === "#" ? null : new RegExp(a[1], "i") };
    });
    // A diet keeps only the dinners that fit it (DIETS in ingredients.py): tagged for it,
    // with none of its ruled-out ingredients, and never meat with dairy where that applies.
    var DIETS = {};
    (RULES.diets || []).forEach(function (d) {
      DIETS[d[0]] = { tags: d[1].tags, none: d[1].none && new RegExp(d[1].none, "i"),
        apart: d[1].apart && d[1].apart.map(function (p) { return new RegExp(p, "i"); }) };
    });
    var fitsDiet = function (r) {
      var d = DIETS[avoid.diet]; if (!d) return true;
      var names = r.ingredients.map(function (i) { return i.n || ""; }).filter(Boolean);
      var has = function (rx) { return names.some(function (n) { return rx.test(n); }); };
      if (d.tags && !d.tags.some(function (t) { return r.tags.indexOf(t) !== -1; })) return false;
      if (d.none && has(d.none)) return false;
      return !(d.apart && d.apart.every(has));
    };
    var allowed = function (r) {
      if (!fitsDiet(r)) return false;
      var rules = avoidRules.filter(function (a) { return avoid.groups.indexOf(a.label) !== -1; });
      if (rules.some(function (a) { return a.tag && r.tags.indexOf(a.tag) !== -1; })) return false;
      return !r.ingredients.some(function (i) {
        return i.n && (avoid.items.indexOf(i.n) !== -1 || rules.some(function (a) { return a.rx && a.rx.test(i.n); }));
      });
    };
    var avoiding = function () { return !!avoid.diet || avoid.groups.length + avoid.items.length > 0; };

    // -- Scoring, as build.py's week_plans does it --
    var weightCache = {};
    var weightsOf = function (r) {
      if (weightCache[r.url]) return weightCache[r.url];
      var w = {};
      r.ingredients.forEach(function (i) {
        if (i.n && !i.s) w[i.n] = (RULES.fresh || []).indexOf(i.a) !== -1 ? RULES.freshWeight : 1;
      });
      return (weightCache[r.url] = w);
    };
    var score = function (week) {
      var uses = {}, weight = {};
      week.forEach(function (r) { var w = weightsOf(r); for (var n in w) { uses[n] = (uses[n] || 0) + 1; weight[n] = w[n]; } });
      // Something already in the kitchen counts as if it were shared once more.
      var t = 0;
      for (var n in uses) t += weight[n] * (uses[n] - 1 + (have.indexOf(n) !== -1 ? 1 : 0));
      return t;
    };
    // Cravings may break the variety rules themselves; the fill just mustn't make it worse.
    var varied = function (week, cravings) {
      var ok = ["category", "cuisine"].every(function (key) {
        var counts = {}, base = {};
        cravings.forEach(function (r) { base[r[key]] = (base[r[key]] || 0) + 1; });
        // Basics are all one "style"; their cuisines keep them varied.
        week.forEach(function (r) { if (!(key === "category" && r.basic)) counts[r[key]] = (counts[r[key]] || 0) + 1; });
        return Object.keys(counts).every(function (k) { return counts[k] <= Math.max(RULES.maxSame, base[k] || 0); });
      });
      var cuisines = {}, own = {};
      week.forEach(function (r) { cuisines[r.cuisine] = 1; });
      cravings.forEach(function (r) { own[r.cuisine] = 1; });
      var reach = Object.keys(own).length + week.length - cravings.length;
      // Effort after work: a craving may go past a limit, but the dinners filled in can't add to it.
      var over = function (list, test) { return list.filter(test).length; };
      var long = function (r) { return r.minutes > RULES.longMinutes; };
      var fried = function (r) { return r.fried; };
      var minutes = function (list) { return list.reduce(function (t, r) { return t + r.minutes; }, 0); };
      var fillers = week.filter(function (r) { return cravings.indexOf(r) === -1; });
      return ok && Object.keys(cuisines).length >= Math.min(RULES.minCuisines, reach)
        && over(week, long) <= Math.max(RULES.maxLong, over(cravings, long))
        && over(week, fried) <= Math.max(RULES.maxFried, over(cravings, fried))
        // Heavy cravings leave quick fill-ins: 20 minutes a night on average once over the limit.
        && minutes(week) <= Math.max(RULES.maxWeekMinutes, minutes(cravings) + QUICK_FILL * fillers.length);
    };
    var QUICK_FILL = 20;
    var shortTime = function (m) {
      var h = Math.floor(m / 60), n = m % 60;
      return [h ? h + " hr" : "", n ? n + " min" : ""].filter(Boolean).join(" ");
    };
    var combos = function (pool, k, from, acc, out) {
      if (acc.length === k) { out.push(acc.slice()); return; }
      for (var i = from; i < pool.length; i++) { acc.push(pool[i]); combos(pool, k, i + 1, acc, out); acc.pop(); }
    };
    // Every way to fill the nights around the cravings, best sharing first.
    var rank = function (cravings) {
      var pool = index.filter(function (r) { return r.plan && allowed(r) && cravings.indexOf(r) === -1; });
      var all = [];
      combos(pool, size - cravings.length, 0, [], all);
      return all.map(function (f) { return { fill: f, week: cravings.concat(f) }; })
        .filter(function (c) { return varied(c.week, cravings); })
        .map(function (c) { c.score = score(c.week); return c; })
        .sort(function (a, b) { return b.score - a.score; });
    };
    var lunchPicks = function (week) {
      var ranked = week.filter(function (r) { return r.lunch; }).sort(function (a, b) { return b.lunch - a.lunch; });
      var best = ranked.filter(function (r) { return r.lunch === 2; }).slice(0, RULES.lunches);
      return best.length ? best : ranked.slice(0, 1);
    };
    // As build.py's plan_name: the first name the plan fits that isn't taken.
    var nameFor = function (week, taken) {
      var names = RULES.names || [];
      for (var i = 0; i < names.length; i++) {
        var name = names[i][0], what = names[i][1], values = names[i][2], least = names[i][3];
        if (taken.indexOf(name) !== -1) continue;
        var count = 0;
        if (what === "cuisines") count = Object.keys(week.reduce(function (o, r) { o[r.cuisine] = 1; return o; }, {})).length;
        else if (what === "basic") count = week.filter(function (r) { return r.basic; }).length;
        else if (what === "tags") count = week.filter(function (r) { return values.some(function (v) { return r.tags.indexOf(v) !== -1; }); }).length;
        else if (what !== "any") count = week.filter(function (r) { return values.indexOf(r[what]) !== -1; }).length;
        if (count >= least) return name;
      }
      return names.length ? names[names.length - 1][0] : "Your plan";
    };

    // -- Savings: each pack bought once for several dinners instead of once per dinner, and
    // nothing bought for what's already in the kitchen. Prices rise with food inflation
    // from the date they were checked, so the estimate keeps up until they're checked again.
    var PACKS = {};
    (RULES.packs || []).forEach(function (p) { PACKS[p[0]] = { size: p[1], per: p[2], price: p[3] }; });
    var country = { au: 0, uk: 1, us: 2 }[(window.FieldKitchenNames || {}).pref] || 0;
    var years = Math.max(0, (Date.now() - new Date(RULES.pricesChecked || Date.now())) / 31557600000);
    var priceOf = function (p, c) { return p.price[c] * Math.pow(1 + ((RULES.inflation || [])[c] || 0), years); };
    var money = function (v, c) { return ((c == null ? country : c) === 1 ? "£" : "$") + Math.round(v); };
    // Lunch dinners go on at double the household; the rest at the household.
    var servesFor = function (card, url) {
      return extra && urlsOf(card, "data-lunches").indexOf(url) !== -1 ? people * 2 : people;
    };
    var savingOf = function (card, c) {
      if (c == null) c = country;
      var uses = {}, aisle = {}, out = { fresh: 0, jars: 0, had: 0, hadNames: [] };
      urlsOf(card).forEach(function (url) {
        var r = byUrl(url); if (!r) return;
        var scale = servesFor(card, url) / (r.serves || 1), mine = {};
        r.ingredients.forEach(function (i) {
          var p = PACKS[i.n]; if (!p) return;
          var unit = i.u || "";
          var amount = i.q == null ? (p.per[""] != null ? p.per[""] : p.size / 2)
            : p.per[unit] != null ? i.q * p.per[unit] : p.size / 2;
          mine[i.n] = (mine[i.n] || 0) + amount * scale;
          aisle[i.n] = i.a;
        });
        for (var n in mine) (uses[n] = uses[n] || []).push(mine[n]);
      });
      for (var n in uses) {
        var p = PACKS[n], packs = function (a) { return Math.ceil(a / p.size - 1e-6); };
        var together = packs(uses[n].reduce(function (t, a) { return t + a; }, 0));
        if (have.indexOf(n) !== -1) { out.had += together * priceOf(p, c); out.hadNames.push(n); continue; }
        if (uses[n].length < 2) continue;
        var apart = uses[n].reduce(function (t, a) { return t + packs(a); }, 0);
        var fresh = (RULES.fresh || []).indexOf(aisle[n]) !== -1;
        out[fresh ? "fresh" : "jars"] += (apart - together) * priceOf(p, c);
      }
      out.total = out.fresh + out.jars + out.had;
      return out;
    };
    var saveLine = function (card) {
      var save = card.querySelector(".plan-save"), s = savingOf(card);
      save.hidden = s.total < 1;
      save.textContent = "";
      save.appendChild(el("strong", "", "Saves about " + money(s.total)));
      save.appendChild(document.createTextNode(" against buying for each dinner on its own"));
      var parts = [];
      if (s.fresh >= 1) parts.push(money(s.fresh) + " of fresh food shared");
      if (s.jars >= 1) parts.push(money(s.jars) + " of jars and packets bought once");
      if (s.had >= 1) parts.push(money(s.had) + " already in your kitchen (" + joinAnd(s.hadNames.map(function (n) { return n.toLowerCase(); })) + ")");
      if (parts.length) save.appendChild(el("small", "", parts.join(" · ")));
      if (window.FieldKitchenNames) FieldKitchenNames.swap(save, true);
    };

    // A running total of what the plans added to the list have saved, kept per browser.
    // Each plan counts once, at what it saved when it was added, in all three currencies.
    var tally = document.querySelector(".plan-tally");
    var syncTally = function () {
      var saved = stored("fk-saved", []);
      var total = saved.reduce(function (t, x) { return t + (x.amounts[country] || 0); }, 0);
      tally.hidden = total < 1;
      if (tally.hidden) return;
      var since = new Date(saved[0].date);
      tally.textContent = "Your plans have saved about " + money(total) + " since " + since.getDate() + " " +
        since.toLocaleString("en-AU", { month: "short", year: "numeric" }) + " (" + saved.length + " plan" + (saved.length === 1 ? "" : "s") + ")";
    };
    var recordSaving = function (card) {
      var key = urlsOf(card).slice().sort().join(" ");
      var saved = stored("fk-saved", []).filter(function (x) { return x.key !== key; });
      saved.push({ key: key, date: new Date().toISOString(), amounts: [0, 1, 2].map(function (c) { return Math.round(savingOf(card, c).total); }) });
      store("fk-saved", saved);
      syncTally();
    };

    var syncPeople = function () {
      sizeChips.forEach(function (c) { c.setAttribute("aria-pressed", String(+c.getAttribute("data-people") === people)); });
      extraBox.checked = extra;
    };
    var syncPlans = function () {
      var list = stored("fk-list", []);
      cards.forEach(function (card) {
        var urls = urlsOf(card);
        var all = urls.every(function (u) { return list.some(function (x) { return x.url === u && x.serves === servesFor(card, u); }); });
        var b = card.querySelector(".plan-add");
        b.hidden = false;
        b.classList.toggle("added", all);
        b.lastChild.textContent = all ? "On your list" : "Add these to my list";
        var view = card.querySelector(".plan-view");
        if (all && !view) {
          view = el("a", "pill pill-outline plan-view", "View list");
          view.href = "list.html";
          b.parentNode.insertBefore(view, b.nextSibling);
        } else if (!all && view) view.remove();
        saveLine(card);
      });
    };
    var wire = function (card) {
      cards.push(card);
      card.querySelector(".plan-add").addEventListener("click", function () {
        // Each dinner goes on at its size; one already on the list is updated, not doubled.
        var urls = urlsOf(card);
        var list = stored("fk-list", []).filter(function (x) { return urls.indexOf(x.url) === -1; });
        urls.forEach(function (u) { list.push({ url: u, serves: servesFor(card, u) }); });
        store("fk-list", list);
        recordSaving(card);
        syncPlans();
        syncBasics();
      });
    };
    var unwire = function (card) { cards = cards.filter(function (c) { return c !== card; }); card.remove(); };

    // A plan card built here, laid out like the ones build.py writes.
    var makeCard = function (week, title, eyebrow, cravings) {
      week = week.slice().sort(function (a, b) { return a.keeps - b.keeps || a.title.localeCompare(b.title); });
      var lunches = lunchPicks(week);
      var uses = {}, fresh = {};
      week.map(weightsOf).forEach(function (w) { for (var n in w) { uses[n] = (uses[n] || 0) + 1; if (w[n] > 1) fresh[n] = 1; } });
      var shared = Object.keys(uses).filter(function (n) { return uses[n] > 1; })
        .sort(function (a, b) { return uses[b] - uses[a] || (fresh[b] || 0) - (fresh[a] || 0) || a.localeCompare(b); });
      var lead = shared.filter(function (n) { return fresh[n] && (RULES.everyday || []).indexOf(n) === -1; });
      lead = (lead.length ? lead : shared).slice(0, 3);
      var card = el("article", "plan");
      card.setAttribute("data-urls", JSON.stringify(week.map(function (r) { return r.url; })));
      card.setAttribute("data-lunches", JSON.stringify(lunches.map(function (r) { return r.url; })));
      var head = el("header");
      head.appendChild(el("p", "eyebrow", eyebrow));
      head.appendChild(el("h2", "", title));
      if (lead.length) head.appendChild(el("p", "plan-sharing", "Sharing " + lead.map(function (n) { return n.toLowerCase(); }).join(", ")));
      card.appendChild(head);
      // No set days: soonest to go off first, as build.py orders its plans (keeps_info).
      var ol = el("ol", "plan-days");
      week.forEach(function (r, i) {
        var li = el("li"); if (lunches.indexOf(r) !== -1) li.setAttribute("data-lunch", "");
        li.appendChild(el("span", "plan-day", String(i + 1)));
        var d = el("div"), a = el("a", "", r.title); a.href = r.url; d.appendChild(a);
        (r.labels || []).forEach(function (t) { d.appendChild(el("span", "plan-tag", t)); });
        var soon = r.keeps > 3 ? "" : i + 1 <= r.keeps ? " · cook within " + r.keeps + " days" : " · freeze the " + r.keepsWhat + " on shop day";
        d.appendChild(el("small", "", (r.basic ? "Basic · " : "") + r.cuisine + " · " + shortTime(r.minutes) + soon + (cravings.indexOf(r) !== -1 ? " · your pick" : "")));
        li.appendChild(d);
        if (lunches.indexOf(r) !== -1) li.appendChild(el("span", "plan-lunch", "+ lunch"));
        ol.appendChild(li);
      });
      card.appendChild(ol);
      if (lunches.length) {
        var hint = el("p", "plan-leftovers");
        if (boxIcon) hint.appendChild(boxIcon.cloneNode(true));
        hint.appendChild(el("span", "", "For lunches, cook extra " + joinAnd(lunches.map(function (r) { return r.title; })) +
          (lunches.length === 1 ? ": it reheats" : ": they reheat") + " well the next day."));
        card.appendChild(hint);
      }
      card.appendChild(el("p", "plan-save"));
      if (shared.length) {
        var det = el("details", "plan-shared");
        det.appendChild(el("summary", "", shared.length + " ingredients bought once, used more than once"));
        var ul = el("ul");
        shared.forEach(function (n) { var li = el("li", "", n + " "); li.appendChild(el("b", "", "×" + uses[n])); ul.appendChild(li); });
        det.appendChild(ul); card.appendChild(det);
      }
      var add = el("button", "pill pill-solid plan-add"); add.type = "button"; add.hidden = true;
      if (plusIcon) add.appendChild(plusIcon.cloneNode(true));
      add.appendChild(document.createTextNode("Add these to my list"));
      card.appendChild(add);
      if (window.FieldKitchenNames) FieldKitchenNames.swap(card, true);
      return card;
    };
    var eyebrowOf = function (week) {
      return week.length + " dinners · " + shortTime(week.reduce(function (t, r) { return t + r.minutes; }, 0)) + " cooking";
    };

    // Ready-made plans: the build's, or reworked here around what's being left out.
    var plansNone = document.querySelector(".plans-none");
    var plansHave = document.querySelector(".plans-have");
    var readyMade = function () {
      var rework = avoiding() || have.length > 0;
      cards.filter(function (c) { return c.classList.contains("plan-local"); }).forEach(unwire);
      serverCards.forEach(function (c) { c.hidden = rework; });
      plansNone.hidden = true;
      plansHave.hidden = !have.length;
      plansHave.textContent = have.length ? "Picked to use what's already in your kitchen (" + have.length +
        " thing" + (have.length === 1 ? "" : "s") + " ticked on What can I cook?)." : "";
      if (!rework) return;
      var chosen = [], taken = [];
      rank([]).some(function (c) {
        if (chosen.every(function (p) { return c.week.filter(function (r) { return p.indexOf(r) !== -1; }).length <= 1; })) chosen.push(c.week);
        return chosen.length >= (RULES.count || 6);
      });
      chosen.forEach(function (week) {
        var title = nameFor(week, taken); taken.push(title);
        var card = makeCard(week, title, eyebrowOf(week), []);
        card.classList.add("plan-local");
        plans.appendChild(card);
        wire(card);
      });
      plansNone.hidden = chosen.length > 0;
      if (!chosen.length) {
        // Too few dinners left for a plan: say which ones still fit, so they're easy to find.
        var fit = index.filter(function (r) { return r.plan && allowed(r); });
        plansNone.textContent = fit.length ? "Only " + fit.length + " dinner" + (fit.length === 1 ? "" : "s") +
          " in the book fit" + (fit.length === 1 ? "s" : "") + " everything you're leaving out, not enough for a plan of " + size + " yet: " : "Nothing in the book fits everything you're leaving out yet.";
        fit.forEach(function (r, i) {
          var a = el("a", "", r.title); a.href = r.url;
          plansNone.appendChild(a);
          plansNone.appendChild(document.createTextNode(i === fit.length - 1 ? "." : i === fit.length - 2 ? " and " : ", "));
        });
      }
    };

    sizeChips.forEach(function (c) {
      c.addEventListener("click", function () { people = +c.getAttribute("data-people"); store("fk-people", people); syncPeople(); syncPlans(); });
    });
    extraBox.addEventListener("change", function () { extra = extraBox.checked; store("fk-lunches", extra); syncPlans(); });
    peopleBox.hidden = false;
    syncPeople();
    serverCards.forEach(wire);

    // Basics: one tap puts a supermarket shortcut on the list at the household size.
    var basicRows = [].slice.call(document.querySelectorAll(".plan-basics li"));
    var syncBasics = function () {
      var list = stored("fk-list", []);
      basicRows.forEach(function (li) {
        var r = byUrl(li.getAttribute("data-url"));
        li.hidden = !!r && !allowed(r);
        var on = list.some(function (x) { return x.url === li.getAttribute("data-url"); });
        var b = li.querySelector(".basic-add");
        b.hidden = false;
        b.classList.toggle("added", on);
        b.lastChild.textContent = on ? "On your list" : "Add to list";
      });
    };
    basicRows.forEach(function (li) {
      li.querySelector(".basic-add").addEventListener("click", function () {
        var url = li.getAttribute("data-url");
        var list = stored("fk-list", []).filter(function (x) { return x.url !== url; });
        list.push({ url: url, serves: people });
        store("fk-list", list);
        syncBasics();
        syncPlans();
      });
    });

    // A search box with suggestions under it, used for cravings and for leaving things out.
    var picker = function (input, box, options, choose) {
      var close = function () { box.hidden = true; box.textContent = ""; input.setAttribute("aria-expanded", "false"); };
      var suggest = function () {
        var q = input.value.trim().toLowerCase();
        var hits = options().filter(function (o) { return !q || o.label.toLowerCase().indexOf(q) !== -1; })
          .sort(function (a, b) { return (a.label.toLowerCase().indexOf(q) - b.label.toLowerCase().indexOf(q)) || a.label.localeCompare(b.label); })
          .slice(0, 6);
        box.textContent = "";
        if (!hits.length) { close(); return; }
        hits.forEach(function (o) {
          var li = el("li"); li.setAttribute("role", "option");
          li.appendChild(el("span", "", o.label));
          li.appendChild(el("small", "", o.hint));
          li.addEventListener("pointerdown", function (e) { e.preventDefault(); input.value = ""; close(); choose(o.value); });
          box.appendChild(li);
        });
        box.hidden = false; input.setAttribute("aria-expanded", "true");
        if (window.FieldKitchenNames) FieldKitchenNames.swap(box, true);
      };
      input.addEventListener("input", suggest);
      input.addEventListener("focus", suggest);
      input.addEventListener("blur", function () { setTimeout(close, 100); });
    };
    var chip = function (text, label, remove) {
      var b = el("button", "chip", text + " ×");
      b.type = "button"; b.setAttribute("aria-pressed", "true"); b.setAttribute("aria-label", "Remove " + label);
      b.addEventListener("click", remove);
      return b;
    };

    // -- Build your own --
    var build = document.querySelector(".plan-build");
    var craveInput = build.querySelector("input");
    var craveChips = build.querySelector(".plan-cravings");
    var fill = build.querySelector(".plan-fill");
    var result = build.querySelector(".plan-result");
    var maxCravings = size - 1;
    var cravings = stored("fk-cravings", []).map(function (u) { return byUrl(u); }).filter(Boolean);
    var ranked = [], shown = [];
    build.hidden = false;
    var drawCravings = function () {
      craveChips.textContent = "";
      cravings.forEach(function (r) {
        craveChips.appendChild(chip(r.title, r.title, function () { cravings = cravings.filter(function (x) { return x !== r; }); changed(); }));
      });
      fill.disabled = !cravings.length;
      craveInput.disabled = cravings.length >= maxCravings;
      craveInput.placeholder = cravings.length >= maxCravings ? "That's " + maxCravings + " picked" : "What are you craving?";
    };
    var changed = function () {
      store("fk-cravings", cravings.map(function (r) { return r.url; }));
      [].slice.call(result.querySelectorAll(".plan")).forEach(unwire);
      result.textContent = ""; ranked = []; shown = [];
      drawCravings();
    };
    picker(craveInput, build.querySelector(".list-suggest"), function () {
      return index.filter(function (r) { return r.plan && allowed(r) && cravings.indexOf(r) === -1; }).map(function (r) {
        return { label: r.title, hint: r.basic ? "Basic · " + r.cuisine : r.cuisine + " · " + r.category, value: r };
      });
    }, function (r) {
      cravings.push(r); changed();
      if (cravings.length < maxCravings) craveInput.focus();
    });
    var draw = function (week) {
      [].slice.call(result.querySelectorAll(".plan")).forEach(unwire);
      result.textContent = "";
      var card = makeCard(week, nameFor(week, []), "Your plan · " + eyebrowOf(week), cravings);
      card.classList.add("plan-mine");
      var again = el("button", "pill pill-outline plan-again", "Try another mix"); again.type = "button";
      again.addEventListener("click", next);
      card.appendChild(again);
      result.appendChild(card);
      wire(card);
      syncPlans();
    };
    // "Try another mix" shows the next best fill that changes at least two of its dinners
    // from every fill shown so far (or one, when only one night is left to fill).
    var next = function () {
      var overlap = function (x, y) { return x.fill.filter(function (r) { return y.fill.indexOf(r) !== -1; }).length; };
      var pick = ranked.filter(function (c) {
        return shown.indexOf(c) === -1 && shown.every(function (s) { return overlap(c, s) <= Math.max(0, c.fill.length - 2); });
      })[0];
      if (!pick) { shown = []; pick = ranked[0]; }
      if (!pick) { result.textContent = ""; result.appendChild(el("p", "plan-none", "Nothing in the book fits around those picks. Try swapping one.")); return; }
      shown.push(pick);
      draw(pick.week);
    };
    fill.addEventListener("click", function () {
      ranked = rank(cravings).slice(0, 60);
      shown = [];
      next();
      result.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });

    // -- Leave out panel --
    var avoidBox = document.querySelector(".plan-avoid");
    var avoidChips = [].slice.call(avoidBox.querySelectorAll("[data-avoid]"));
    var avoidItems = avoidBox.querySelector(".plan-avoid-items");
    var avoidCount = avoidBox.querySelector(".plan-avoid-count");
    var everyIngredient = {};
    index.forEach(function (r) { if (r.plan) r.ingredients.forEach(function (i) { if (i.n && !i.s) everyIngredient[i.n] = i.a; }); });
    var dietChips = [].slice.call(avoidBox.querySelectorAll("[data-diet]"));
    if (avoid.diet === undefined) avoid.diet = null;
    var drawAvoid = function () {
      dietChips.forEach(function (c) { c.setAttribute("aria-pressed", String(c.getAttribute("data-diet") === avoid.diet)); });
      avoidBox.querySelector(".plan-diet-note").hidden = !/-style$/.test(avoid.diet || "");
      avoidChips.forEach(function (c) { c.setAttribute("aria-pressed", String(avoid.groups.indexOf(c.getAttribute("data-avoid")) !== -1)); });
      avoidItems.textContent = "";
      avoid.items.forEach(function (n) {
        avoidItems.appendChild(chip(n, n, function () { avoid.items = avoid.items.filter(function (x) { return x !== n; }); avoidChanged(); }));
      });
      var n = (avoid.diet ? 1 : 0) + avoid.groups.length + avoid.items.length;
      avoidCount.textContent = n ? "(" + n + ")" : "";
      if (window.FieldKitchenNames) FieldKitchenNames.swap(avoidItems, true);
    };
    var avoidChanged = function () {
      store("fk-avoid", avoid);
      drawAvoid();
      cravings = cravings.filter(allowed);
      changed();
      readyMade();
      syncBasics();
      syncPlans();
    };
    dietChips.forEach(function (c) {
      c.addEventListener("click", function () {
        var label = c.getAttribute("data-diet");
        avoid.diet = avoid.diet === label ? null : label;
        avoidChanged();
      });
    });
    avoidChips.forEach(function (c) {
      c.addEventListener("click", function () {
        var label = c.getAttribute("data-avoid"), at = avoid.groups.indexOf(label);
        if (at === -1) avoid.groups.push(label); else avoid.groups.splice(at, 1);
        avoidChanged();
      });
    });
    picker(avoidBox.querySelector("input"), avoidBox.querySelector(".list-suggest"), function () {
      return Object.keys(everyIngredient).filter(function (n) { return avoid.items.indexOf(n) === -1; })
        .map(function (n) { return { label: n, hint: everyIngredient[n], value: n }; });
    }, function (n) { avoid.items.push(n); avoidChanged(); });
    avoidBox.hidden = false;
    if (avoiding()) avoidBox.open = true;

    drawAvoid();
    cravings = cravings.filter(allowed);
    drawCravings();
    readyMade();
    syncBasics();
    syncPlans();
    syncTally();
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
      if (window.FieldKitchenNames) { FieldKitchenNames.swap(matchList, true); FieldKitchenNames.swap(picks, true); }
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
