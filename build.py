"""Build The Field Kitchen.

Reads every recipe in recipes/<Cuisine>/<Style>/*.md (plus any matching photo in
photos/) and regenerates:
  - the Contents section of README.md (between the CONTENTS markers)
  - the website in docs/ (served by GitHub Pages): a home page, one page per
    cuisine, one page per recipe, and docs/book.html, the whole book for printing
  - docs/search-index.js, the recipe index the site search and home page read
  - docs/sw.js and docs/manifest.webmanifest, so the site installs and works offline

Standard library only. Run:  python build.py
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

ROOT = Path(__file__).parent
RECIPES = ROOT / "recipes"
PHOTOS = ROOT / "photos"
README = ROOT / "README.md"
TEMPLATES = ROOT / "templates"
DOCS = ROOT / "docs"
BOOK_PAGE = "book.html"
STYLESHEET = "style.css"
ICON = "icon.svg"
APP_ICONS = ("icon-192.png", "icon-512.png")
SITE_SCRIPT = "site.js"
HOME_SCRIPT = "home.js"
RECIPE_SCRIPT = "recipe.js"
SEARCH_INDEX = "search-index.js"
MANIFEST = "manifest.webmanifest"
SERVICE_WORKER = "sw.js"
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
PHOTO_WARN_BYTES = 1_500_000
RECENT_COUNT = 5
NOTES_COUNT = 3
TONES = 6  # colour tones for the cuisine cards, .tone-1 to .tone-6 in style.css
QUICK_MINUTES = 30
PROJECT_MINUTES = 150
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
    "flame": '<path d="M12 3c.5 3 5 5 5 10a5 5 0 0 1-10 0c0-2.5 1.5-4 2.5-5 .3 1.5 1.2 2.5 2.5 2.5-.5-2.5-.5-5 0-7.5z"/>',
}
# Line drawings (64x64, stroked) shown on cuisine cards and pages; new cuisines get the plate.
CUISINE_ART = {
    "british": ('<ellipse cx="30" cy="38" rx="16" ry="13"/><path d="M22 25h16M28 25v-4h4v4"/>'
                '<path d="M14 37c-6 0-8-6-11-9"/><path d="M46 31c9 0 9 13 0 13"/><path d="M18 51h24"/>'),
    "chinese": ('<path d="M6 30h46a23 17 0 0 1-46 0z"/><path d="M52 32l9-2"/>'
                '<path d="M20 22c-2-4 2-6 0-10M29 22c-2-4 2-6 0-10M38 22c-2-4 2-6 0-10"/>'),
    "indian": ('<path d="M14 28h36l-4 21a7 7 0 0 1-7 6H25a7 7 0 0 1-7-6z"/><path d="M11 28h42"/>'
               '<path d="M14 35h-5M50 35h5"/><path d="M26 20c-2-3 2-5 0-8M33 20c-2-3 2-5 0-8M40 20c-2-3 2-5 0-8"/>'),
    "italian": ('<path d="M8 34h48a24 16 0 0 1-48 0z"/>'
                '<path d="M16 34c2-8 6-8 8 0s6-8 8 0 6-8 8 0 6-8 8 0"/><path d="M47 6v24M43 6v7a4 4 0 0 0 8 0V6"/>'),
    "japanese": ('<path d="M8 32h46a23 18 0 0 1-46 0z"/><path d="M15 32c4-11 28-11 32 0"/>'
                 '<path d="M30 21 58 7M34 24 60 12"/>'),
    "south african": ('<path d="M14 24h36v12a18 16 0 0 1-36 0z"/><path d="M11 24h42"/>'
                      '<path d="M18 24c0-11 28-11 28 0"/><path d="M21 48l-5 9M32 52v7M43 48l5 9"/>'),
    "spanish": ('<ellipse cx="32" cy="38" rx="24" ry="10"/><path d="M8 38H2M56 38h6"/>'
                '<circle cx="23" cy="36" r="3"/><circle cx="39" cy="41" r="3"/><path d="M29 33c4-3 8 0 6 4"/>'
                '<path d="M42 33c2-2 5-1 5 1"/>'),
    "_plate": ('<circle cx="32" cy="34" r="17"/><circle cx="32" cy="34" r="10"/>'
               '<path d="M7 16v34M4 16v8a3 3 0 0 0 6 0v-8M57 16c-4 4-4 15 0 17v17"/>'),
}
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
    return {c: dict(sorted(cats.items())) for c, cats in sorted(book.items())}


def all_recipes(book):
    return [r for cats in book.values() for recipes in cats.values() for r in recipes]


def total_minutes(r):
    """Sum of every '<n> min' and '<n> hr' in the time line (upper end of ranges), or None."""
    time = r.get("time", "")
    found = re.findall(r"(\d+(?:\.\d+)?)\s*(hr|min)", time)
    if not found:
        return None
    return sum(float(n) * (60 if unit == "hr" else 1) for n, unit in found)


def recipe_tags(r):
    """Quick-filter tags for the home page chips, plus the recipe's style."""
    tags = [slug(r["category"])]
    minutes = total_minutes(r)
    text = (r.get("time", "") + " " + r["body"]).lower()
    ahead = re.search(r"day before|make ahead|made ahead|make these ahead|ahead of time|curing|drying", text)
    if minutes is not None and minutes <= QUICK_MINUTES and not ahead:
        tags.append("quick")
    if ahead:
        tags.append("make-ahead")
    if (minutes is not None and minutes >= PROJECT_MINUTES) or "day before" in r.get("time", "").lower():
        tags.append("project")
    return tags


QUICK_CHIPS = (("quick", f"Under {QUICK_MINUTES} min"), ("make-ahead", "Make ahead"), ("project", "Weekend project"))


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
    paths = CUISINE_ART.get(cuisine.lower(), CUISINE_ART["_plate"])
    return (f'<svg class="{css}" aria-hidden="true" viewBox="0 0 64 64" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')


def intro(r):
    """The recipe's opening paragraph, before ## Ingredients, as plain text."""
    head = r["body"].split("\n## ", 1)[0].strip()
    return re.sub(r"[*_]", "", " ".join(head.split()))


def search_index(book):
    """Title, place in the book, ingredient lines and card details for each recipe."""
    entries = []
    for r in all_recipes(book):
        m = re.search(r"^## Ingredients\n(.*?)(?=^## )", r["body"], re.S | re.M)
        lines = re.findall(r"^- (.*)", m.group(1), re.M) if m else []
        entries.append({"title": r["title"], "cuisine": r["cuisine"], "category": r["category"],
                        "url": r["url"], "text": " ".join(lines),
                        "meta": html.unescape(meta_line(r)), "intro": intro(r),
                        "photo": r.get("photo", "")})
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
    print_here = ' aria-current="page"' if current == BOOK_PAGE else ""
    return f"""<nav class="site-nav" aria-label="Site" data-root="{root}">
  <div class="inner">
    <a class="home" href="{root}index.html">{icon_inline()}{TITLE}</a>
    <div class="menu" id="site-menu">
      <div class="cuisine-menu">
        <button type="button" class="nav-button cuisine-toggle{in_cuisine}" aria-expanded="false" aria-controls="cuisine-list">Cuisines{svg_icon("chevron", "chevron")}</button>
        <ul class="cuisine-list" id="cuisine-list">{"".join(links)}</ul>
      </div>
      <a class="nav-button print" href="{root}{BOOK_PAGE}"{print_here}>{svg_icon("printer")}Print</a>
      <form class="search" role="search">
        <label class="search-field">{svg_icon("search")}<input type="search" placeholder="Search recipes" aria-label="Search recipes or ingredients" autocomplete="off"><kbd>/</kbd></label>
        <ul class="search-results" hidden></ul>
      </form>
    </div>
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


def recipe_html(r, root="", anchor=None, kicker=None, css="recipe", tools="", title_attr=""):
    source = ""
    if r.get("source"):
        s = r["source"]
        label = html.escape(re.sub(r"^https?://(www\.)?", "", s).split("/")[0])
        s_html = f'<a href="{html.escape(s)}">{label}</a>' if s.startswith("http") else html.escape(s)
        source = f'<p class="source">Source: {s_html}</p>'
    photo = ""
    if r.get("photo"):
        photo = (f'<figure class="recipe-photo"><img src="{root}{r["photo"]}" '
                 f'alt="{html.escape(r["title"])}" loading="lazy"></figure>')
    kicker = kicker or f"{html.escape(r['cuisine'])} · {html.escape(r['category'])}"
    id_attr = f' id="{anchor}"' if anchor else ""
    return f"""
<article class="{css}"{id_attr}>
  {photo}
  <p class="kicker">{kicker}</p>
  <h3{title_attr}>{html.escape(r['title'])}</h3>
  <p class="meta">{meta_line(r)}</p>
  {tools}
  {render(r['body'])}
  {source}
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

    # Chips: the quick filters that match at least one recipe, then every style.
    tag_counts = {}
    for r in recipes:
        for t in r["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    styles = sorted({r["category"] for r in recipes})
    chip_list = [(key, label) for key, label in QUICK_CHIPS if tag_counts.get(key)]
    chip_list += [(slug(s), s) for s in styles]
    chips = '<button type="button" class="chip" data-filter="" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" class="chip" data-filter="{key}" aria-pressed="false">'
        f'{html.escape(label)}<small>{tag_counts[key]}</small></button>'
        for key, label in chip_list
    )

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
      <article class="kitchen tone-{i % TONES + 1} reveal">
        {cuisine_art(cuisine, "kitchen-art")}
        <header>
          <h3><a href="{cuisine_url(cuisine)}"{vt_name("c", cuisine)}>{html.escape(cuisine)}</a></h3>
          <span class="kitchen-count">{n}</span>
        </header>
        <div class="tags">{tags}</div>
        <ul>{items}</ul>
        <a class="kitchen-more" href="{cuisine_url(cuisine)}">All {html.escape(cuisine)} recipes →</a>
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
        <a class="pill pill-outline" href="{BOOK_PAGE}">Print the book</a>
      </div>
    </header>{feature}
    <section class="tile tile-recent reveal">
      <p class="eyebrow">Recently added</p>
      <ul>{recent}</ul>
    </section>{quote}
  </div>

  <section class="kitchens" id="kitchens" aria-label="Contents">
    <div class="section-head reveal">
      <h2>The Kitchens</h2>
      <p>{plural(count, 'recipe')} across {plural(cuisines, 'cuisine')}, every one cooked at our table.</p>
    </div>
    <div class="chips" role="group" aria-label="Filter recipes" hidden>{chips}</div>
    <p class="filter-empty" hidden>Nothing matches that filter yet.</p>
    <div class="kitchen-grid">{"".join(cards)}
    </div>
  </section>
  <script src="{HOME_SCRIPT}" defer></script>"""
    return page(book, 0, TITLE, content, main_class="home")


def cuisine_html(book, cuisine):
    groups = []
    for category, recipes in book[cuisine].items():
        items = "\n".join(
            f'<li><a href="{r["url"].split("/", 1)[1]}"{vt_name("r", r["url"][:-5])}>{html.escape(r["title"])}</a>'
            f'<span class="meta">{meta_line(r)}</span></li>'
            for r in recipes
        )
        groups.append(f'<section class="style-group"><h2>{html.escape(category)}</h2>\n'
                      f'<ul class="recipe-list">\n{items}\n</ul></section>')
    content = (f'<header class="page-head">{cuisine_art(cuisine, "cuisine-art")}'
               f'<h1{vt_name("c", cuisine)}>{html.escape(cuisine)}</h1>'
               f'<div class="ornament">· · ·</div></header>\n' + "\n".join(groups))
    return page(book, 1, f"{cuisine} · {TITLE}", content, current=cuisine)


def recipe_page_html(book, r, prev, nxt):
    root = "../../"
    kicker = (f'<a href="{root}{cuisine_url(r["cuisine"])}">{html.escape(r["cuisine"])}</a>'
              f' · {html.escape(r["category"])}')
    serves = re.match(r"\d+", r["serves"])
    scaler = ""
    if serves:
        scaler = (f'<div class="scaler" data-base="{serves.group()}"><span>Serves</span>'
                  '<button type="button" class="scale-down" aria-label="Fewer servings">−</button>'
                  f'<output aria-live="polite">{serves.group()}</output>'
                  '<button type="button" class="scale-up" aria-label="More servings">+</button></div>')
    tools = (f'<div class="recipe-tools" hidden>{scaler}'
             f'<button type="button" class="pill pill-outline cook-toggle" aria-pressed="false">'
             f'{svg_icon("flame")}Cook mode</button></div>'
             '<p class="scale-note" hidden>Amounts with a number are scaled and rounded. '
             'Amounts in the method, and things like "to taste" or "a handful", stay as written.</p>')
    pager = []
    if prev:
        pager.append(f'<a class="prev" href="{root}{prev["url"]}"><span>Previous</span>{html.escape(prev["title"])}</a>')
    if nxt:
        pager.append(f'<a class="next" href="{root}{nxt["url"]}"><span>Next</span>{html.escape(nxt["title"])}</a>')
    content = ('<div class="read-progress" aria-hidden="true"></div>'
               + recipe_html(r, root=root, kicker=kicker, css="recipe solo", tools=tools,
                             title_attr=vt_name("r", r["url"][:-5]))
               + f'\n<nav class="pager" aria-label="More recipes">{"".join(pager)}</nav>'
               + f'\n<script src="{root}{RECIPE_SCRIPT}" defer></script>')
    return page(book, 2, f"{r['title']} · {TITLE}", content, current=r["cuisine"])


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
    for asset in (STYLESHEET, ICON, SITE_SCRIPT, HOME_SCRIPT, RECIPE_SCRIPT):
        write(asset, (TEMPLATES / asset).read_text(encoding="utf-8"))
    for name in APP_ICONS:
        shutil.copyfile(TEMPLATES / name, DOCS / name)
    write(MANIFEST, manifest())
    write(SEARCH_INDEX, search_index(book))
    write("index.html", home_html(book))
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
