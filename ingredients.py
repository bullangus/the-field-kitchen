"""Understand ingredient lines for the shopping list, "What can I cook?" and
ingredient highlighting: the amount and unit at the start of a line, and which
core ingredient it is.

Each INGREDIENTS entry is (pattern, name, aisle, staple). The first pattern that
matches a line wins, so specific entries ("spring onion", "lemongrass") come
before general ones ("onion", "lemon"). The pattern is also used in the browser
to find the ingredient in method steps, so keep it to plain words, | and \\b.
Staples (salt, pepper, oil, sugar, water) are assumed to be in the pantry.
Add an entry when a new recipe brings an ingredient the table doesn't know;
unknown lines still work, they just shop under "Other" by their own name.
"""

import re

PRODUCE, HERBS, MEAT, DAIRY, GRAINS, PANTRY, SPICES, OILS, DRINKS, OTHER = (
    "Fruit & veg", "Herbs", "Meat & seafood", "Dairy & eggs", "Bread, pasta & rice",
    "Pantry & sauces", "Herbs & spices", "Oils & vinegars", "Wine & spirits", "Other")
# Shopping list order, roughly how a supermarket is walked.
AISLES = (PRODUCE, HERBS, MEAT, DAIRY, GRAINS, PANTRY, SPICES, OILS, DRINKS, OTHER)

INGREDIENTS = [
    # Skip: pointers rather than things to buy.
    (r"\bone topping\b|\bsee topping", None, None, True),
    (r"\bwater\b", "Water", PANTRY, True),
    # Stocks, sauces and pastes named after other ingredients go first.
    (r"\bchicken stock\b", "Chicken stock", PANTRY, False),
    (r"\bfish sauce\b", "Fish sauce", PANTRY, False),
    (r"\bsweet chilli sauce\b", "Sweet chilli sauce", PANTRY, False),
    (r"\bchilli crisp\b", "Chilli crisp", PANTRY, False),
    (r"\bsriracha\b|\bhot sauce\b", "Hot sauce", PANTRY, False),
    (r"\bdark soy\b", "Dark soy sauce", PANTRY, False),
    (r"\bsoy sauce\b", "Soy sauce", PANTRY, False),
    (r"\boyster sauce\b", "Oyster sauce", PANTRY, False),
    (r"\btomato sauce\b|\bketchup\b", "Tomato sauce", PANTRY, False),
    (r"\bpassata\b", "Tomato passata", PANTRY, False),
    (r"\bcherry tomatoes\b", "Cherry tomatoes", PRODUCE, False),
    (r"\btomato paste\b", "Tomato paste", PANTRY, False),
    (r"\btomato(es)?\b", "Tinned tomatoes", PANTRY, False),
    (r"\bkidney beans\b", "Red kidney beans", PANTRY, False),
    (r"\bcannellini\b", "Cannellini beans", PANTRY, False),
    (r"\bstock cubes?\b|\bbouillon\b", "Beef stock cubes", PANTRY, False),
    (r"\bstrawberry jelly\b", "Aeroplane strawberry jelly", PANTRY, False),
    (r"\borange jelly\b", "Aeroplane orange jelly", PANTRY, False),
    (r"\bblancmange\b", "Strawberry blancmange", PANTRY, False),
    (r"\bcustard\b", "Bird's custard powder", PANTRY, False),
    (r"\bmandarin", "Tinned mandarins", PANTRY, False),
    (r"\bflake\b", "Flake chocolate", PANTRY, False),
    (r"\bchocolate\b", "Dark chocolate", PANTRY, False),
    (r"\bvanilla\b", "Vanilla extract", PANTRY, False),
    (r"\bjam rolls?\b", "Jam rolls", GRAINS, False),
    (r"\bsausages?\b", "Pork sausages", MEAT, False),
    (r"\bdripping\b", "Beef dripping", OILS, False),
    (r"\bduck fat\b|\bgoose fat\b", "Duck fat", OILS, False),
    (r"\bcointreau\b", "Cointreau", DRINKS, False),
    (r"\bcoconut milk\b|\bcoconut cream\b", "Coconut milk", PANTRY, False),
    (r"\bcurry paste\b", "Yellow curry paste", PANTRY, False),
    (r"\bcurry powder\b", "Curry powder", SPICES, False),
    (r"\bpeanuts\b", "Roasted peanuts", PANTRY, False),
    (r"\btamarind\b", "Tamarind paste", PANTRY, False),
    (r"\bworcestershire\b", "Worcestershire sauce", PANTRY, False),
    (r"\bchutney\b", "Mrs Ball's chutney", PANTRY, False),
    (r"\bmaple syrup\b", "Maple syrup", PANTRY, False),
    (r"\bmustard seeds\b", "Black mustard seeds", SPICES, False),
    (r"\bdijon\b|\bmustard\b", "Dijon mustard", PANTRY, False),
    (r"\bkewpie\b", "Kewpie mayonnaise", DAIRY, False),
    (r"\bmayonnaise\b", "Mayonnaise", DAIRY, False),
    (r"\bdashi\b", "Dashi powder", PANTRY, False),
    (r"\bmsg\b", "MSG", PANTRY, False),
    (r"\bbicarbonate\b|\bbaking soda\b", "Bicarbonate of soda", PANTRY, False),
    (r"\bdesiccated coconut\b", "Desiccated coconut", PANTRY, False),
    (r"\bcashew", "Cashew nuts", PANTRY, False),
    (r"\byeast\b", "Dried yeast", PANTRY, False),
    # Oils and vinegars (before avocado, sesame and peanut).
    (r"\bolive oil\b", "Olive oil", OILS, True),
    (r"\bsesame oil\b", "Sesame oil", OILS, False),
    (r"\bpeanut oil\b", "Peanut oil", OILS, True),
    (r"\bsunflower oil\b", "Sunflower oil", OILS, True),
    (r"\boil\b", "Neutral oil", OILS, True),
    (r"\bbalsamic\b", "Balsamic vinegar", OILS, False),
    (r"\brice vinegar\b", "Rice vinegar", OILS, False),
    (r"\bvinegar\b", "White wine vinegar", OILS, False),
    # Wine and spirits (before orange and rice).
    (r"\bgrand marnier\b|\borange liqueur\b", "Grand Marnier", DRINKS, False),
    (r"\bsake\b", "Cooking sake", DRINKS, False),
    (r"\bshaoxing\b|\brice wine\b", "Shaoxing wine", DRINKS, False),
    (r"\bmirin\b", "Mirin", DRINKS, False),
    (r"\bred wine\b", "Red wine", DRINKS, False),
    # Meat and seafood.
    (r"\bsnapper\b|\bwhole fish\b", "Whole snapper", MEAT, False),
    (r"\bchicken wings\b", "Chicken wings", MEAT, False),
    (r"\bchicken thighs?\b", "Chicken thighs", MEAT, False),
    (r"\bwhole chicken\b", "Whole chicken", MEAT, False),
    (r"\bduck\b", "Duck breasts", MEAT, False),
    (r"\bleg ham\b|\bham\b", "Leg ham", MEAT, False),
    (r"\bguanciale\b", "Guanciale", MEAT, False),
    (r"\bbacon\b", "Streaky bacon", MEAT, False),
    (r"\bnduja\b", "'Nduja", MEAT, False),
    (r"\bpork mince\b", "Pork mince", MEAT, False),
    (r"\bbeef mince\b", "Beef mince", MEAT, False),
    (r"\bpork belly\b", "Pork belly with loin", MEAT, False),
    (r"\bflank\b|\bskirt\b|\bsteak\b", "Beef steak", MEAT, False),
    # Bread, pasta and rice (egg noodles before eggs, flours before plain flour).
    (r"\bwonton\b|\bdumpling wrappers\b", "Wonton or dumpling wrappers", GRAINS, False),
    (r"\bcorn chips\b", "Corn chips", GRAINS, False),
    (r"\begg noodles\b|\blo mein\b", "Egg noodles", GRAINS, False),
    (r"\bvermicelli\b", "Rice vermicelli", GRAINS, False),
    (r"\blasagne sheets\b", "Fresh lasagne sheets", GRAINS, False),
    (r"\bfettuccine\b", "Dried fettuccine", GRAINS, False),
    (r"\bfileja\b", "Fileja pasta", GRAINS, False),
    (r"\bspaghetti\b|\brigatoni\b", "Spaghetti or rigatoni", GRAINS, False),
    (r"\btortillas\b", "Corn tortillas", GRAINS, False),
    (r"\brice\b", "Rice", GRAINS, False),
    (r"\bself-raising\b", "Self-raising flour", GRAINS, False),
    (r"\bbread flour\b", "Bread flour", GRAINS, False),
    (r"\btipo 00\b", "Tipo 00 flour", GRAINS, False),
    (r"\bgram\b|\bchickpea\b", "Gram (chickpea) flour", GRAINS, False),
    (r"\bcornflour\b|\bcornstarch\b|\bpotato starch\b", "Cornflour", GRAINS, False),
    (r"\bflour\b", "Plain flour", GRAINS, False),
    # Dairy and eggs.
    (r"\beggs?\b", "Eggs", DAIRY, False),
    (r"\bbutter\b", "Butter", DAIRY, False),
    # Before cream: "Dutch cream" is a potato.
    (r"\bpotato(es)?\b", "Potatoes", PRODUCE, False),
    (r"\bsour cream\b", "Sour cream", DAIRY, False),
    (r"\bcream\b", "Thickened cream", DAIRY, False),
    (r"\byoghurt\b", "Greek yoghurt", DAIRY, False),
    (r"\bmilk\b", "Milk", DAIRY, False),
    (r"\bmozzarella\b", "Mozzarella", DAIRY, False),
    (r"\bpecorino\b", "Pecorino", DAIRY, False),
    (r"\bparmesan\b|\bparmigiano\b", "Parmesan", DAIRY, False),
    (r"\bpaneer\b", "Paneer", DAIRY, False),
    (r"\bcheese\b", "Grated cheese", DAIRY, False),
    # Spices (seeds and ground before the fresh herb; garlic powder before garlic).
    (r"\bcoriander seeds\b", "Coriander seeds", SPICES, False),
    (r"\bground coriander\b", "Ground coriander", SPICES, False),
    (r"\bcumin\b", "Cumin", SPICES, False),
    (r"\bsichuan pepper", "Sichuan peppercorns", SPICES, False),
    (r"\bgarlic powder\b", "Garlic powder", SPICES, False),
    (r"\bonion powder\b", "Onion powder", SPICES, False),
    (r"\boregano\b", "Dried oregano", SPICES, False),
    (r"\bpaprika\b", "Paprika", SPICES, False),
    (r"\bgaram masala\b", "Garam masala", SPICES, False),
    (r"\bturmeric\b", "Turmeric", SPICES, False),
    (r"\bgochugaru\b", "Gochugaru", SPICES, False),
    (r"\bchilli flakes\b", "Chilli flakes", SPICES, False),
    (r"\bchilli powder\b", "Chilli powder", SPICES, False),
    (r"\bcayenne\b", "Cayenne pepper", SPICES, False),
    (r"\bshichimi\b", "Shichimi togarashi", SPICES, False),
    (r"\ballspice\b", "Ground allspice", SPICES, False),
    (r"\bnutmeg\b", "Nutmeg", SPICES, False),
    (r"\bfennel\b", "Fennel pollen or seeds", SPICES, False),
    (r"\bsesame seeds\b", "Sesame seeds", SPICES, False),
    (r"\bsalt\b", "Salt", SPICES, True),
    (r"\bpepper(corns)?\b", "Pepper", SPICES, True),
    # Fruit and veg (specific before general).
    (r"\bspring onions?\b|\bgreen onions?\b|\bscallions?\b", "Spring onions", PRODUCE, False),
    (r"\beschallot\b|\bshallot\b", "Eschallot", PRODUCE, False),
    (r"\bred onion\b", "Red onion", PRODUCE, False),
    (r"\bwhite onion\b", "White onion", PRODUCE, False),
    (r"\bonions?\b", "Brown onions", PRODUCE, False),
    (r"\bgarlic\b", "Garlic", PRODUCE, False),
    (r"\bwhole cloves\b|\bcloves, whole\b", "Whole cloves", SPICES, False),
    (r"\bginger\b", "Fresh ginger", PRODUCE, False),
    (r"\blemongrass\b", "Lemongrass", PRODUCE, False),
    (r"\bmakrut\b|\blime leaves\b", "Makrut lime leaves", PRODUCE, False),
    (r"\blimes?\b", "Limes", PRODUCE, False),
    (r"\blemons?\b", "Lemons", PRODUCE, False),
    (r"\boranges?\b", "Oranges", PRODUCE, False),
    (r"\bavocados?\b", "Avocados", PRODUCE, False),
    (r"\bstrawberries\b", "Strawberries", PRODUCE, False),
    (r"\bchillies\b|\bchilli\b", "Fresh red chillies", PRODUCE, False),
    (r"\bjalape", "Jalapeño", PRODUCE, False),
    (r"\bcarrots?\b", "Carrots", PRODUCE, False),
    (r"\bcelery\b", "Celery", PRODUCE, False),
    (r"\bcucumber\b", "Cucumber", PRODUCE, False),
    (r"\basparagus\b", "Asparagus", PRODUCE, False),
    (r"\bspinach\b", "Baby spinach", PRODUCE, False),
    (r"\blettuce\b|\bcabbage\b|\bsalad greens\b", "Lettuce and cabbage", PRODUCE, False),
    (r"\bcurry leaves\b", "Curry leaves", HERBS, False),
    (r"\bcoriander\b", "Coriander", HERBS, False),
    (r"\bmint\b", "Mint", HERBS, False),
    (r"\bparsley\b", "Parsley", HERBS, False),
    (r"\bbasil\b", "Basil", HERBS, False),
    (r"\brosemary\b", "Rosemary", HERBS, False),
    (r"\bthyme\b", "Thyme", HERBS, False),
    (r"\bsugar\b", "Sugar", PANTRY, True),
]
COMPILED = [(re.compile(p, re.I), p, name, aisle, staple) for p, name, aisle, staple in INGREDIENTS]

FRACTIONS = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3, "⅛": 0.125}
NUMBER = r"(?:\d+(?:\.\d+)?[½¼¾⅓⅔⅛]?|[½¼¾⅓⅔⅛])"
MEASURES = {"kg": ("g", 1000), "g": ("g", 1), "l": ("ml", 1000), "ml": ("ml", 1),
            "tbsp": ("tsp", 3), "tsp": ("tsp", 1)}
COUNTS = ("cloves", "clove", "cm", "head", "bunch", "sticks", "stick", "sprigs", "sprig", "stalks",
          "rashers", "pieces", "piece", "sachet", "pack")
LEADING = re.compile(rf"^({NUMBER})(?:\s*[–-]\s*({NUMBER}))?\s*(kg|g|ml|l|tbsp|tsp|{'|'.join(COUNTS)})?\b", re.I)


# Words too generic to link an ingredient to a method step on their own.
GENERIC_LAST = {"sauce", "oil", "seeds", "powder", "flakes", "leaves", "juice", "stock", "onion", "onions?",
                "flour", "paste", "wine", "crisp", "thighs?", "wings", "mince", "cream", "sheets", "noodles",
                "pepper", "syrup", "tomatoes", "ham", "steak", "fish", "chilli"}
GENERIC_FIRST = {"sweet", "dark", "light", "fresh", "whole", "red", "white", "ground", "black", "spring", "green",
                 "olive", "sesame", "peanut", "sunflower", "fish", "rice", "egg", "leg", "orange", "lime", "tomato",
                 "cherry", "baby", "bread", "self-raising", "tipo", "corn", "desiccated", "maple", "oyster", "chicken"}


def highlight_pattern(pattern):
    """The table pattern plus the telling word of each phrase ("desiccated coconut" ->
    coconut, "chicken thighs" -> chicken), so method steps that say it shorter still link."""
    alternatives = pattern.split("|")
    extra = []
    for alt in alternatives:
        words = alt.replace(r"\b", "").split()
        if len(words) < 2:
            continue
        if words[-1] not in GENERIC_LAST:
            extra.append(rf"\b{words[-1]}\b")
        elif words[0] not in GENERIC_FIRST:
            extra.append(rf"\b{words[0]}\b")
        elif words[0] == "chicken":
            extra.append(r"\bchicken\b")
    return "|".join(alternatives + [e for e in extra if e not in alternatives])


def number(text):
    """'1½' -> 1.5, '½' -> 0.5, '2.5' -> 2.5."""
    frac = FRACTIONS.get(text[-1], 0)
    whole = text[:-1] if frac else text
    return (float(whole) if whole else 0) + frac


def parse_line(line):
    """Amount, unit, core ingredient and aisle for one ingredient line.

    Returns a dict: t (the line), n (shopping name or None to skip), a (aisle),
    s (staple), p (pattern to find it in method text), q (amount, upper end of a
    range, or None), u (unit: g, ml, tsp, a count word like 'cloves', or None).
    """
    item = {"t": line, "n": None, "a": OTHER, "s": False, "p": "", "q": None, "u": None}
    for rx, pattern, name, aisle, staple in COMPILED:
        if rx.search(line):
            item.update(n=name, a=aisle, s=staple, p=highlight_pattern(pattern) if name else "")
            break
    else:
        # Unknown ingredient: shop for it by its own words, minus amounts and prep notes.
        bare = re.sub(rf"^{NUMBER}(\s*[–-]\s*{NUMBER})?\s*(\w+\b)?\s*(\([^)]*\))?\s*", "", line)
        item["n"] = re.split(r",|\(| or ", bare)[0].strip().capitalize() or line
    if item["n"] is None:
        return item
    m = LEADING.match(line)
    if m:
        amount = number(m.group(2) or m.group(1))
        unit = (m.group(3) or "").lower()
        if unit in MEASURES:
            base, factor = MEASURES[unit]
            item["q"], item["u"] = amount * factor, base
        else:
            item["q"], item["u"] = amount, unit or None
    return item
