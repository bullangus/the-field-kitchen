# The Field Kitchen

*Recipes from our family table.* A family cookbook to be printed one day.

**Read the book:** `docs/index.html` (published with GitHub Pages). To print it, open it in a browser and choose Print, then Save as PDF.

## Contents

<!-- CONTENTS:START -->
_No recipes yet._
<!-- CONTENTS:END -->

## How it's organised

```
recipes/
  <Cuisine>/
    <Style of dish>/
      <recipe-name>.md
```

Each recipe is one Markdown file using [templates/recipe.md](templates/recipe.md). `python build.py` regenerates the contents above and the printable book in `docs/index.html`. Don't edit either of those by hand.
