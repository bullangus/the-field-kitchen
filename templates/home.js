// Home page: the "Why not cook..." tile shows a random recipe from the search
// index (a new one on "Pick another"), and tiles fade up as they scroll in.
(function () {
  var index = window.FIELD_KITCHEN_INDEX || [];
  var tile = document.querySelector(".tile-feature");
  if (tile && index.length > 1) {
    var links = tile.querySelectorAll("h2 a, .tile-actions a");
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
      where.textContent = r.cuisine + " · " + r.category;
      meta.textContent = r.meta;
      intro.textContent = r.intro;
    };
    next.hidden = false;
    next.addEventListener("click", show);
    show();
  }

  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (calm || !("IntersectionObserver" in window)) return;
  document.documentElement.classList.add("reveal-ready");
  var seen = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add("in"); seen.unobserve(e.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll(".reveal").forEach(function (el) { seen.observe(el); });
})();
