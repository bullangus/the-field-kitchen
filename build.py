"""Build The Field Kitchen.

Reads every recipe in recipes/<Cuisine>/<Style>/*.md (plus any matching photo in
photos/) and regenerates:
  - the Contents section of README.md (between the CONTENTS markers)
  - the website in docs/ (served by GitHub Pages): a home page, one page per
    cuisine, one page per recipe, the shopping list and "What can I cook?"
    pages, and docs/book.html, the whole book for printing
  - docs/search-index.js, every recipe's details and parsed ingredients, read
    by search, the home page, the shopping list and "What can I cook?"
  - docs/sw.js and docs/manifest.webmanifest, so the site installs and works offline

Standard library only (plus ingredients.py beside it). Run:  python build.py
"""

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from ingredients import AISLES, parse_line

ROOT = Path(__file__).parent
RECIPES = ROOT / "recipes"
PHOTOS = ROOT / "photos"
README = ROOT / "README.md"
TEMPLATES = ROOT / "templates"
DOCS = ROOT / "docs"
BOOK_PAGE = "book.html"
LIST_PAGE = "list.html"
COOK_PAGE = "cook.html"
STYLESHEET = "style.css"
ICON = "icon.svg"
APP_ICONS = ("icon-192.png", "icon-512.png")
SITE_SCRIPT = "site.js"
HOME_SCRIPT = "home.js"
RECIPE_SCRIPT = "recipe.js"
TOOLS_SCRIPT = "tools.js"
SEARCH_INDEX = "search-index.js"
WORLD_DOTS = "world-dots.json"
MANIFEST = "manifest.webmanifest"
SERVICE_WORKER = "sw.js"
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
PHOTO_WARN_BYTES = 1_500_000
RECENT_COUNT = 5
NOTES_COUNT = 3
KITCHEN_CARD_RECIPES = 3  # recipes shown on each home page cuisine card; the rest are a click away
TONES = 6  # colour tones for cuisine cards and headers, .tone-1 to .tone-6 in style.css
QUICK_MINUTES = 30
PROJECT_MINUTES = 150  # hands-on time
MAKE_AHEAD_MINUTES = 240  # waiting time (marinating, curing...) that means starting ahead
PASSIVE_WORDS = r"marinat|curing|drying|rising|resting|chilling"
TITLE = "The Field Kitchen"
SUBTITLE = "Recipes from our family table"
THEME_COLOR = "#8a3b24"
BACKGROUND_COLOR = "#fbf8f3"

REQUIRED = ("title", "cuisine", "category", "serves")
# Inner paths of the 24x24 stroke icons used in the nav bar and on recipe pages.
NAV_ICONS = {
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "printer": ('<path d="M6 9V3h12v6"/><rect x="6" y="14" width="12" height="7"/>'
                '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>'),
    "moon": '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    "sun": ('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4'
            'M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    "basket": '<path d="M4 9h16l-1.6 9.6a2 2 0 0 1-2 1.7H7.6a2 2 0 0 1-2-1.7z"/><path d="m8 9 4-5 4 5"/><path d="M10 13v3M14 13v3"/>',
    "sparkle": ('<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/>'
                '<path d="M19 15l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>'),
    "play": '<path d="M7 4.5v15l12.5-7.5z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
}
# Cuisine icons (24x24 outline paths) from Tabler Icons v3.19.0, MIT licence,
# https://tabler.io/icons. New cuisines get the knife and fork until one is added here.
CUISINE_ART = {
    'american': '<path d="M4 15h16a4 4 0 0 1 -4 4h-8a4 4 0 0 1 -4 -4z" /> <path d="M12 4c3.783 0 6.953 2.133 7.786 5h-15.572c.833 -2.867 4.003 -5 7.786 -5z" /> <path d="M5 12h14" />',  # burger
    'australian': '<path d="M19 8h-14a6 6 0 0 0 6 6h2a6 6 0 0 0 6 -5.775l0 -.225z" /> <path d="M17 20a2 2 0 1 1 0 -4a2 2 0 0 1 0 4z" /> <path d="M15 14l1 2" /> <path d="M9 14l-3 6" /> <path d="M15 18h-8" /> <path d="M15 5v-1" /> <path d="M12 5v-1" /> <path d="M9 5v-1" />',  # grill
    'british': '<path d="M10.29 3h3.42a2 2 0 0 1 1.988 1.78l1.555 14a2 2 0 0 1 -1.988 2.22h-6.53a2 2 0 0 1 -1.988 -2.22l1.555 -14a2 2 0 0 1 1.988 -1.78z" /> <path d="M7.47 12.5l-4.257 -5.019a.899 .899 0 0 1 .69 -1.481h13.09a3 3 0 0 1 3.007 3v3c0 1.657 -1.346 3 -3.007 3" /> <path d="M7 17h10" />',  # teapot
    'chinese': '<path d="M4 11h16a1 1 0 0 1 1 1v.5c0 1.5 -2.517 5.573 -4 6.5v1a1 1 0 0 1 -1 1h-8a1 1 0 0 1 -1 -1v-1c-1.687 -1.054 -4 -5 -4 -6.5v-.5a1 1 0 0 1 1 -1z" /> <path d="M19 7l-14 1" /> <path d="M19 2l-14 3" />',  # bowl-chopsticks
    'greek': '<path d="M21 5.6c-3.2 -.7 -6.6 .2 -9.2 2.6" /> <path d="M13.2 6.9q-.9 -3.3 -4.6 -3.7q.5 3.4 4.6 3.7z" /> <path d="M11.9 8.1q-3 -2.3 -6.6 -.7q3 2.6 6.6 .7z" /> <path d="M11.9 8.3c-1.2 .9 -1.9 2 -2.13 3.46" /> <path d="M9.77 11.76a3 4.3 20 1 1 -2.94 8.08a3 4.3 20 1 1 2.94 -8.08z" /> <path d="M16.2 6.1c-.8 1.3 -1.3 2.8 -1.36 4.54" /> <path d="M14.84 10.64a2.9 4.1 -15 1 1 2.12 7.92a2.9 4.1 -15 1 1 -2.12 -7.92z" /> <path d="M6.9 14c-.5 .7 -.7 1.5 -.6 2.4" /> <path d="M14.4 12.8c-.4 .6 -.6 1.3 -.5 2.1" />',  # two olives on a twig, drawn for this book in the Tabler style (no icon set has an olive)
    'indian': '<path d="M4 11h16a1 1 0 0 1 1 1v.5c0 1.5 -2.517 5.573 -4 6.5v1a1 1 0 0 1 -1 1h-8a1 1 0 0 1 -1 -1v-1c-1.687 -1.054 -4 -5 -4 -6.5v-.5a1 1 0 0 1 1 -1z" /> <path d="M12 4a2.4 2.4 0 0 0 -1 2a2.4 2.4 0 0 0 1 2" /> <path d="M16 4a2.4 2.4 0 0 0 -1 2a2.4 2.4 0 0 0 1 2" /> <path d="M8 4a2.4 2.4 0 0 0 -1 2a2.4 2.4 0 0 0 1 2" />',  # soup
    'italian': '<path d="M12 21.5c-3.04 0 -5.952 -.714 -8.5 -1.983l8.5 -16.517l8.5 16.517a19.09 19.09 0 0 1 -8.5 1.983z" /> <path d="M5.38 15.866a14.94 14.94 0 0 0 6.815 1.634a14.944 14.944 0 0 0 6.502 -1.479" /> <path d="M13 11.01v-.01" /> <path d="M11 14v-.01" />',  # pizza
    'japanese': '<path d="M16.69 7.44a6.973 6.973 0 0 0 -1.69 4.56c0 1.747 .64 3.345 1.699 4.571" /> <path d="M2 9.504c7.715 8.647 14.75 10.265 20 2.498c-5.25 -7.761 -12.285 -6.142 -20 2.504" /> <path d="M18 11v.01" /> <path d="M11.5 10.5c-.667 1 -.667 2 0 3" />',  # fish
    'mexican': '<path d="M13 11c0 2.21 -2.239 4 -5 4s-5 -1.79 -5 -4a8 8 0 1 0 16 0a3 3 0 0 0 -6 0" /> <path d="M16 8c0 -2 2 -4 4 -4" />',  # pepper
    'south african': '<path d="M4 21l16 -4" /> <path d="M20 21l-16 -4" /> <path d="M12 15a4 4 0 0 0 4 -4c0 -3 -2 -3 -2 -8c-4 2 -6 5 -6 8a4 4 0 0 0 4 4z" />',  # campfire
    'spanish': '<path d="M5.5 5.5a2.5 2.5 0 0 0 -2.5 2.5c0 7.18 5.82 13 13 13a2.5 2.5 0 1 0 0 -5a8 8 0 0 1 -8 -8a2.5 2.5 0 0 0 -2.5 -2.5z" /> <path d="M5.195 5.519l-1.243 -1.989a1 1 0 0 1 .848 -1.53h1.392a1 1 0 0 1 .848 1.53l-1.245 1.99" /> <path d="M18.482 18.225l1.989 -1.243a1 1 0 0 1 1.53 .848v1.392a1 1 0 0 1 -1.53 .848l-1.991 -1.245" />',  # sausage
    'thai': '<path d="M17.536 3.393c3.905 3.906 3.905 10.237 0 14.143c-3.906 3.905 -10.237 3.905 -14.143 0l14.143 -14.143" /> <path d="M5.868 15.06a6.5 6.5 0 0 0 9.193 -9.192" /> <path d="M10.464 10.464l4.597 4.597" /> <path d="M10.464 10.464v6.364" /> <path d="M10.464 10.464h6.364" />',  # lemon (a lime slice)
    '_default': '<path d="M19 3v12h-5c-.023 -3.681 .184 -7.406 5 -12zm0 12v6h-1v-3m-10 -14v17m-3 -17v3a3 3 0 1 0 6 0v-3" />',  # tools-kitchen-2
}
# Where each cuisine sits on the home page map: (longitude, latitude, label side:
# "start" right of the pin, "end" left of it, "above" over it).
# Add one per new cuisine; cuisines without a place are left off the map.
CUISINE_PLACES = {
    "american": (-98, 39, "end"),
    "australian": (134, -25, "end"),
    "british": (-2, 54, "end"),
    "chinese": (104, 34, "start"),
    "greek": (22, 39, "start"),
    "indian": (78, 22, "end"),
    "italian": (12.5, 42.5, "above"),
    "japanese": (138, 37, "start"),
    "mexican": (-102, 23, "end"),
    "south african": (25, -29, "start"),
    "spanish": (-3.7, 40, "end"),
    "thai": (101, 15, "start"),
}
QUICK_CHIPS = (("quick", f"Under {QUICK_MINUTES} min"), ("make-ahead", "Make ahead"), ("project", "Weekend project"))
# docs/ is fully generated, but these must survive a rebuild.
KEEP_IN_DOCS = {".nojekyll", "CNAME"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        sys.exit(f"{path}: missing {', '.join(missing)}")
    meta["body"] = m.group(2)
    meta["path"] = path.relative_to(ROOT).as_posix()
    meta["stem"] = path.stem
    meta["url"] = f"{slug(meta['cuisine'])}/{slug(meta['category'])}/{path.stem}.html"
    return meta


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def render(body):
    """Render the small Markdown subset recipes use: ## / ### headings,
    paragraphs, '- ' bullet lists and '1. ' numbered lists."""
    out, para, list_tag = [], [], None

    def flush():
        nonlocal list_tag
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    for raw in body.splitlines():
        line = raw.strip()
        item = re.match(r"(-|\d+\.)\s+(.*)", line)
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            out.append(f'<h5>{inline(line[4:])}</h5>')
        elif line.startswith("## "):
            flush()
            name = line[3:]
            out.append(f'<h4 class="part part-{slug(name)}">{inline(name)}</h4>')
        elif item:
            tag = "ul" if item.group(1) == "-" else "ol"
            if para:
                flush()
            if list_tag != tag:
                flush()
                out.append(f"<{tag}>")
                list_tag = tag
            out.append(f"<li>{inline(item.group(2))}</li>")
        elif list_tag and raw.startswith((" ", "\t")):
            out[-1] = out[-1][:-5] + " " + inline(line) + "</li>"
        else:
            if list_tag:
                flush()
            para.append(line)
    flush()
    return "\n".join(out)


def sections(body):
    """(intro markdown, {heading: markdown}) for a recipe body split on its ## headings."""
    parts = re.split(r"^## (.+)$", body, flags=re.M)
    return parts[0].strip(), {name.strip(): md for name, md in zip(parts[1::2], parts[2::2])}


def bullets(md):
    return re.findall(r"^- (.*)", md or "", re.M)


def find_photos(recipes):
    """Match photos/<recipe file name>.<jpg|jpeg|png|webp> to recipes by file name."""
    if not PHOTOS.is_dir():
        return
    by_stem = {}
    for r in recipes:
        by_stem.setdefault(r["stem"], []).append(r)
    for photo in sorted(PHOTOS.iterdir()):
        if photo.suffix.lower() not in PHOTO_EXTENSIONS:
            continue
        owners = by_stem.get(photo.stem, [])
        if not owners:
            print(f"Warning: {photo.name} doesn't match any recipe file name, so it isn't used.")
            continue
        if len(owners) > 1:
            sys.exit(f"{photo.name} matches more than one recipe: {', '.join(o['path'] for o in owners)}. "
                     "Rename one of the recipe files.")
        if owners[0].get("photo"):
            sys.exit(f"{owners[0]['stem']} has more than one photo in photos/. Keep just one.")
        if photo.stat().st_size > PHOTO_WARN_BYTES:
            print(f"Warning: {photo.name} is {photo.stat().st_size // 1000} KB; "
                  "under about 1 MB keeps the site quick on phones.")
        owners[0]["photo"] = f"photos/{photo.stem}{photo.suffix.lower()}"
        owners[0]["photo_source"] = photo


def load():
    book, recipes = {}, []
    for path in sorted(RECIPES.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        r = parse(path)
        r["added"] = date_added(r)
        r["tags"] = recipe_tags(r)
        recipes.append(r)
        book.setdefault(r["cuisine"], {}).setdefault(r["category"], []).append(r)
    find_photos(recipes)
    for cats in book.values():
        for rs in cats.values():
            rs.sort(key=lambda r: r["title"].lower())
    book = {c: dict(sorted(cats.items())) for c, cats in sorted(book.items())}
    for i, cuisine in enumerate(book):
        for rs in book[cuisine].values():
            for r in rs:
                r["tone"] = i % TONES + 1
    return book


def all_recipes(book):
    return [r for cats in book.values() for recipes in cats.values() for r in recipes]


def minutes_in(text):
    """Sum of every '<n> min' and '<n> hr' in text (the upper end of a range counts)."""
    found = re.findall(r"(\d+(?:\.\d+)?)\s*(hr|min)", text)
    return sum(float(n) * (60 if unit == "hr" else 1) for n, unit in found)


def split_time(r):
    """(hands-on, hands-off) minutes from the time line, or None if it has no times.
    Parts like '+ 30 min marinating' or '(mostly rising)' are waiting, not work."""
    time = r.get("time", "")
    if not re.search(r"\d+\s*(hr|min)", time):
        return None
    active = passive = 0
    for part in re.split(r"[+·]", time):
        if re.search(PASSIVE_WORDS, part, re.I):
            passive += minutes_in(part)
        else:
            active += minutes_in(part)
    return active, passive


def recipe_tags(r):
    """Quick-filter tags for the chips, plus the recipe's style."""
    tags = [slug(r["category"])]
    times = split_time(r)
    active, passive = times if times else (None, 0)
    text = (r.get("time", "") + " " + r["body"]).lower()
    ahead = re.search(r"day before|make ahead|made ahead|make these ahead|ahead of time|curing|drying", text)
    if active is not None and active <= QUICK_MINUTES and not passive and not ahead:
        tags.append("quick")
    if ahead or passive >= MAKE_AHEAD_MINUTES:
        tags.append("make-ahead")
    if (active is not None and active >= PROJECT_MINUTES) or "day before" in r.get("time", "").lower():
        tags.append("project")
    return tags


def quick_tag_labels(r):
    return [label for key, label in QUICK_CHIPS if key in r["tags"]]


def time_facts(r):
    """[(label, value)] from the time line: 'Prep 15 min · Cook 30 min' -> Prep / Cook tiles."""
    facts = []
    for part in (p.strip() for p in r.get("time", "").split("·") if p.strip()):
        word, _, rest = part.partition(" ")
        if word in ("Prep", "Cook") and rest:
            facts.append((word, rest))
        else:
            facts.append(("Time", part))
    return facts


def contents_md(book):
    if not book:
        return "_No recipes yet._"
    lines = []
    for cuisine, cats in book.items():
        lines.append(f"### {cuisine}")
        for category, recipes in cats.items():
            links = ", ".join(f"[{r['title']}]({r['path']})" for r in recipes)
            lines.append(f"- **{category}:** {links}")
        lines.append("")
    count = len(all_recipes(book))
    lines.append(f"_{count} recipe{'s' if count != 1 else ''}._")
    return "\n".join(lines).strip()


def update_readme(book):
    text = README.read_text(encoding="utf-8")
    new = re.sub(
        r"(<!-- CONTENTS:START -->\n).*?(\n<!-- CONTENTS:END -->)",
        lambda m: m.group(1) + contents_md(book) + m.group(2),
        text,
        flags=re.S,
    )
    README.write_text(new, encoding="utf-8", newline="\n")


def cuisine_url(cuisine):
    return f"{slug(cuisine)}/index.html"


def vt_name(prefix, text):
    # Shared view-transition-name so a title glides between pages; must be unique per page.
    return f' style="view-transition-name: {prefix}-{slug(text)}"'


def meta_line(r):
    meta = [f"Serves {html.escape(r['serves'])}"]
    if r.get("time"):
        meta.append(html.escape(r["time"]))
    return " · ".join(meta)


def icon_inline():
    # Inline copy of the favicon that follows the text colour, for the nav bar.
    svg = (TEMPLATES / ICON).read_text(encoding="utf-8").strip()
    return (svg.replace('fill="#fbf8f3" stroke="#8a3b24"', 'fill="none" stroke="currentColor"')
               .replace("<svg ", '<svg aria-hidden="true" ', 1))


def cuisine_art(cuisine, css):
    paths = CUISINE_ART.get(cuisine.lower(), CUISINE_ART["_default"])
    # pathLength lets CSS "draw" each line in, whatever its real length.
    paths = paths.replace("<path ", '<path pathLength="1" ')
    # Thinner than the icon set's default 2, since these are shown large.
    return (f'<svg class="{css} draw" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.15" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')


def intro(r):
    """The recipe's opening paragraph, before ## Ingredients, as plain text."""
    head = r["body"].split("\n## ", 1)[0].strip()
    return re.sub(r"[*_]", "", " ".join(head.split()))


def search_index(book):
    """Every recipe's details for search, the home page, shopping list and "What can I cook?"."""
    entries = []
    for r in all_recipes(book):
        _, parts = sections(r["body"])
        # Search covers topping options too, so searching a topping finds its recipe.
        lines = bullets(parts.get("Ingredients")) + bullets(parts.get("Topping Options"))
        serves = re.match(r"\d+", r["serves"])
        entries.append({"title": r["title"], "cuisine": r["cuisine"], "category": r["category"],
                        "url": r["url"], "text": " ".join(lines),
                        "meta": html.unescape(meta_line(r)), "intro": intro(r),
                        "photo": r.get("photo", ""), "tags": r["tags"],
                        "serves": int(serves.group()) if serves else 1,
                        "ingredients": [parse_line(line) for line in bullets(parts.get("Ingredients"))]})
    return "window.FIELD_KITCHEN_INDEX = " + json.dumps(entries, ensure_ascii=False, indent=0) + ";\n"


def svg_icon(name, css=""):
    cls = f' class="{css}"' if css else ""
    return (f'<svg{cls} aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{NAV_ICONS[name]}</svg>')


def nav_html(book, root, current=None):
    links = []
    for cuisine, cats in book.items():
        here = ' aria-current="page"' if cuisine == current else ""
        n = sum(len(rs) for rs in cats.values())
        links.append(f'<li><a href="{root}{cuisine_url(cuisine)}"{here}>{html.escape(cuisine)}'
                     f'<small>{n}</small></a></li>')
    in_cuisine = " current" if current in book else ""

    def here(page):
        return ' aria-current="page"' if current == page else ""
    return f"""<nav class="site-nav" aria-label="Site" data-root="{root}">
  <div class="inner">
    <a class="home" href="{root}index.html">{icon_inline()}{TITLE}</a>
    <div class="menu" id="site-menu">
      <div class="cuisine-menu">
        <button type="button" class="nav-button cuisine-toggle{in_cuisine}" aria-expanded="false" aria-controls="cuisine-list">Cuisines{svg_icon("chevron", "chevron")}</button>
        <ul class="cuisine-list" id="cuisine-list">{"".join(links)}</ul>
      </div>
      <a class="nav-button" href="{root}{COOK_PAGE}"{here(COOK_PAGE)}>{svg_icon("sparkle")}What can I cook?</a>
      <a class="nav-button print" href="{root}{BOOK_PAGE}"{here(BOOK_PAGE)}>{svg_icon("printer")}Print</a>
      <form class="search" role="search">
        <label class="search-field">{svg_icon("search")}<input type="search" placeholder="Search recipes" aria-label="Search recipes or ingredients" autocomplete="off"><kbd title="Ctrl or ⌘ K opens the command palette">/</kbd></label>
        <ul class="search-results" hidden></ul>
      </form>
    </div>
    <a class="nav-button list-link" href="{root}{LIST_PAGE}"{here(LIST_PAGE)} aria-label="Shopping list">{svg_icon("basket")}<span class="list-count" hidden>0</span></a>
    <button type="button" class="nav-button theme-toggle" aria-label="Switch between light and dark">{svg_icon("moon", "moon")}{svg_icon("sun", "sun")}</button>
    <button type="button" class="nav-button menu-toggle" aria-expanded="false" aria-controls="site-menu" aria-label="Menu">{svg_icon("menu")}</button>
  </div>
</nav>"""


def toc_html(book, href):
    """Contents list grouped by cuisine and style; href(r) gives each recipe's link."""
    if not book:
        return '<li class="empty">No recipes yet.</li>'
    toc = []
    for cuisine, cats in book.items():
        toc.append(f'<li class="toc-cuisine"><a href="{href(cuisine)}">{html.escape(cuisine)}</a><ul>')
        for category, recipes in cats.items():
            toc.append(f'<li class="toc-category"><span>{html.escape(category)}</span><ul>')
            for r in recipes:
                toc.append(f'<li><a href="{href(r)}">{html.escape(r["title"])}</a></li>')
            toc.append("</ul></li>")
        toc.append("</ul></li>")
    return "\n".join(toc)


def source_html(r):
    """'Based on <source>': we change recipes as we cook them, so they aren't copies.
    Our own recipes ("Family recipe", "Our own, ...") are shown as written."""
    if not r.get("source"):
        return ""
    s = r["source"]
    if re.match(r"(family recipe|our own)", s, re.I):
        return f'<p class="source">{html.escape(s)}</p>'
    label = html.escape(re.sub(r"^https?://(www\.)?", "", s).split("/")[0])
    s_html = f'<a href="{html.escape(s)}">{label}</a>' if s.startswith("http") else html.escape(s)
    return f'<p class="source">Based on {s_html}</p>'


def recipe_html(r, root="", anchor=None):
    """A recipe as it appears in the printed book: one plain column."""
    photo = ""
    if r.get("photo"):
        photo = (f'<figure class="recipe-photo"><img src="{root}{r["photo"]}" '
                 f'alt="{html.escape(r["title"])}" loading="lazy"></figure>')
    id_attr = f' id="{anchor}"' if anchor else ""
    return f"""
<article class="recipe"{id_attr}>
  {photo}
  <p class="kicker">{html.escape(r['cuisine'])} · {html.escape(r['category'])}</p>
  <h3>{html.escape(r['title'])}</h3>
  <p class="meta">{meta_line(r)}</p>
  {render(r['body'])}
  {source_html(r)}
</article>"""


def page(book, depth, page_title, content, current=None, main_class=None):
    root = "../" * depth
    template = (TEMPLATES / "page.html").read_text(encoding="utf-8")
    return (template.replace("{{PAGE_TITLE}}", html.escape(page_title))
                    .replace("{{ROOT}}", root)
                    .replace("{{NAV}}", nav_html(book, root, current))
                    .replace("{{MAIN_CLASS}}", f' class="{main_class}"' if main_class else "")
                    .replace("{{CONTENT}}", content))


def date_added(r):
    # Timestamp of the commit that first added the file (full time, so recipes added
    # the same day still sort newest first); uncommitted recipes count as added now.
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%aI", "--", r["path"]],
                             cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.split()
    except (OSError, subprocess.SubprocessError):
        out = []
    return out[-1] if out else datetime.now().astimezone().isoformat(timespec="seconds")


def family_notes(book):
    """Newest dated owner note ('- YYYY-MM-DD: ...') of each recipe, newest first."""
    notes = []
    for r in all_recipes(book):
        section = r["body"].split("\n## Notes", 1)
        found = re.findall(r"^- (\d{4}-\d{2}-\d{2}): (.+)$", section[1], re.M) if len(section) == 2 else []
        if found:
            # Later lines win on the same day, since notes are appended in order.
            day, text = max(enumerate(found), key=lambda f: (f[1][0], f[0]))[1]
            notes.append((day, r, text))
    return sorted(notes, key=lambda n: (n[0], n[1]["added"]), reverse=True)


def nice_date(iso):
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%b %Y')}"


def chips_html(recipes, with_styles=True):
    """Filter chips: the quick filters that match something here, then (optionally) every style."""
    counts = {}
    for r in recipes:
        for t in r["tags"]:
            counts[t] = counts.get(t, 0) + 1
    chip_list = [(key, label) for key, label in QUICK_CHIPS if counts.get(key)]
    if with_styles:
        chip_list += [(slug(s), s) for s in sorted({r["category"] for r in recipes})]
    if not chip_list:
        return ""
    chips = '<button type="button" class="chip" data-filter="" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" class="chip" data-filter="{key}" aria-pressed="false">'
        f'{html.escape(label)}<small>{counts[key]}</small></button>'
        for key, label in chip_list
    )
    return (f'<div class="chips" role="group" aria-label="Filter recipes" hidden>{chips}</div>'
            '<p class="filter-empty" hidden>Nothing matches that filter yet.</p>')


def world_map(book):
    """Dotted world map with a glowing pin per cuisine, linking to its page."""
    data = json.loads((TEMPLATES / WORLD_DOTS).read_text(encoding="utf-8"))
    land = "".join(f"M{x:g} {y:g}h0" for x, y in data["dots"])
    pins = []
    for i, (cuisine, cats) in enumerate(book.items()):
        place = CUISINE_PLACES.get(cuisine.lower())
        if not place:
            print(f"Note: {cuisine} has no CUISINE_PLACES entry, so it isn't on the home page map.")
            continue
        lon, lat, side = place
        x, y = lon + 180, 80 - lat
        n = sum(len(rs) for rs in cats.values())
        # Label to the right ("start"), left ("end") or centred above the pin ("above").
        dx, dy, anchor = {"start": (4.5, 1.4, "start"), "end": (-4.5, 1.4, "end"), "above": (0, -4.5, "middle")}[side]
        pins.append(
            f'<a class="pin tone-{i % TONES + 1}" href="{cuisine_url(cuisine)}" '
            f'aria-label="{html.escape(cuisine)}: {n} recipe{"s" if n != 1 else ""}">'
            f'<circle class="pin-pulse" cx="{x:g}" cy="{y:g}" r="3"/>'
            f'<circle class="pin-dot" cx="{x:g}" cy="{y:g}" r="{1.6 + min(n, 6) * 0.25:g}"/>'
            f'<text x="{x + dx:g}" y="{y + dy:g}" text-anchor="{anchor}">{html.escape(cuisine)}</text></a>')
    return f"""
  <section class="atlas reveal" aria-label="Where our recipes come from">
    <div class="section-head">
      <h2>Our table, around the world</h2>
      <p>Tap a pin to visit that kitchen.</p>
    </div>
    <div class="atlas-map">
      <svg viewBox="0 0 {data['width']} {data['height']}" role="img" aria-label="World map with a pin for each cuisine">
        <path class="land" d="{land}"/>
        {"".join(pins)}
      </svg>
    </div>
  </section>"""


def home_html(book):
    recipes = all_recipes(book)
    count, cuisines = len(recipes), len(book)
    notes = family_notes(book)
    hat = icon_inline().replace("<svg ", '<svg class="hat" ', 1)

    def plural(n, word):
        return f"{n} {word}{'' if n == 1 else 's'}"

    pick = recipes[0] if recipes else None
    feature = ""
    if pick:
        photo = pick.get("photo", "")
        feature = f"""
    <section class="tile tile-feature reveal" aria-live="polite">
      <figure class="feature-photo"{'' if photo else ' hidden'}><img src="{photo}" alt=""></figure>
      <p class="eyebrow">Why not cook…</p>
      <h2><a href="{pick['url']}">{html.escape(pick['title'])}</a></h2>
      <p class="feature-where">{html.escape(pick['cuisine'])} · {html.escape(pick['category'])}</p>
      <p class="feature-meta">{meta_line(pick)}</p>
      <p class="feature-intro">{html.escape(intro(pick))}</p>
      <div class="tile-actions">
        <a class="pill pill-light" href="{pick['url']}">Open recipe</a>
        <button type="button" class="pill pill-ghost feature-next" hidden>Pick another</button>
      </div>
    </section>"""

    added = sorted(recipes, key=lambda r: r["added"], reverse=True)[:RECENT_COUNT]
    recent = "".join(
        f'<li><a href="{r["url"]}">{html.escape(r["title"])}</a>'
        f'<span>{html.escape(r["cuisine"])} · {nice_date(r["added"])}</span></li>'
        for r in added
    )

    quote = ""
    if notes:
        day, r, text = notes[0]
        more = "".join(
            f'<li><a href="{nr["url"]}">{html.escape(nr["title"])}</a> <span>{inline(nt)}</span></li>'
            for _, nr, nt in notes[1:NOTES_COUNT]
        )
        quote = f"""
    <section class="tile tile-note reveal">
      <p class="eyebrow">From our kitchen</p>
      <blockquote>{inline(text)}</blockquote>
      <p class="note-source"><a href="{r['url']}">{html.escape(r['title'])}</a> · {nice_date(day)}</p>
      <ul class="note-more">{more}</ul>
    </section>"""

    cards = []
    for i, (cuisine, cats) in enumerate(book.items()):
        n = sum(len(rs) for rs in cats.values())
        tags = "".join(f'<span class="tag">{html.escape(c)}</span>' for c in cats)
        items = "".join(
            f'<li data-tags="{" ".join(r["tags"])}">'
            + (f'<img class="thumb" src="{r["photo"]}" alt="" loading="lazy">' if r.get("photo") else "")
            + f'<div><a href="{r["url"]}"{vt_name("r", r["url"][:-5])}>{html.escape(r["title"])}</a>'
            f'<span>{html.escape(r.get("time") or "Serves " + r["serves"])}</span></div></li>'
            for rs in cats.values() for r in rs
        )
        cards.append(f"""
      <article class="kitchen filter-group tone-{i % TONES + 1} reveal" data-limit="{KITCHEN_CARD_RECIPES}" data-tilt>
        {cuisine_art(cuisine, "kitchen-art")}
        <header>
          <h3><a href="{cuisine_url(cuisine)}"{vt_name("c", cuisine)}>{html.escape(cuisine)}</a></h3>
          <span class="kitchen-count">{n}</span>
        </header>
        <div class="tags">{tags}</div>
        <ul>{items}</ul>
        <a class="kitchen-more" href="{cuisine_url(cuisine)}">{f"All {n} {html.escape(cuisine)} recipes" if n > KITCHEN_CARD_RECIPES else f"All {html.escape(cuisine)} recipes"} →</a>
      </article>""")

    content = f"""
  <div class="bento">
    <header class="tile tile-hero reveal">
      {hat}
      <h1>{TITLE}</h1>
      <p class="hero-sub">{SUBTITLE}</p>
      <ul class="stats">
        <li><strong>{count}</strong> {'recipe' if count == 1 else 'recipes'}</li>
        <li><strong>{cuisines}</strong> {'cuisine' if cuisines == 1 else 'cuisines'}</li>
        <li><strong>{len(notes)}</strong> {'kitchen note' if len(notes) == 1 else 'kitchen notes'}</li>
      </ul>
      <div class="tile-actions">
        <a class="pill pill-solid" href="#kitchens">Browse the kitchens</a>
        <a class="pill pill-outline" href="{COOK_PAGE}">{svg_icon("sparkle")}What can I cook?</a>
      </div>
    </header>{feature}
    <section class="tile tile-recent reveal">
      <p class="eyebrow">Recently added</p>
      <ul>{recent}</ul>
    </section>{quote}
  </div>
{world_map(book)}
  <section class="kitchens filter-scope" id="kitchens" aria-label="Contents">
    <div class="section-head reveal">
      <h2>The Kitchens</h2>
      <p>{plural(count, 'recipe')} across {plural(cuisines, 'cuisine')}, every one cooked at our table.</p>
    </div>
    {chips_html(recipes)}
    <div class="kitchen-grid">{"".join(cards)}
    </div>
  </section>
  <script src="{HOME_SCRIPT}" defer></script>"""
    return page(book, 0, TITLE, content, main_class="home")


def recipe_card(r, href):
    photo = f'<img class="card-photo" src="../{r["photo"]}" alt="" loading="lazy">' if r.get("photo") else ""
    facts = "".join(f'<span><b>{html.escape(label)}</b> {html.escape(value)}</span>' for label, value in time_facts(r))
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in quick_tag_labels(r))
    return f"""
      <a class="recipe-card reveal" href="{href}" data-tags="{" ".join(r["tags"])}" data-tilt>
        {photo}
        <h3{vt_name("r", r["url"][:-5])}>{html.escape(r["title"])}</h3>
        <p class="card-intro">{html.escape(intro(r))}</p>
        <div class="card-facts"><span><b>Serves</b> {html.escape(r["serves"])}</span>{facts}</div>
        <div class="tags">{tags}</div>
      </a>"""


def cuisine_html(book, cuisine):
    cats = book[cuisine]
    recipes = [r for rs in cats.values() for r in rs]
    tone = recipes[0]["tone"]
    n = len(recipes)
    groups = "".join(
        f'<section class="style-group filter-group"><h2>{html.escape(category)}</h2><div class="recipe-cards">'
        + "".join(recipe_card(r, r["url"].split("/", 1)[1]) for r in rs)
        + "</div></section>"
        for category, rs in cats.items()
    )
    styles = "".join(f'<span class="tag">{html.escape(c)}</span>' for c in cats)
    content = f"""
  <header class="cuisine-hero tone-{tone} reveal">
    {cuisine_art(cuisine, "hero-art")}
    <p class="eyebrow">The {html.escape(cuisine)} kitchen</p>
    <h1{vt_name("c", cuisine)}>{html.escape(cuisine)}</h1>
    <p class="hero-count">{n} recipe{'s' if n != 1 else ''}</p>
    <div class="tags">{styles}</div>
  </header>
  <div class="filter-scope">
    {chips_html(recipes, with_styles=False)}
    {groups}
  </div>"""
    return page(book, 1, f"{cuisine} · {TITLE}", content, current=cuisine, main_class="wide")


def notes_panel(md):
    """The Notes section as two groups: undated tips, and our dated changes."""
    tips, changes = [], []
    for line in bullets(md):
        m = re.match(r"(\d{4}-\d{2}-\d{2}): (.+)", line)
        if m:
            changes.append(f'<li><time datetime="{m.group(1)}">{nice_date(m.group(1))}</time><p>{inline(m.group(2))}</p></li>')
        else:
            tips.append(f"<li>{inline(line)}</li>")
    if not tips and not changes:
        return ""
    out = ['<section class="notes-panel reveal"><h2>From our kitchen</h2><div class="notes-columns">']
    if tips:
        out.append(f'<div><h3>Good to know</h3><ul class="tips">{"".join(tips)}</ul></div>')
    if changes:
        out.append(f'<div><h3>How we make it</h3><ol class="changes">{"".join(changes)}</ol></div>')
    out.append("</div></section>")
    return "".join(out)


def recipe_page_html(book, r, prev, nxt):
    root = "../../"
    intro_md, parts = sections(r["body"])
    serves = re.match(r"\d+", r["serves"])
    if serves:
        # The scaler starts from the first number; whatever follows it is shown underneath.
        # A range ("2–3") reads oddly as "–3", so ranges show in full instead.
        rest = r["serves"][len(serves.group()):].strip()
        if re.match(r"[–-]\s*\d", rest):
            rest = f"recipe says {r['serves']}"
        serves_html = (f'<div class="scaler" data-base="{serves.group()}">'
                       '<button type="button" class="scale-down" aria-label="Fewer servings">−</button>'
                       f'<output aria-live="polite">{serves.group()}</output>'
                       '<button type="button" class="scale-up" aria-label="More servings">+</button></div>'
                       + (f'<small>{html.escape(rest)}</small>' if rest else ""))
    else:
        serves_html = f'<strong>{html.escape(r["serves"])}</strong>'
    facts = (f'<div class="fact fact-serves"><span>Serves</span>{serves_html}</div>'
             + "".join(f'<div class="fact"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
                       for label, value in time_facts(r)))
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in quick_tag_labels(r))
    photo = (f'<figure class="hero-photo"><img src="{root}{r["photo"]}" alt="{html.escape(r["title"])}"></figure>'
             if r.get("photo") else "")
    options = ""
    if parts.get("Topping Options"):
        options = f'<section class="options"><h2>Topping options</h2>{render(parts["Topping Options"])}</section>'
    pager = []
    if prev:
        pager.append(f'<a class="prev" href="{root}{prev["url"]}"><span>Previous</span>{html.escape(prev["title"])}</a>')
    if nxt:
        pager.append(f'<a class="next" href="{root}{nxt["url"]}"><span>Next</span>{html.escape(nxt["title"])}</a>')
    content = f"""<div class="read-progress" aria-hidden="true"></div>
<article class="recipe-page" data-url="{r['url']}">
  <header class="recipe-hero tone-{r['tone']}{' has-photo' if photo else ''}">
    {cuisine_art(r["cuisine"], "hero-art")}
    <div class="hero-text">
      <p class="kicker"><a href="{root}{cuisine_url(r['cuisine'])}">{html.escape(r['cuisine'])}</a> · {html.escape(r['category'])}</p>
      <h1{vt_name("r", r["url"][:-5])}>{html.escape(r['title'])}</h1>
      {f'<p class="hero-intro">{inline(" ".join(intro_md.split()))}</p>' if intro_md else ''}
      <div class="facts">{facts}</div>
      {f'<div class="tags">{tags}</div>' if tags else ''}
      <div class="hero-actions">
        <button type="button" class="pill pill-solid start-cooking" hidden>{svg_icon("play")}Start cooking</button>
        <button type="button" class="pill pill-outline add-to-list" hidden>{svg_icon("plus")}Add to shopping list</button>
      </div>
    </div>
    {photo}
  </header>
  <div class="recipe-tabs" role="tablist" aria-label="Recipe sections" hidden>
    <button type="button" role="tab" aria-selected="true" data-tab="ingredients">Ingredients</button>
    <button type="button" role="tab" aria-selected="false" data-tab="method">Method</button>
  </div>
  <div class="recipe-layout" data-tab="ingredients">
    <aside class="ingredients-panel" aria-label="Ingredients">
      <h2>Ingredients</h2>
      <p class="scale-note" hidden>Amounts with a number are scaled and rounded. Amounts in the method, and things like "to taste" or "a handful", stay as written.</p>
      {render(parts.get("Ingredients", ""))}
      <p class="panel-hint">Tick things off as you go. Tap an ingredient's name to see where it's used.</p>
    </aside>
    <div class="method-panel">
      <h2>Method</h2>
      {render(parts.get("Method", ""))}
      {options}
    </div>
  </div>
  {notes_panel(parts.get("Notes"))}
  {source_html(r)}
</article>
<nav class="pager" aria-label="More recipes">{"".join(pager)}</nav>
<script src="{root}{RECIPE_SCRIPT}" defer></script>"""
    return page(book, 2, f"{r['title']} · {TITLE}", content, current=r["cuisine"], main_class="wide")


def list_html(book):
    content = f"""
  <header class="page-hero">
    <p class="eyebrow">Shopping list</p>
    <h1>Shopping list</h1>
    <p class="list-summary">Add recipes from their page with "Add to shopping list". Amounts are combined and sorted by aisle.</p>
    <div class="hero-actions list-actions" hidden>
      <button type="button" class="pill pill-solid list-share">Share or copy</button>
      <button type="button" class="pill pill-outline list-print">{svg_icon("printer")}Print</button>
      <button type="button" class="pill pill-outline list-clear">Clear list</button>
    </div>
  </header>
  <div class="list-recipes"></div>
  <div class="list-aisles"></div>
  <p class="list-empty" hidden>Your list is empty. Open a recipe and choose "Add to shopping list".</p>
  <script src="{TOOLS_SCRIPT}" defer></script>"""
    return page(book, 0, f"Shopping list · {TITLE}", content, current=LIST_PAGE, main_class="wide")


def cook_html(book):
    """'What can I cook?': every non-staple ingredient as a chip, grouped by aisle."""
    by_aisle = {}
    for r in all_recipes(book):
        _, parts = sections(r["body"])
        for line in bullets(parts.get("Ingredients")):
            item = parse_line(line)
            if item["n"] and not item["s"]:
                by_aisle.setdefault(item["a"], set()).add(item["n"])
    groups = "".join(
        f'<fieldset class="pantry-group"><legend>{html.escape(aisle)}</legend>'
        + "".join(f'<button type="button" class="chip" aria-pressed="false" data-ingredient="{html.escape(name)}">{html.escape(name)}</button>'
                  for name in sorted(by_aisle[aisle]))
        + "</fieldset>"
        for aisle in AISLES if aisle in by_aisle
    )
    content = f"""
  <header class="page-hero">
    <p class="eyebrow">{svg_icon("sparkle")}What can I cook?</p>
    <h1>Cook with what you have</h1>
    <p>Tap what's in your fridge and pantry. Salt, pepper, oil, sugar and water are assumed.</p>
    <div class="hero-actions"><button type="button" class="pill pill-outline pantry-clear">Clear</button></div>
  </header>
  <div class="cook-layout">
    <div class="pantry">{groups}</div>
    <section class="matches" aria-live="polite">
      <h2>Best matches</h2>
      <p class="matches-empty">Pick a few ingredients to see what you can make.</p>
      <ol class="match-list"></ol>
    </section>
  </div>
  <script src="{TOOLS_SCRIPT}" defer></script>"""
    return page(book, 0, f"What can I cook? · {TITLE}", content, current=COOK_PAGE, main_class="wide")


def book_html(book):
    body = []
    for cuisine, cats in book.items():
        cid = slug(cuisine)
        body.append(f'<section class="cuisine" id="{cid}"><h2>{html.escape(cuisine)}</h2>')
        for category, recipes in cats.items():
            body.append(f'<p class="category-list">{html.escape(category)}: '
                        + ", ".join(html.escape(r["title"]) for r in recipes) + "</p>")
        body.append("</section>")
        for recipes in cats.values():
            for r in recipes:
                body.append(recipe_html(r, anchor=slug(r["url"][:-5])))
    toc = toc_html(book, lambda x: f"#{slug(x)}" if isinstance(x, str) else f"#{slug(x['url'][:-5])}")
    template = (TEMPLATES / "book.html").read_text(encoding="utf-8")
    return (template.replace("{{TITLE}}", TITLE)
                    .replace("{{SUBTITLE}}", SUBTITLE)
                    .replace("{{NAV}}", nav_html(book, "", BOOK_PAGE))
                    .replace("{{PRINT_ICON}}", svg_icon("printer"))
                    .replace("{{CONTENTS}}", toc)
                    .replace("{{BODY}}", "\n".join(body)))


def manifest():
    return json.dumps({
        "name": TITLE,
        "short_name": "Field Kitchen",
        "description": SUBTITLE,
        "start_url": "./index.html",
        "scope": "./",
        "display": "standalone",
        "background_color": BACKGROUND_COLOR,
        "theme_color": THEME_COLOR,
        "icons": [{"src": name, "sizes": name[5:-4] + "x" + name[5:-4], "type": "image/png", "purpose": "any"}
                  for name in APP_ICONS] + [{"src": ICON, "sizes": "any", "type": "image/svg+xml"}],
    }, indent=2) + "\n"


def service_worker():
    """sw.js with the list of every file to keep offline and a version that changes with them."""
    files = sorted(p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*")
                   if p.is_file() and p.name not in KEEP_IN_DOCS)
    digest = hashlib.sha256()
    for name in files:
        digest.update(name.encode())
        digest.update((DOCS / name).read_bytes())
    template = (TEMPLATES / SERVICE_WORKER).read_text(encoding="utf-8")
    return (template.replace("{{VERSION}}", digest.hexdigest()[:12])
                    .replace("{{FILES}}", json.dumps(["./"] + files, indent=2)))


def write(rel, text):
    path = DOCS / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_site(book):
    # Clear old output so renamed or moved recipes don't leave stale pages behind.
    for p in DOCS.iterdir():
        if p.name in KEEP_IN_DOCS:
            continue
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    for asset in (STYLESHEET, ICON, SITE_SCRIPT, HOME_SCRIPT, RECIPE_SCRIPT, TOOLS_SCRIPT):
        write(asset, (TEMPLATES / asset).read_text(encoding="utf-8"))
    for name in APP_ICONS:
        shutil.copyfile(TEMPLATES / name, DOCS / name)
    write(MANIFEST, manifest())
    write(SEARCH_INDEX, search_index(book))
    write("index.html", home_html(book))
    write(LIST_PAGE, list_html(book))
    write(COOK_PAGE, cook_html(book))
    write(BOOK_PAGE, book_html(book))
    for cuisine in book:
        write(cuisine_url(cuisine), cuisine_html(book, cuisine))
    recipes = all_recipes(book)
    for i, r in enumerate(recipes):
        prev = recipes[i - 1] if i > 0 else None
        nxt = recipes[i + 1] if i + 1 < len(recipes) else None
        write(r["url"], recipe_page_html(book, r, prev, nxt))
        if r.get("photo"):
            (DOCS / "photos").mkdir(exist_ok=True)
            shutil.copyfile(r["photo_source"], DOCS / r["photo"])
    # Last, so its file list and version cover everything above.
    write(SERVICE_WORKER, service_worker())


def main():
    book = load()
    update_readme(book)
    DOCS.mkdir(exist_ok=True)
    build_site(book)
    photos = sum(1 for r in all_recipes(book) if r.get("photo"))
    print(f"Built {len(all_recipes(book))} recipe(s) across {len(book)} cuisine(s), {photos} with photos.")


if __name__ == "__main__":
    main()
