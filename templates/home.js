// "Why not cook..." card on the home page: shows a random recipe from the
// search index, and a fresh one each time "Pick another" is pressed.
(function () {
  var card = document.querySelector(".feature");
  var index = window.FIELD_KITCHEN_INDEX || [];
  if (!card || index.length < 2) return;
  var link = card.querySelector("h2 a");
  var where = card.querySelector(".feature-where");
  var meta = card.querySelector(".meta");
  var intro = card.querySelector(".feature-intro");
  var next = card.querySelector(".feature-next");
  var current = -1;

  function show() {
    var i;
    do { i = Math.floor(Math.random() * index.length); } while (i === current);
    current = i;
    var r = index[i];
    link.href = r.url;
    link.textContent = r.title;
    where.textContent = r.cuisine + " · " + r.category;
    meta.textContent = r.meta;
    intro.textContent = r.intro;
  }

  next.hidden = false;
  next.addEventListener("click", show);
  show();
})();
