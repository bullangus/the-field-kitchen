// Offline support for The Field Kitchen. build.py fills in VERSION and FILES:
// every file in docs/, so the whole book is saved on first visit. Pages are
// fetched fresh when online (so new recipes show up) and fall back to the saved
// copy when offline; a new build changes VERSION and replaces the old copy.
var VERSION = "fe0dab4ef9b6";
var CACHE = "field-kitchen-" + VERSION;
var FILES = [
  "./",
  "american/baking/chocolate-chip-cookies.html",
  "american/chicken/buffalo-chicken-wings.html",
  "american/index.html",
  "american/pasta/mac-and-cheese.html",
  "american/salads/caesar-salad.html",
  "australian/index.html",
  "australian/pork/maple-orange-glazed-ham.html",
  "australian/seafood/barbecued-whole-snapper.html",
  "australian/seafood/honey-glazed-salmon.html",
  "australian/sides/nans-christmas-pasta-salad.html",
  "basics/bean-nachos.html",
  "basics/butter-chicken.html",
  "basics/dumpling-night.html",
  "basics/falafel-wraps.html",
  "basics/fish-and-chips.html",
  "basics/hot-chook-and-coleslaw.html",
  "basics/laksa.html",
  "basics/old-el-paso-tacos.html",
  "basics/pies-and-peas.html",
  "basics/pizza-night.html",
  "basics/ravioli-and-sauce.html",
  "basics/schnitty-and-chips.html",
  "basics/snags-in-bread.html",
  "basics/vegie-burgers.html",
  "basics/vegie-fried-rice.html",
  "basics/vegie-korma.html",
  "book.html",
  "british/beef/cottage-pie.html",
  "british/chicken/classic-roast-chicken.html",
  "british/desserts/classic-trifle.html",
  "british/index.html",
  "british/pork/toad-in-the-hole.html",
  "british/potatoes/baked-potato.html",
  "british/sides/duck-fat-potatoes.html",
  "british/sides/gravy.html",
  "chinese/beef/mongolian-beef.html",
  "chinese/chicken/dry-chilli-chicken.html",
  "chinese/chicken/salt-and-pepper-wings.html",
  "chinese/index.html",
  "chinese/noodles/chilli-oil-noodles.html",
  "chinese/noodles/crispy-chilli-bacon-noodles.html",
  "chinese/pork/dumpling-lasagna.html",
  "cook.html",
  "fonts/cormorant-garamond-normal-latin-ext.woff2",
  "fonts/cormorant-garamond-normal-latin.woff2",
  "fonts/source-serif-4-italic-latin-ext.woff2",
  "fonts/source-serif-4-italic-latin.woff2",
  "fonts/source-serif-4-normal-latin-ext.woff2",
  "fonts/source-serif-4-normal-latin.woff2",
  "greek/index.html",
  "greek/sides/greek-yoghurt-sauce.html",
  "home.js",
  "icon-192.png",
  "icon-512.png",
  "icon-mono-192.png",
  "icon-mono-512.png",
  "icon.svg",
  "index.html",
  "indian/breads/simple-naan.html",
  "indian/index.html",
  "indian/sides/raita.html",
  "italian/breads/focaccia.html",
  "italian/index.html",
  "italian/pasta/carbonara.html",
  "italian/pasta/fettuccine-alfredo.html",
  "italian/pasta/lasagne.html",
  "italian/pasta/marry-me-chicken-risoni.html",
  "italian/pasta/nduja-pasta.html",
  "italian/pasta/spag-bol.html",
  "italian/pork/crispy-porchetta.html",
  "japanese/breads/shokupan.html",
  "japanese/chicken/chicken-nanban.html",
  "japanese/chicken/karaage.html",
  "japanese/chicken/katsu-curry.html",
  "japanese/chicken/nagoya-chicken-wings.html",
  "japanese/eggs/egg-sando.html",
  "japanese/eggs/ramen-egg.html",
  "japanese/index.html",
  "japanese/pork/tonkatsu.html",
  "japanese/sides/shredded-cabbage.html",
  "japanese/sushi/chicken-avocado-nigiri.html",
  "japanese/sushi/salmon-aburi.html",
  "japanese/sushi/salmon-nigiri.html",
  "japanese/sushi/sushi-rice.html",
  "list.html",
  "manifest.webmanifest",
  "mexican/beef/carne-asada-tacos.html",
  "mexican/beef/chilli-con-carne.html",
  "mexican/index.html",
  "plans.html",
  "recipe.js",
  "search-index.js",
  "site.js",
  "south-african/chicken/bunny-chow.html",
  "south-african/duck/yvettes-duck-curry.html",
  "south-african/index.html",
  "south-african/sides/chunky-onion-and-tomato-relish.html",
  "spanish/chicken/chicken-and-white-bean-stew.html",
  "spanish/index.html",
  "style.css",
  "thai/beef/thai-beef-salad.html",
  "thai/chicken/satay-chicken.html",
  "thai/chicken/yellow-curry.html",
  "thai/index.html",
  "tools.js"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) { return cache.addAll(FILES); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) {
        return k.indexOf("field-kitchen-") === 0 && k !== CACHE;
      }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  // "no-cache" checks with the server every time (a quick "not modified" when nothing has
  // changed), so a new build shows at once instead of after the browser's 10-minute cache.
  event.respondWith(
    fetch(request, { cache: "no-cache" }).then(function (response) {
      if (response.ok) {
        var copy = response.clone();
        caches.open(CACHE).then(function (cache) { cache.put(request, copy); });
      }
      return response;
    }).catch(function () {
      return caches.match(request, { ignoreSearch: true }).then(function (hit) {
        return hit || caches.match("./index.html");
      });
    })
  );
});
