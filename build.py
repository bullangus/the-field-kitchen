"""Build The Field Kitchen.

Reads every recipe in recipes/<Cuisine>/<Style>/*.md and regenerates:
  - the Contents section of README.md (between the CONTENTS markers)
  - the website in docs/ (served by GitHub Pages): a home page with the
    contents, one page per cuisine, one page per recipe
  - docs/book.html, the complete book on one page, for printing

Standard library only. Run:  python build.py
"""

import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RECIPES = ROOT / "recipes"
README = ROOT / "README.md"
TEMPLATES = ROOT / "templates"
DOCS = ROOT / "docs"
BOOK_PAGE = "book.html"
STYLESHEET = "style.css"
TITLE = "The Field Kitchen"
SUBTITLE = "Recipes from our family table"

REQUIRED = ("title", "cuisine", "category", "serves")
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


def load():
    book = {}
    for path in sorted(RECIPES.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        r = parse(path)
        book.setdefault(r["cuisine"], {}).setdefault(r["category"], []).append(r)
    for cats in book.values():
        for recipes in cats.values():
            recipes.sort(key=lambda r: r["title"].lower())
    return {c: dict(sorted(cats.items())) for c, cats in sorted(book.items())}


def all_recipes(book):
    return [r for cats in book.values() for recipes in cats.values() for r in recipes]


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


def meta_line(r):
    meta = [f"Serves {html.escape(r['serves'])}"]
    if r.get("time"):
        meta.append(html.escape(r["time"]))
    return " · ".join(meta)


def nav_html(book, root, current=None):
    links = []
    for cuisine in book:
        here = ' aria-current="page"' if cuisine == current else ""
        links.append(f'<li><a href="{root}{cuisine_url(cuisine)}"{here}>{html.escape(cuisine)}</a></li>')
    here = ' aria-current="page"' if current == BOOK_PAGE else ""
    links.append(f'<li><a href="{root}{BOOK_PAGE}"{here}>Print the book</a></li>')
    return f"""<nav class="site-nav" aria-label="Site">
  <div class="inner">
    <a class="home" href="{root}index.html">{TITLE}</a>
    <ul>{"".join(links)}</ul>
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


def recipe_html(r, anchor=None, kicker=None, css="recipe"):
    source = ""
    if r.get("source"):
        s = r["source"]
        label = html.escape(re.sub(r"^https?://(www\.)?", "", s).split("/")[0])
        s_html = f'<a href="{html.escape(s)}">{label}</a>' if s.startswith("http") else html.escape(s)
        source = f'<p class="source">Source: {s_html}</p>'
    kicker = kicker or f"{html.escape(r['cuisine'])} · {html.escape(r['category'])}"
    id_attr = f' id="{anchor}"' if anchor else ""
    return f"""
<article class="{css}"{id_attr}>
  <p class="kicker">{kicker}</p>
  <h3>{html.escape(r['title'])}</h3>
  <p class="meta">{meta_line(r)}</p>
  {render(r['body'])}
  {source}
</article>"""


def page(book, depth, page_title, content, current=None):
    root = "../" * depth
    template = (TEMPLATES / "page.html").read_text(encoding="utf-8")
    return (template.replace("{{PAGE_TITLE}}", html.escape(page_title))
                    .replace("{{ROOT}}", root)
                    .replace("{{NAV}}", nav_html(book, root, current))
                    .replace("{{CONTENT}}", content))


def home_html(book):
    toc = toc_html(book, lambda x: cuisine_url(x) if isinstance(x, str) else x["url"])
    content = f"""  <header class="cover home-cover">
    <h1>{TITLE}</h1>
    <div class="ornament">· · ·</div>
    <p>{SUBTITLE}</p>
  </header>

  <nav class="contents" aria-label="Contents">
    <h2>Contents</h2>
    <ul>
{toc}
    </ul>
  </nav>

  <p class="print-link">Want it on paper? <a href="{BOOK_PAGE}">Open the whole book</a>, then Print and Save as PDF.</p>"""
    return page(book, 0, TITLE, content)


def cuisine_html(book, cuisine):
    groups = []
    for category, recipes in book[cuisine].items():
        items = "\n".join(
            f'<li><a href="{r["url"].split("/", 1)[1]}">{html.escape(r["title"])}</a>'
            f'<span class="meta">{meta_line(r)}</span></li>'
            for r in recipes
        )
        groups.append(f'<section class="style-group"><h2>{html.escape(category)}</h2>\n'
                      f'<ul class="recipe-list">\n{items}\n</ul></section>')
    content = (f'<header class="page-head"><h1>{html.escape(cuisine)}</h1>'
               f'<div class="ornament">· · ·</div></header>\n' + "\n".join(groups))
    return page(book, 1, f"{cuisine} · {TITLE}", content, current=cuisine)


def recipe_page_html(book, r, prev, nxt):
    root = "../../"
    kicker = (f'<a href="{root}{cuisine_url(r["cuisine"])}">{html.escape(r["cuisine"])}</a>'
              f' · {html.escape(r["category"])}')
    pager = []
    if prev:
        pager.append(f'<a class="prev" href="{root}{prev["url"]}"><span>Previous</span>{html.escape(prev["title"])}</a>')
    if nxt:
        pager.append(f'<a class="next" href="{root}{nxt["url"]}"><span>Next</span>{html.escape(nxt["title"])}</a>')
    content = (recipe_html(r, kicker=kicker, css="recipe solo")
               + f'\n<nav class="pager" aria-label="More recipes">{"".join(pager)}</nav>')
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
    write(STYLESHEET, (TEMPLATES / STYLESHEET).read_text(encoding="utf-8"))
    write("index.html", home_html(book))
    write(BOOK_PAGE, book_html(book))
    for cuisine in book:
        write(cuisine_url(cuisine), cuisine_html(book, cuisine))
    recipes = all_recipes(book)
    for i, r in enumerate(recipes):
        prev = recipes[i - 1] if i > 0 else None
        nxt = recipes[i + 1] if i + 1 < len(recipes) else None
        write(r["url"], recipe_page_html(book, r, prev, nxt))


def main():
    book = load()
    update_readme(book)
    DOCS.mkdir(exist_ok=True)
    build_site(book)
    print(f"Built {len(all_recipes(book))} recipe(s) across {len(book)} cuisine(s).")


if __name__ == "__main__":
    main()
