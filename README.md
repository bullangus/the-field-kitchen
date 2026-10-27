# The Field Kitchen

*Recipes from our family table.* A family cookbook to be printed one day.

**Read the book:** https://bullangus.github.io/the-field-kitchen/ (GitHub Pages, built from `docs/` on `main`). To print it, follow "Print the book" (`docs/book.html`) and choose Print, then Save as PDF.

## Contents

<!-- CONTENTS:START -->
### Chinese
- **Beef:** [Mongolian Beef](recipes/Chinese/Beef/mongolian-beef.md)
- **Chicken:** [Crispy Salt & Pepper Wings](recipes/Chinese/Chicken/salt-and-pepper-wings.md)
- **Noodles:** [Crispy Chilli Bacon Noodles](recipes/Chinese/Noodles/crispy-chilli-bacon-noodles.md)

### Italian
- **Pasta:** [Fettuccine Alfredo](recipes/Italian/Pasta/fettuccine-alfredo.md)

### Japanese
- **Chicken:** [Chicken Nanban (Fried Chicken with Tartar Sauce)](recipes/Japanese/Chicken/chicken-nanban.md), [Karaage (Japanese Fried Chicken)](recipes/Japanese/Chicken/karaage.md)

### Spanish
- **Chicken:** [Chicken & White Bean Stew](recipes/Spanish/Chicken/chicken-and-white-bean-stew.md)

_7 recipes._
<!-- CONTENTS:END -->

## How it's organised

```
recipes/
  <Cuisine>/
    <Style of dish>/
      <recipe-name>.md
```

Each recipe is one Markdown file using [templates/recipe.md](templates/recipe.md). `python build.py` regenerates the contents above and the whole website in `docs/` (one page per cuisine and recipe, plus the printable `book.html`). Don't edit either of those by hand.
