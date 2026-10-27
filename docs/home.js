// Home page: the "Why not cook..." tile shows a random recipe from the search
// index (a new one on "Pick another"), the chips filter the cuisine cards, and
// tiles fade up as they scroll in.
(function () {
  var index = window.FIELD_KITCHEN_INDEX || [];

  // ---- Random recipe ----
  var tile = document.querySelector(".tile-feature");
  if (tile && index.length > 1) {
    var links = tile.querySelectorAll("h2 a, .tile-actions a");
    var figure = tile.querySelector(".feature-photo");
    var img = figure.querySelector("img");
    var where = tile.querySelector(".feature-where");
    var meta = tile.querySelector(".feature-meta");
    var intro = tile.querySelector(".feature-intro");
    var next = tile.querySelector(".feature-next");
    var current = -1;

    var show = function () {
      var i;
      do { i = Math.floor(Math.random() * index.length); } while (i === current);
      current = i;
      var r = index[i];
      links[0].textContent = r.title;
      for (var k = 0; k < links.length; k++) links[k].href = r.url;
      figure.hidden = !r.photo;
      if (r.photo) img.src = r.photo;
      where.textContent = r.cuisine + " · " + r.category;
      meta.textContent = r.meta;
      intro.textContent = r.intro;
    };
    next.hidden = false;
    next.addEventListener("click", show);
    show();
  }

  // ---- Filter chips ----
  var chips = document.querySelector(".chips");
  if (chips) {
    var buttons = [].slice.call(chips.querySelectorAll(".chip"));
    var kitchens = [].slice.call(document.querySelectorAll(".kitchen"));
    var empty = document.querySelector(".filter-empty");
    chips.hidden = false;
    var filter = function (tag) {
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-filter") === tag)); });
      var shown = 0;
      kitchens.forEach(function (card) {
        var visible = 0;
        card.querySelectorAll("li[data-tags]").forEach(function (li) {
          var match = !tag || li.getAttribute("data-tags").split(" ").indexOf(tag) !== -1;
          li.hidden = !match;
          if (match) visible++;
        });
        card.hidden = visible === 0;
        shown += visible;
      });
      empty.hidden = shown > 0;
    };
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { filter(b.getAttribute("data-filter")); });
    });
  }

  // ---- Fade-up on scroll ----
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (calm || !("IntersectionObserver" in window)) return;
  document.documentElement.classList.add("reveal-ready");
  var tiles = document.querySelectorAll(".reveal");
  var reported = false;
  var seen = new IntersectionObserver(function (entries) {
    reported = true;
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add("in"); seen.unobserve(e.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  tiles.forEach(function (el) { seen.observe(el); });
  // Never leave the page blank: if the observer hasn't reported, show everything.
  setTimeout(function () {
    if (!reported) tiles.forEach(function (el) { el.classList.add("in"); });
  }, 1000);
})();
