"""Build The Field Kitchen.

Reads every recipe in recipes/<Cuisine>/<Style>/*.md and regenerates:
  - the Contents section of README.md (between the CONTENTS markers)
  - docs/index.html, the complete print-ready book (served by GitHub Pages)

Standard library only. Run:  python build.py
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RECIPES = ROOT / "recipes"
README = ROOT / "README.md"
BOOK = ROOT / "docs" / "index.html"
TITLE = "The Field Kitchen"
SUBTITLE = "Recipes from our family table"

REQUIRED = ("title", "cuisine", "category", "serves")


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
    count = sum(len(rs) for cats in book.values() for rs in cats.values())
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
    README.write_text(new, encoding="utf-8")


def recipe_html(r, anchor):
    meta = [f"Serves {html.escape(r['serves'])}"]
    if r.get("time"):
        meta.append(html.escape(r["time"]))
    source = ""
    if r.get("source"):
        s = r["source"]
        label = html.escape(re.sub(r"^https?://(www\.)?", "", s).split("/")[0])
        s_html = f'<a href="{html.escape(s)}">{label}</a>' if s.startswith("http") else html.escape(s)
        source = f'<p class="source">Source: {s_html}</p>'
    return f"""
<article class="recipe" id="{anchor}">
  <p class="kicker">{html.escape(r['cuisine'])} · {html.escape(r['category'])}</p>
  <h3>{html.escape(r['title'])}</h3>
  <p class="meta">{' · '.join(meta)}</p>
  {render(r['body'])}
  {source}
</article>"""


def build_html(book):
    toc, body = [], []
    for cuisine, cats in book.items():
        cid = slug(cuisine)
        toc.append(f'<li class="toc-cuisine"><a href="#{cid}">{html.escape(cuisine)}</a><ul>')
        body.append(f'<section class="cuisine" id="{cid}"><h2>{html.escape(cuisine)}</h2>')
        for category, recipes in cats.items():
            kid = f"{cid}-{slug(category)}"
            toc.append(f'<li class="toc-category"><span>{html.escape(category)}</span><ul>')
            body.append(f'<p class="category-list" id="{kid}">{html.escape(category)}: '
                        + ", ".join(html.escape(r["title"]) for r in recipes) + "</p>")
            for r in recipes:
                rid = f"{kid}-{slug(r['title'])}"
                toc.append(f'<li><a href="#{rid}">{html.escape(r["title"])}</a></li>')
            toc.append("</ul></li>")
        toc.append("</ul></li>")
        body.append("</section>")
        for category, recipes in cats.items():
            kid = f"{cid}-{slug(category)}"
            for r in recipes:
                body.append(recipe_html(r, f"{kid}-{slug(r['title'])}"))
    toc_html = "\n".join(toc) if toc else '<li class="empty">No recipes yet.</li>'
    template = (ROOT / "templates" / "book.html").read_text(encoding="utf-8")
    return (template.replace("{{TITLE}}", TITLE)
                    .replace("{{SUBTITLE}}", SUBTITLE)
                    .replace("{{CONTENTS}}", toc_html)
                    .replace("{{BODY}}", "\n".join(body)))


def main():
    book = load()
    update_readme(book)
    BOOK.write_text(build_html(book), encoding="utf-8")
    count = sum(len(rs) for cats in book.values() for rs in cats.values())
    print(f"Built {count} recipe(s) across {len(book)} cuisine(s).")


if __name__ == "__main__":
    main()
