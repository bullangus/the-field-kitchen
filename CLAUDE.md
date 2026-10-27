# The Field Kitchen: house rules

A family cookbook destined for print. The owner sends recipes (links, pasted text, photos) and cooking notes. These rules apply every time.

## Adding a recipe

1. Transcribe faithfully: every ingredient, quantity and step from the source, with nothing invented and nothing dropped. If anything is unreadable or missing (a quantity, an oven temperature, a time), **stop and ask** rather than guess.
2. File it at `recipes/<Cuisine>/<Style>/<kebab-name>.md`, following `templates/recipe.md`. Front matter `cuisine` and `category` must match the folder names exactly. Reuse an existing cuisine or style when one fits. Check `ls recipes/*/` first.
3. If you create a **new cuisine or style folder**, say so explicitly in the reply.
4. Run `python build.py`, then commit (and push if a remote exists).

## Format

- Sections in order: front matter (title, cuisine, category, serves, optional time and source), 1–2 line intro if useful, `## Ingredients`, `## Method` (numbered), optional `## Notes`.
- Ingredient subgroups use `### For the …`.
- Keep it plain: no emoji, no extra headings, no tips boxes. Source tips that matter go into the method or a note.

## Measurements

- Weights in g/kg first. Add cups/tbsp/tsp in brackets where that's easier to measure: `200 g (1 cup) caster sugar`, `15 ml (1 tbsp) olive oil`.
- If the source is in cups, keep the cup measure and add grams, using **ingredient-specific** densities (e.g. flour ≈ 125 g/cup, caster sugar ≈ 200 g/cup, butter 227 g/cup, rice ≈ 185 g/cup). Never use one density for everything.
- Spoons: 1 tbsp = 15 ml, 1 tsp = 5 ml. Use the source's cup: Australian/metric 250 ml (e.g. Marion's Kitchen), US 240 ml. Flour weights assume spooned-and-levelled cups.
- Oven: `180°C (160°C fan / 350°F / gas 4)`.
- Small amounts (pinches, 1 tsp spices) can stay in spoons only when grams would be fussy.
- Double-check every conversion.

## Cooking notes from the owner

Update the recipe itself (quantities, steps, timings). Unless told otherwise, also add a dated line under `## Notes` saying what changed and why, e.g. `- 2026-11-02: Cut the chilli to 1 tsp because 2 was too hot for the kids.`
