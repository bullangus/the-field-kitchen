# Recipe photos

Drop a photo in this folder named exactly like the recipe's file, and the next `python build.py` puts it on the site and in the printed book.

| Recipe file | Photo |
|---|---|
| `recipes/Italian/Pasta/lasagne.md` | `photos/lasagne.jpg` |
| `recipes/South African/Duck/mohs-duck-and-tamarind-curry.md` | `photos/mohs-duck-and-tamarind-curry.jpg` |

- Formats: `.jpg`, `.jpeg`, `.png` or `.webp`. One photo per recipe.
- Landscape works best. Pages crop to 3:2 and the home page tile to 16:9, from the centre.
- Keep each under about 1 MB (roughly 2000 px wide) so the site stays quick on phones. The build warns about anything bigger.
- A photo whose name doesn't match a recipe is skipped with a warning, so check the spelling if one doesn't appear.

Where a photo shows up: at the top of the recipe's page, as a thumbnail on its cuisine card on the home page, in the "Why not cook…" tile when that recipe comes up, and above the recipe in the printed book.
