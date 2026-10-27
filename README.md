# The Field Kitchen

*Recipes from our family table.* A family cookbook to be printed one day.

**Read the book:** https://bullangus.github.io/the-field-kitchen/ (GitHub Pages, built from `docs/` on `main`). To print it, follow "Print the book" (`docs/book.html`) and choose Print, then Save as PDF.

## Contents

<!-- CONTENTS:START -->
### Australian
- **Pork:** [Maple & Caramelised Orange Glazed Ham](recipes/Australian/Pork/maple-orange-glazed-ham.md)
- **Seafood:** [Barbecued Whole Snapper with Lime & Chilli](recipes/Australian/Seafood/barbecued-whole-snapper.md)

### British
- **Chicken:** [Classic Roast Chicken](recipes/British/Chicken/classic-roast-chicken.md)

### Chinese
- **Beef:** [Mongolian Beef](recipes/Chinese/Beef/mongolian-beef.md)
- **Chicken:** [Crispy Salt & Pepper Wings](recipes/Chinese/Chicken/salt-and-pepper-wings.md)
- **Noodles:** [Crispy Chilli Bacon Noodles](recipes/Chinese/Noodles/crispy-chilli-bacon-noodles.md)

### Indian
- **Breads:** [Simple Naan (No Yeast)](recipes/Indian/Breads/simple-naan.md)
- **Sides:** [Raita](recipes/Indian/Sides/raita.md)

### Italian
- **Breads:** [Focaccia](recipes/Italian/Breads/focaccia.md)
- **Pasta:** ['Nduja Pasta](recipes/Italian/Pasta/nduja-pasta.md), [Fettuccine Alfredo](recipes/Italian/Pasta/fettuccine-alfredo.md), [Lasagne](recipes/Italian/Pasta/lasagne.md), [Spaghetti alla Carbonara](recipes/Italian/Pasta/carbonara.md)
- **Pork:** [Crispy Porchetta](recipes/Italian/Pork/crispy-porchetta.md)

### Japanese
- **Chicken:** [Chicken Nanban (Fried Chicken with Tartar Sauce)](recipes/Japanese/Chicken/chicken-nanban.md), [Karaage (Japanese Fried Chicken)](recipes/Japanese/Chicken/karaage.md)
- **Eggs:** [Ramen Egg (Ajitsuke Tamago)](recipes/Japanese/Eggs/ramen-egg.md)

### Mexican
- **Beef:** [Carne Asada Tacos](recipes/Mexican/Beef/carne-asada-tacos.md)

### South African
- **Duck:** [Moh's Duck and Tamarind Curry](recipes/South African/Duck/mohs-duck-and-tamarind-curry.md)

### Spanish
- **Chicken:** [Chicken & White Bean Stew](recipes/Spanish/Chicken/chicken-and-white-bean-stew.md)

_20 recipes._
<!-- CONTENTS:END -->

## How it's organised

```
recipes/
  <Cuisine>/
    <Style of dish>/
      <recipe-name>.md
```

Each recipe is one Markdown file using [templates/recipe.md](templates/recipe.md). To add a photo, drop it in [photos/](photos/README.md) named after the recipe file (e.g. `photos/lasagne.jpg`). `python build.py` regenerates the contents above and the whole website in `docs/` (one page per cuisine and recipe, plus the printable `book.html`). Don't edit either of those by hand.
