# The Field Kitchen

*Recipes from our family table.* A family cookbook to be printed one day.

**Read the book:** https://bullangus.github.io/the-field-kitchen/ (GitHub Pages, built from `docs/` on `main`). To print it, follow "Print the book" (`docs/book.html`) and choose Print, then Save as PDF.

## Contents

<!-- CONTENTS:START -->
### American
- **Baking:** [Chocolate Chip Cookies](recipes/American/Baking/chocolate-chip-cookies.md)
- **Chicken:** [Buffalo Wings](recipes/American/Chicken/buffalo-chicken-wings.md)
- **Salads:** [Caesar Salad](recipes/American/Salads/caesar-salad.md)

### Australian
- **Pork:** [Maple Orange Glazed Ham](recipes/Australian/Pork/maple-orange-glazed-ham.md)
- **Seafood:** [Barbecued Snapper](recipes/Australian/Seafood/barbecued-whole-snapper.md)

### British
- **Chicken:** [Roast Chicken](recipes/British/Chicken/classic-roast-chicken.md)
- **Desserts:** [Trifle](recipes/British/Desserts/classic-trifle.md)
- **Pork:** [Toad in the Hole](recipes/British/Pork/toad-in-the-hole.md)
- **Sides:** [Duck Fat Potatoes](recipes/British/Sides/duck-fat-potatoes.md)

### Chinese
- **Beef:** [Mongolian Beef](recipes/Chinese/Beef/mongolian-beef.md)
- **Chicken:** [Salt & Pepper Wings](recipes/Chinese/Chicken/salt-and-pepper-wings.md)
- **Noodles:** [Chilli Bacon Noodles](recipes/Chinese/Noodles/crispy-chilli-bacon-noodles.md)
- **Pork:** [Dumpling Lasagna](recipes/Chinese/Pork/dumpling-lasagna.md)

### Greek
- **Sides:** [Yoghurt Sauce](recipes/Greek/Sides/greek-yoghurt-sauce.md)

### Indian
- **Breads:** [Naan](recipes/Indian/Breads/simple-naan.md)
- **Sides:** [Raita](recipes/Indian/Sides/raita.md)

### Italian
- **Breads:** [Focaccia](recipes/Italian/Breads/focaccia.md)
- **Pasta:** ['Nduja Pasta](recipes/Italian/Pasta/nduja-pasta.md), [Carbonara](recipes/Italian/Pasta/carbonara.md), [Fettuccine Alfredo](recipes/Italian/Pasta/fettuccine-alfredo.md), [Lasagne](recipes/Italian/Pasta/lasagne.md)
- **Pork:** [Porchetta](recipes/Italian/Pork/crispy-porchetta.md)

### Japanese
- **Chicken:** [Chicken Nanban](recipes/Japanese/Chicken/chicken-nanban.md), [Karaage](recipes/Japanese/Chicken/karaage.md), [Katsu Curry](recipes/Japanese/Chicken/katsu-curry.md), [Tebasaki Wings](recipes/Japanese/Chicken/nagoya-chicken-wings.md)
- **Eggs:** [Ramen Eggs](recipes/Japanese/Eggs/ramen-egg.md)
- **Pork:** [Tonkatsu](recipes/Japanese/Pork/tonkatsu.md)

### Mexican
- **Beef:** [Carne Asada Tacos](recipes/Mexican/Beef/carne-asada-tacos.md), [Chilli Con Carne](recipes/Mexican/Beef/chilli-con-carne.md)

### South African
- **Duck:** [Moh's Duck Curry](recipes/South African/Duck/mohs-duck-and-tamarind-curry.md)
- **Sides:** [Onion & Tomato Relish](recipes/South African/Sides/chunky-onion-and-tomato-relish.md)

### Spanish
- **Chicken:** [Chicken & White Bean Stew](recipes/Spanish/Chicken/chicken-and-white-bean-stew.md)

### Thai
- **Beef:** [Thai Beef Salad](recipes/Thai/Beef/thai-beef-salad.md)
- **Chicken:** [Satay Chicken](recipes/Thai/Chicken/satay-chicken.md), [Yellow Curry](recipes/Thai/Chicken/yellow-curry.md)

_36 recipes._
<!-- CONTENTS:END -->

## How it's organised

```
recipes/
  <Cuisine>/
    <Style of dish>/
      <recipe-name>.md
```

Each recipe is one Markdown file using [templates/recipe.md](templates/recipe.md). To add a photo, drop it in [photos/](photos/README.md) named after the recipe file (e.g. `photos/lasagne.jpg`). `python build.py` regenerates the contents above and the whole website in `docs/` (one page per cuisine and recipe, plus the printable `book.html`). Don't edit either of those by hand.
