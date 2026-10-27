// Home page: the "Why not cook..." tile shows a random recipe from the search
// index, and a new one each time "Pick another" is pressed. (Filter chips and
// fade-up on scroll live in site.js, since cuisine pages use them too.)
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
