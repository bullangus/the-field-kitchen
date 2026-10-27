// The shopping list and "What can I cook?" pages. Both read the parsed ingredients
// in search-index.js (see ingredients.py): each line's shopping name, aisle,
// amount and unit. Lists and pantry picks are kept in this browser only.
(function () {
  var index = window.FIELD_KITCHEN_INDEX || [];
  var AISLES = ["Fruit & veg", "Herbs", "Meat & seafood", "Dairy & eggs", "Bread, pasta & rice",
                "Pantry & sauces", "Herbs & spices", "Oils & vinegars", "Wine & spirits", "Other"];
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
    return (q > 1 ? String(Math.ceil(q - 0.05)) : frac(q)) + (u ? " " + u : "");
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
      var checked = stored("fk-list-checked", {});
      recipesBox.textContent = ""; aislesBox.textContent = ""; lines = [];
      empty.hidden = picked.length > 0;
      actions.hidden = !picked.length;
      if (!picked.length) { summary.textContent = "Add recipes from their page with “Add to shopping list”. Amounts are combined and sorted by aisle."; return; }

      // Recipes on the list, each with its servings.
      picked.forEach(function (x) {
        var r = byUrl(x.url);
        var chip = el("div", "list-recipe");
        var a = el("a", "", r.title); a.href = r.url;
        var s = el("span", "", "Serves " + x.serves);
        var rm = el("button", "", "×"); rm.type = "button"; rm.setAttribute("aria-label", "Remove " + r.title);
        rm.addEventListener("click", function () {
          store("fk-list", stored("fk-list", []).filter(function (y) { return y.url !== x.url; }));
          build();
        });
        chip.appendChild(a); chip.appendChild(s); chip.appendChild(rm);
        recipesBox.appendChild(chip);
      });

      // Merge every ingredient line by shopping name, then by unit.
      var items = {};
      picked.forEach(function (x) {
        var r = byUrl(x.url), ratio = x.serves / (r.serves || 1);
        r.ingredients.forEach(function (ing) {
          if (!ing.n || ing.n === "Water") return;
          var it = items[ing.n] || (items[ing.n] = { name: ing.n, aisle: ing.a, staple: ing.s, units: {}, some: false, from: [] });
          if (ing.q === null) it.some = true;
          else it.units[ing.u || ""] = (it.units[ing.u || ""] || 0) + ing.q * ratio;
          if (it.from.indexOf(r.title) === -1) it.from.push(r.title);
        });
      });
      var all = Object.keys(items).map(function (k) { return items[k]; });
      var groups = AISLES.map(function (a) {
        return { name: a, items: all.filter(function (it) { return it.aisle === a && !it.staple; }) };
      });
      groups.push({ name: "Pantry staples: check you have", items: all.filter(function (it) { return it.staple; }) });
      var count = 0;
      groups.forEach(function (g) {
        if (!g.items.length) return;
        g.items.sort(function (a, b) { return a.name.localeCompare(b.name); });
        var section = el("section", "aisle");
        section.appendChild(el("h2", "", g.name));
        var ul = el("ul");
        g.items.forEach(function (it) {
          var amounts = Object.keys(it.units).map(function (u) { return amount(it.units[u], u); });
          if (it.some && amounts.length) amounts.push("plus some");
          var text = it.name + (amounts.length ? ": " + amounts.join(" + ") : "");
          lines.push((checked[it.name] ? "✓ " : "▢ ") + text);
          var li = el("li", checked[it.name] ? "done" : "");
          var tick = el("button", "tick"); tick.type = "button";
          tick.setAttribute("aria-pressed", String(!!checked[it.name]));
          tick.setAttribute("aria-label", "Got " + it.name);
          var body = el("div");
          var name = el("strong", "", it.name);
          body.appendChild(name);
          if (amounts.length) body.appendChild(el("span", "amount", amounts.join(" + ")));
          body.appendChild(el("small", "", "For " + it.from.join(", ")));
          tick.addEventListener("click", function () {
            var c = stored("fk-list-checked", {});
            if (c[it.name]) delete c[it.name]; else c[it.name] = true;
            store("fk-list-checked", c);
            li.classList.toggle("done");
            tick.setAttribute("aria-pressed", String(!!c[it.name]));
          });
          li.appendChild(tick); li.appendChild(body);
          ul.appendChild(li);
          count++;
        });
        section.appendChild(ul);
        aislesBox.appendChild(section);
      });
      summary.textContent = count + " things to buy for " + picked.length + " recipe" + (picked.length === 1 ? "" : "s") +
        ". Tick them off as you shop.";
    };

    document.querySelector(".list-clear").addEventListener("click", function () {
      store("fk-list", []); store("fk-list-checked", {}); build();
    });
    document.querySelector(".list-print").addEventListener("click", function () { window.print(); });
    var share = document.querySelector(".list-share");
    share.addEventListener("click", function () {
      var text = "Shopping list\n\n" + lines.join("\n");
      if (navigator.share) { navigator.share({ title: "Shopping list", text: text }).catch(function () {}); return; }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function () {
          share.textContent = "Copied!";
          setTimeout(function () { share.textContent = "Share or copy"; }, 2000);
        });
      }
    });
    build();
  }

  // ---- What can I cook? ----
  var pantry = document.querySelector(".pantry");
  if (pantry) {
    var chips = [].slice.call(pantry.querySelectorAll("[data-ingredient]"));
    var matchList = document.querySelector(".match-list");
    var none = document.querySelector(".matches-empty");
    var have = stored("fk-fridge", []);

    var rank = function () {
      store("fk-fridge", have);
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(have.indexOf(c.getAttribute("data-ingredient")) !== -1)); });
      matchList.textContent = "";
      if (!have.length) { none.hidden = false; none.textContent = "Pick a few ingredients to see what you can make."; return; }
      var results = index.map(function (r) {
        var need = [];
        r.ingredients.forEach(function (i) { if (i.n && !i.s && need.indexOf(i.n) === -1) need.push(i.n); });
        var got = need.filter(function (n) { return have.indexOf(n) !== -1; });
        var missing = need.filter(function (n) { return have.indexOf(n) === -1; });
        return { r: r, got: got, missing: missing, score: need.length ? got.length / need.length : 0 };
      }).filter(function (m) { return m.got.length; })
        .sort(function (a, b) { return a.missing.length - b.missing.length || b.score - a.score; })
        .slice(0, 12);
      none.hidden = results.length > 0;
      if (!results.length) none.textContent = "Nothing uses those yet. Try adding a few more.";
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
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        var name = c.getAttribute("data-ingredient");
        var i = have.indexOf(name);
        if (i === -1) have.push(name); else have.splice(i, 1);
        rank();
      });
    });
    document.querySelector(".pantry-clear").addEventListener("click", function () { have = []; rank(); });
    rank();
  }
})();
