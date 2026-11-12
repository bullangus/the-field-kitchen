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
      var checked = stored("fk-list-checked", {});
      recipesBox.textContent = ""; aislesBox.textContent = ""; lines = [];
      empty.hidden = picked.length > 0;
      actions.hidden = !picked.length;
      if (!picked.length) { summary.textContent = "One list for everything you plan to cook."; ideas(); return; }

      // Recipes on the list, each with its servings.
      picked.forEach(function (x) {
        var r = byUrl(x.url);
        var chip = el("div", "list-recipe");
        var a = el("a", "", r.title); a.href = r.url;
        var s = el("span", "", "Serves " + x.serves + (x.options || []).map(function (o) { return " + " + o; }).join(""));
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
        var add = el("button", "pill pill-outline", "+ Add");
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
