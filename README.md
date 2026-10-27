# The Field Kitchen

*Recipes from our family table.* A family cookbook to be printed one day.

**Read the book:** https://bullangus.github.io/the-field-kitchen/ (GitHub Pages, built from `docs/` on `main`). To print it, follow "Print the book" (`docs/book.html`) and choose Print, then Save as PDF.

## Contents

<!-- CONTENTS:START -->
### American
- **Chicken:** [Restaurant-Style Buffalo Chicken Wings](recipes/American/Chicken/buffalo-chicken-wings.md)

### Australian
- **Pork:** [Maple & Caramelised Orange Glazed Ham](recipes/Australian/Pork/maple-orange-glazed-ham.md)
- **Seafood:** [Barbecued Whole Snapper with Lime & Chilli](recipes/Australian/Seafood/barbecued-whole-snapper.md)

### British
- **Chicken:** [Classic Roast Chicken](recipes/British/Chicken/classic-roast-chicken.md)
- **Desserts:** [Classic Trifle](recipes/British/Desserts/classic-trifle.md)
- **Pork:** [Toad in the Hole](recipes/British/Pork/toad-in-the-hole.md)

### Chinese
- **Beef:** [Mongolian Beef](recipes/Chinese/Beef/mongolian-beef.md)
- **Chicken:** [Crispy Salt & Pepper Wings](recipes/Chinese/Chicken/salt-and-pepper-wings.md)
- **Noodles:** [Crispy Chilli Bacon Noodles](recipes/Chinese/Noodles/crispy-chilli-bacon-noodles.md)
- **Pork:** [Dumpling Lasagna](recipes/Chinese/Pork/dumpling-lasagna.md)

### Greek
- **Sides:** [Greek Yoghurt Sauce](recipes/Greek/Sides/greek-yoghurt-sauce.md)

### Indian
- **Breads:** [Simple Naan (No Yeast)](recipes/Indian/Breads/simple-naan.md)
- **Sides:** [Raita](recipes/Indian/Sides/raita.md)

### Italian
- **Breads:** [Focaccia](recipes/Italian/Breads/focaccia.md)
- **Pasta:** ['Nduja Pasta](recipes/Italian/Pasta/nduja-pasta.md), [Fettuccine Alfredo](recipes/Italian/Pasta/fettuccine-alfredo.md), [Lasagne](recipes/Italian/Pasta/lasagne.md), [Spaghetti alla Carbonara](recipes/Italian/Pasta/carbonara.md)
- **Pork:** [Crispy Porchetta](recipes/Italian/Pork/crispy-porchetta.md)

### Japanese
- **Chicken:** [Chicken Nanban (Fried Chicken with Tartar Sauce)](recipes/Japanese/Chicken/chicken-nanban.md), [Karaage (Japanese Fried Chicken)](recipes/Japanese/Chicken/karaage.md), [Nagoya-Style Fried Chicken Wings (Tebasaki)](recipes/Japanese/Chicken/nagoya-chicken-wings.md)
- **Eggs:** [Ramen Egg (Ajitsuke Tamago)](recipes/Japanese/Eggs/ramen-egg.md)

### Mexican
- **Beef:** [Carne Asada Tacos](recipes/Mexican/Beef/carne-asada-tacos.md), [Chilli Con Carne](recipes/Mexican/Beef/chilli-con-carne.md)

### South African
- **Duck:** [Moh's Duck and Tamarind Curry](recipes/South African/Duck/mohs-duck-and-tamarind-curry.md)
- **Sides:** [Chunky Onion and Tomato Relish](recipes/South African/Sides/chunky-onion-and-tomato-relish.md)

### Spanish
- **Chicken:** [Chicken & White Bean Stew](recipes/Spanish/Chicken/chicken-and-white-bean-stew.md)

_28 recipes._
<!-- CONTENTS:END -->

## How it's organised

```
recipes/
  <Cuisine>/
    <Style of dish>/
      <recipe-name>.md
```

Each recipe is one Markdown file using [templates/recipe.md](templates/recipe.md). To add a photo, drop it in [photos/](photos/README.md) named after the recipe file (e.g. `photos/lasagne.jpg`). `python build.py` regenerates the contents above and the whole website in `docs/` (one page per cuisine and recipe, plus the printable `book.html`). Don't edit either of those by hand.
