// Home page: the "Why not cook..." tile shows a random recipe from the search
// index, and a new one each time "Pick another" is pressed; "Cook tonight" deals
// out quick recipes; "Your kitchen" lists this reader's favourites and recently
// opened recipes. (Filter chips and fade-up live in site.js.)
(function () {
  var index = window.FIELD_KITCHEN_INDEX || [];
  var tile = document.querySelector(".tile-feature");
  if (!tile || index.length < 2) return;
  var links = tile.querySelectorAll("h2 a, .tile-actions a");
  var figure = tile.querySelector(".feature-photo");
  var img = figure.querySelector("img");
  var where = tile.querySelector(".feature-where");
  var meta = tile.querySelector(".feature-meta");
  var intro = tile.querySelector(".feature-intro");
  var next = tile.querySelector(".feature-next");
  var current = -1;

  function show() {
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
  }
  next.hidden = false;
  next.addEventListener("click", show);
  show();
})();
(function () {
  var index = window.FIELD_KITCHEN_INDEX || [];
  function stored(key, fallback) {
    try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function el(tag, text) { var e = document.createElement(tag); if (text !== undefined) e.textContent = text; return e; }

  // ---- Your kitchen: favourites and recently opened, from this browser ----
  var tile = document.querySelector(".tile-yours");
  if (tile) {
  var byUrl = function (url) { return index.filter(function (r) { return r.url === url; })[0]; }
  var fill = function (box, urls, limit) {
    var recipes = urls.map(byUrl).filter(Boolean).slice(0, limit);
    var ul = box.querySelector("ul");
    recipes.forEach(function (r) {
      var li = el("li"), a = el("a", r.title);
      a.href = r.url;
      li.appendChild(a);
      li.appendChild(el("span", r.cuisine));
      ul.appendChild(li);
    });
    box.hidden = !recipes.length;
    return recipes.length;
  };
  var favs = stored("fk-favs", []);
  var shown = fill(tile.querySelector(".yours-favs"), favs, 5);
  shown += fill(tile.querySelector(".yours-recent"), stored("fk-recent", []).filter(function (u) { return favs.indexOf(u) === -1; }), shown ? 3 : 5);
  if (shown) { tile.hidden = false; tile.parentNode.classList.add("has-yours"); }
  }

  // ---- Cook tonight: a fresh hand of quick recipes on each visit, or on Shuffle ----
  var list = document.querySelector(".tonight-list");
  var quick = index.filter(function (r) { return r.tags.indexOf("quick") !== -1; });
  if (list && quick.length) {
    // Beside "Your kitchen" the tile is narrower: two columns, so deal an even four.
    var count = (parseInt(list.getAttribute("data-count"), 10) || 3) + (document.querySelector(".bento.has-yours") ? 1 : 0);
    var deal = function () {
      var pool = quick.slice(), hand = [];
      while (hand.length < count && pool.length) hand.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
      list.textContent = "";
      hand.forEach(function (r) {
        var li = el("li"), a = el("a");
        a.href = r.url;
        a.appendChild(el("strong", r.title));
        a.appendChild(el("span", r.cuisine + " · " + r.category));
        a.appendChild(el("small", r.meta));
        li.appendChild(a);
        list.appendChild(li);
      });
    };
    var shuffle = document.querySelector(".tonight-shuffle");
    if (quick.length > count) { shuffle.hidden = false; shuffle.addEventListener("click", deal); }
    deal();
  }
})();
