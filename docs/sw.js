// Offline support for The Field Kitchen. build.py fills in VERSION and FILES:
// every file in docs/, so the whole book is saved on first visit. Pages are
// fetched fresh when online (so new recipes show up) and fall back to the saved
// copy when offline; a new build changes VERSION and replaces the old copy.
var VERSION = "47721057c299";
var CACHE = "field-kitchen-" + VERSION;
var FILES = [
  "./",
  "american/chicken/buffalo-chicken-wings.html",
  "american/index.html",
  "australian/index.html",
  "australian/pork/maple-orange-glazed-ham.html",
  "australian/seafood/barbecued-whole-snapper.html",
  "book.html",
  "british/chicken/classic-roast-chicken.html",
  "british/desserts/classic-trifle.html",
  "british/index.html",
  "british/pork/toad-in-the-hole.html",
  "chinese/beef/mongolian-beef.html",
  "chinese/chicken/salt-and-pepper-wings.html",
  "chinese/index.html",
  "chinese/noodles/crispy-chilli-bacon-noodles.html",
  "chinese/pork/dumpling-lasagna.html",
  "cook.html",
  "greek/index.html",
  "greek/sides/greek-yoghurt-sauce.html",
  "home.js",
  "icon-192.png",
  "icon-512.png",
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
  "italian/pasta/nduja-pasta.html",
  "italian/pork/crispy-porchetta.html",
  "japanese/chicken/chicken-nanban.html",
  "japanese/chicken/karaage.html",
  "japanese/chicken/nagoya-chicken-wings.html",
  "japanese/eggs/ramen-egg.html",
  "japanese/index.html",
  "list.html",
  "manifest.webmanifest",
  "mexican/beef/carne-asada-tacos.html",
  "mexican/beef/chilli-con-carne.html",
  "mexican/index.html",
  "recipe.js",
  "search-index.js",
  "site.js",
  "south-african/duck/mohs-duck-and-tamarind-curry.html",
  "south-african/index.html",
  "south-african/sides/chunky-onion-and-tomato-relish.html",
  "spanish/chicken/chicken-and-white-bean-stew.html",
  "spanish/index.html",
  "style.css",
  "thai/beef/thai-beef-salad.html",
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
  event.respondWith(
    fetch(request).then(function (response) {
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
