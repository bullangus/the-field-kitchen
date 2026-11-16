"""Understand ingredient lines for the shopping list, "What can I cook?" and
ingredient highlighting: the amount and unit at the start of a line, and which
core ingredient it is.

Each INGREDIENTS entry is (pattern, name, aisle, staple). The first pattern that
matches a line wins, so specific entries ("spring onion", "lemongrass") come
before general ones ("onion", "lemon"). The pattern is also used in the browser
to find the ingredient in method steps, so keep it to plain words, | and \\b.
Staples (salt, pepper, oil, sugar, water, MSG) are assumed to be in the pantry.
Add an entry when a new recipe brings an ingredient the table doesn't know;
unknown lines still work, they just shop under "Other" by their own name.
"""

import re

# Sections in the order you'd walk a Coles or Woolworths: fresh food round the edge first,
# then the aisles, then the fridges and freezers at the end, and the bottle shop last.
(PRODUCE, BAKERY, DELI, MEAT, PASTA, WORLD, SPICES, BAKING, SAUCES, TINS, OILS, SNACKS,
 DAIRY, FROZEN, LIQUOR, OTHER) = (
    "Fruit & veg", "Bakery", "Deli", "Meat & seafood", "Pasta, rice & noodles", "International foods",
    "Herbs & spices", "Baking & eggs", "Sauces, spreads & stock", "Tins & jars", "Oils & vinegars",
    "Snacks & sweets", "Dairy & fridge", "Freezer", "Bottle shop", "Other")
AISLES = (PRODUCE, BAKERY, DELI, MEAT, PASTA, WORLD, SPICES, BAKING, SAUCES, TINS, OILS, SNACKS,
          DAIRY, FROZEN, LIQUOR, OTHER)

INGREDIENTS = [
    # Skip: pointers rather than things to buy.
    (r"\bone topping\b|\bsee topping|\bpan juices\b", None, None, True),
    (r"\bwater\b", "Water", SAUCES, True),
    # Stocks, sauces and pastes named after other ingredients go first.
    (r"\bchicken bouillon\b|\bchicken stock powder\b", "Chicken stock powder", SAUCES, False),
    (r"\bchicken stock\b", "Chicken stock", SAUCES, False),
    (r"\bfish sauce\b", "Fish sauce", WORLD, False),
    (r"\bsweet chilli sauce\b", "Sweet chilli sauce", SAUCES, False),
    (r"\bchilli crisp\b", "Chilli crisp", WORLD, False),
    (r"\bsriracha\b|\bhot sauce\b", "Hot sauce", SAUCES, False),
    (r"\bdark soy\b", "Dark soy sauce", WORLD, False),
    (r"\bsoy sauce\b", "Soy sauce", WORLD, False),
    (r"\boyster sauce\b", "Oyster sauce", WORLD, False),
    # Australian tomato sauce and ketchup are different products, so they shop separately.
    (r"\bketchup\b", "Ketchup", SAUCES, False),
    (r"\btomato sauce\b", "Tomato sauce", SAUCES, False),
    (r"\bpassata\b", "Tomato passata", TINS, False),
    (r"\bsun-dried tomato(es)?\b|\bsun dried tomato(es)?\b", "Sun-dried tomatoes", TINS, False),
    (r"\bcherry tomatoes\b", "Cherry tomatoes", PRODUCE, False),
    (r"\btomato paste\b", "Tomato paste", TINS, False),
    (r"\bchickpeas\b", "Tinned chickpeas", TINS, False),
    # Fresh, unlike the tinned tomatoes below.
    (r"\bmedium tomato(es)?\b", "Tomatoes", PRODUCE, False),
    (r"\btomato(es)?\b", "Tinned tomatoes", TINS, False),
    (r"\bkidney beans\b", "Red kidney beans", TINS, False),
    (r"\bcannellini\b", "Cannellini beans", TINS, False),
    (r"\bstock cubes?\b|\bbouillon\b", "Beef stock cubes", SAUCES, False),
    (r"\bstrawberry jelly\b", "Aeroplane strawberry jelly", BAKING, False),
    (r"\borange jelly\b", "Aeroplane orange jelly", BAKING, False),
    (r"\bblancmange\b", "Strawberry blancmange", BAKING, False),
    (r"\bgravox\b|\bgravy mix\b", "Gravox Traditional Gravy Mix", SAUCES, False),
    (r"\bcustard\b", "Bird's custard powder", BAKING, False),
    (r"\bmandarin", "Tinned mandarins", TINS, False),
    (r"\bflake\b", "Flake chocolate", SNACKS, False),
    (r"\bchocolate\b", "Dark chocolate", BAKING, False),
    (r"\bvanilla\b", "Vanilla extract", BAKING, False),
    (r"\bjam rolls?\b", "Jam rolls", BAKERY, False),
    (r"\bsausages?\b", "Pork sausages", MEAT, False),
    (r"\bdripping\b", "Beef dripping", MEAT, False),
    (r"\bduck fat\b|\bgoose fat\b", "Duck fat", MEAT, False),
    (r"\bcointreau\b", "Cointreau", LIQUOR, False),
    (r"\bgolden curry\b|\bcurry blocks?\b", "Golden Curry blocks", WORLD, False),
    (r"\bsushi seasoning\b", "Sushi seasoning", WORLD, False),
    (r"\bnori\b", "Nori sheets", WORLD, False),
    (r"\btonkatsu sauce\b", "Tonkatsu sauce", WORLD, False),
    (r"\bpickled ginger\b", "Pickled ginger", WORLD, False),
    (r"\bkarashi\b|\benglish mustard\b|\bjapanese mustard\b", "Japanese or English mustard", WORLD, False),
    (r"\bpanko\b", "Panko breadcrumbs", WORLD, False),
    (r"\bcaesar dressing\b", "Caesar dressing", SAUCES, False),
    (r"\bthousand island\b", "Thousand island dressing", SAUCES, False),
    (r"\bitalian seasoning\b", "Italian seasoning", SPICES, False),
    (r"\bevaporated milk\b", "Evaporated milk", TINS, False),
    (r"\bmilk powder\b", "Skim milk powder", BAKING, False),
    (r"\bcoconut milk\b|\bcoconut cream\b", "Coconut milk", WORLD, False),
    (r"\bred curry paste\b", "Red curry paste", WORLD, False),
    (r"\bcurry paste\b", "Yellow curry paste", WORLD, False),
    (r"\bcurry powder\b", "Curry powder", SPICES, False),
    (r"\bpeanut butter\b", "Peanut butter", SAUCES, False),
    (r"\bpeanuts\b", "Roasted peanuts", SNACKS, False),
    (r"\btamarind\b", "Tamarind paste", WORLD, False),
    (r"\bworcestershire\b", "Worcestershire sauce", SAUCES, False),
    (r"\bchutney\b", "Mrs Ball's chutney", WORLD, False),
    (r"\bhoney\b", "Honey", SAUCES, False),
    (r"\byuzu\b", "Yuzu juice", WORLD, False),
    (r"\bmaple syrup\b", "Maple syrup", SAUCES, False),
    (r"\bmustard seeds\b", "Black mustard seeds", SPICES, False),
    (r"\bdijon\b|\bmustard\b", "Dijon mustard", SAUCES, False),
    (r"\bkewpie\b", "Kewpie mayonnaise", WORLD, False),
    (r"\bmayonnaise\b", "Mayonnaise", SAUCES, False),
    (r"\bdashi\b", "Dashi powder", WORLD, False),
    (r"\bmsg\b", "MSG", WORLD, True),
    (r"\bbicarb(onate)?\b|\bbaking soda\b", "Bicarb soda", BAKING, False),
    (r"\bdesiccated coconut\b", "Desiccated coconut", BAKING, False),
    (r"\bcashew", "Cashew nuts", BAKING, False),
    (r"\byeast\b", "Dried yeast", BAKING, False),
    # Oils and vinegars (before avocado, sesame and peanut).
    (r"\bolive oil\b", "Olive oil", OILS, True),
    (r"\bsesame oil\b", "Sesame oil", WORLD, False),
    (r"\bpeanut oil\b", "Peanut oil", OILS, True),
    (r"\bsunflower oil\b", "Sunflower oil", OILS, True),
    (r"\boil\b", "Neutral oil", OILS, True),
    (r"\bbalsamic\b", "Balsamic vinegar", OILS, False),
    (r"\brice vinegar\b", "Rice vinegar", WORLD, False),
    (r"\bblack vinegar\b|\bblack chinese vinegar\b", "Chinese black vinegar", WORLD, False),
    (r"\bvinegar\b", "White wine vinegar", OILS, False),
    # Wine and spirits (before orange and rice).
    (r"\bgrand marnier\b|\borange liqueur\b", "Grand Marnier", LIQUOR, False),
    (r"\bsake\b", "Cooking sake", WORLD, False),
    (r"\bshaoxing\b|\brice wine\b", "Shaoxing wine", WORLD, False),
    (r"\bmirin\b", "Mirin", WORLD, False),
    (r"\bred wine\b", "Red wine", LIQUOR, False),
    # Meat and seafood.
    (r"\bsnapper\b|\bwhole fish\b", "Whole snapper", MEAT, False),
    (r"\bsalmon\b", "Salmon fillets", MEAT, False),
    # Before chicken: tonkatsu is "pork loin steaks, or chicken".
    (r"\bpork loin\b", "Pork loin steaks", MEAT, False),
    (r"\bchicken wings\b", "Chicken wings", MEAT, False),
    (r"\bchicken thighs?\b", "Chicken thighs", MEAT, False),
    (r"\bchicken breasts?\b", "Chicken breasts", MEAT, False),
    (r"\bwhole chicken\b", "Whole chicken", MEAT, False),
    (r"\bduck\b", "Duck breasts", MEAT, False),
    (r"\bleg ham\b|\bham\b", "Leg ham", DELI, False),
    (r"\bguanciale\b", "Guanciale", DELI, False),
    (r"\bbacon\b", "Streaky bacon", DELI, False),
    (r"\bkabana\b", "Kabana", DELI, False),
    (r"\bnduja\b", "'Nduja", DELI, False),
    (r"\bpork mince\b", "Pork mince", MEAT, False),
    (r"\bbeef mince\b", "Beef mince", MEAT, False),
    (r"\bpork belly\b", "Pork belly with loin", MEAT, False),
    (r"\bflank\b|\bskirt\b|\bsteak\b", "Beef steak", MEAT, False),
    # Bread, pasta and rice (egg noodles before eggs, flours before plain flour).
    (r"\bwonton\b|\bdumpling wrappers\b", "Wonton or dumpling wrappers", DAIRY, False),
    (r"\bcorn chips\b", "Corn chips", SNACKS, False),
    (r"\begg noodles\b|\blo mein\b", "Egg noodles", PASTA, False),
    (r"\bvermicelli\b", "Rice vermicelli", PASTA, False),
    (r"\blasagne sheets\b", "Fresh lasagne sheets", DAIRY, False),
    (r"\bfettuccine\b", "Dried fettuccine", PASTA, False),
    (r"\brisoni\b|\borzo\b", "Risoni", PASTA, False),
    (r"\bfileja\b", "Fileja pasta", PASTA, False),
    (r"\bfusilli\b|\bspiral pasta\b", "Spiral pasta (fusilli)", PASTA, False),
    (r"\bspaghetti\b|\brigatoni\b", "Spaghetti or rigatoni", PASTA, False),
    (r"\btortillas\b", "Corn tortillas", WORLD, False),
    (r"\bsushi rice\b", "Sushi rice", WORLD, False),
    (r"\brice\b", "Rice", PASTA, False),
    (r"\bself-raising\b", "Self-raising flour", BAKING, False),
    (r"\bshokupan\b", "Shokupan (Japanese milk bread)", BAKERY, False),
    (r"\bcavatappi\b", "Cavatappi pasta", PASTA, False),
    (r"\bshin ramyun\b", "Shin Ramyun noodles", WORLD, False),
    (r"\binstant ramen\b|\bramen noodles\b", "Instant ramen noodles", PASTA, False),
    (r"\bbread flour\b", "Bread flour", BAKING, False),
    (r"\btipo 00\b", "Tipo 00 flour", BAKING, False),
    (r"\bgram\b|\bchickpea\b", "Gram (chickpea) flour", WORLD, False),
    (r"\bcornflour\b|\bcornstarch\b|\bpotato starch\b", "Cornflour", BAKING, False),
    (r"\bflour\b", "Plain flour", BAKING, False),
    (r"\bcob loa(f|ves)\b|\bcobs?\b", "Small cob loaves", BAKERY, False),
    (r"\bbread\b", "Bread", BAKERY, False),
    # Dairy and eggs.
    (r"\beggs?\b", "Eggs", BAKING, False),
    (r"\bbutter\b", "Butter", DAIRY, False),
    # Before cream: "Dutch cream" is a potato.
    (r"\bpotato(es)?\b", "Potatoes", PRODUCE, False),
    (r"\bsour cream\b", "Sour cream", DAIRY, False),
    (r"\bcream\b", "Thickened cream", DAIRY, False),
    (r"\byoghurt\b", "Greek yoghurt", DAIRY, False),
    (r"\bmilk\b", "Milk", DAIRY, False),
    (r"\bmozzarella\b", "Mozzarella", DAIRY, False),
    (r"\bcolby\b", "Colby cheese", DAIRY, False),
    (r"\bcheddar\b", "Cheddar", DAIRY, False),
    (r"\bpecorino\b", "Pecorino", DELI, False),
    (r"\bparmesan\b|\bparmigiano\b", "Parmesan", DELI, False),
    (r"\bpaneer\b", "Paneer", DAIRY, False),
    (r"\bcheese\b", "Grated cheese", DAIRY, False),
    # Spices (seeds and ground before the fresh herb; garlic powder before garlic).
    (r"\bcoriander seeds\b", "Coriander seeds", SPICES, False),
    (r"\bground coriander\b", "Ground coriander", SPICES, False),
    (r"\bcumin\b", "Cumin", SPICES, False),
    (r"\bdried sichuan red chillies\b|\bdried chillies\b", "Dried red chillies", WORLD, False),
    (r"\bsichuan pepper|\bsichuan red pepper", "Sichuan peppercorns", WORLD, False),
    (r"\bgarlic powder\b", "Garlic powder", SPICES, False),
    (r"\bonion powder\b", "Onion powder", SPICES, False),
    (r"\boregano\b", "Dried oregano", SPICES, False),
    (r"\bsmoked paprika\b", "Smoked paprika", SPICES, False),
    (r"\bpaprika\b", "Paprika", SPICES, False),
    (r"\bgaram masala\b", "Garam masala", SPICES, False),
    (r"\bturmeric\b", "Turmeric", SPICES, False),
    (r"\bgochugaru\b", "Gochugaru", WORLD, False),
    (r"\bchilli flakes\b", "Chilli flakes", SPICES, False),
    (r"\bchilli powder\b", "Chilli powder", SPICES, False),
    (r"\bcayenne\b", "Cayenne pepper", SPICES, False),
    (r"\bshichimi\b", "Shichimi togarashi", WORLD, False),
    (r"\bcinnamon\b", "Cinnamon sticks", SPICES, False),
    (r"\bcardamom\b", "Green cardamom pods", SPICES, False),
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
    (r"\bpeas and corn\b", "Frozen peas and corn", FROZEN, False),
    (r"\bfrozen peas\b", "Frozen peas", FROZEN, False),
    (r"\bspinach\b", "Baby spinach", PRODUCE, False),
    (r"\bcos\b", "Cos lettuce", PRODUCE, False),
    (r"\bdrum cabbage\b", "Drum cabbage", PRODUCE, False),
    (r"\bmushrooms?\b", "Mushrooms", PRODUCE, False),
    (r"\bcoleslaw\b", "Coleslaw", DELI, False),
    (r"\bcorn kernels\b", "Corn kernels", FROZEN, False),
    (r"\blettuce\b|\bcabbage\b|\bsalad greens\b", "Lettuce and cabbage", PRODUCE, False),
    (r"\bcurry leaves\b", "Curry leaves", PRODUCE, False),
    (r"\bcoriander\b", "Coriander", PRODUCE, False),
    (r"\bmint\b", "Mint", PRODUCE, False),
    (r"\bparsley\b", "Parsley", PRODUCE, False),
    (r"\bbasil\b", "Basil", PRODUCE, False),
    (r"\brosemary\b", "Rosemary", PRODUCE, False),
    (r"\bchives\b", "Chives", PRODUCE, False),
    (r"\bthyme\b", "Thyme", PRODUCE, False),
    (r"\bsugar\b", "Sugar", BAKING, True),
]
# Everyday shopping that isn't in a recipe, for things typed straight onto the shopping list
# ("ravioli", "pasta sauce", "dishwashing liquid"). Checked after INGREDIENTS; first match wins.
GROCERIES = [
    # Fresh pasta and the fresh sauces sold beside it, in the fridge.
    (r"\bravioli\b|\btortellini\b|\bgnocchi\b|\bfresh pasta\b|\bpasta sauce\b|\bpesto\b", DAIRY),
    (r"\bbolognese\b|\bsalsa\b|\bjar\b", TINS),
    (r"\bsauce\b|\bketchup\b|\bjam\b|\bvegemite\b|\bnutella\b|\bspread\b|\bstock\b|\bgravy\b", SAUCES),
    (r"\bpasta\b|\bpenne\b|\blasagne\b|\bnoodles?\b|\bcouscous\b|\bquinoa\b", PASTA),
    (r"\bcereal\b|\bweet-?bix\b|\boats\b|\bmuesli\b|\bcoffee\b|\btea\b|\bmilo\b", SNACKS),
    (r"\bchips\b|\bbiscuits?\b|\bcrackers?\b|\bchocolate\b|\blollies\b|\bnuts\b|\bpopcorn\b", SNACKS),
    (r"\bjuice\b|\bsoft drink\b|\bsoda\b|\bcordial\b|\bmineral water\b|\bsparkling\b|\bcoke\b", SNACKS),
    (r"\bbeer\b|\bwine\b|\bcider\b|\bgin\b|\bvodka\b|\bwhisk(e)?y\b|\brum\b|\bprosecco\b", LIQUOR),
    (r"\bice cream\b|\bfrozen\b|\bice\b|\bpizza\b|\bchips\b|\bnuggets\b", FROZEN),
    (r"\byoghurt\b|\bcheese\b|\bmilk\b|\bcream\b|\bbutter\b|\bdips?\b|\bhummus\b|\btofu\b", DAIRY),
    (r"\bbread\b|\brolls?\b|\bwraps?\b|\bcrumpets?\b|\bmuffins?\b|\bbagels?\b|\bcroissants?\b", BAKERY),
    (r"\bham\b|\bsalami\b|\bprosciutto\b|\bolives?\b|\bpastrami\b|\bturkey slices\b", DELI),
    (r"\bchicken\b|\bbeef\b|\bpork\b|\blamb\b|\bmince\b|\bsteak\b|\bsausages?\b|\bfish\b|\bprawns?\b", MEAT),
    (r"\bapples?\b|\bbananas?\b|\bgrapes\b|\bberries\b|\bsalad\b|\btomato(es)?\b|\bonions?\b|\bveg", PRODUCE),
    (r"\bflour\b|\bsugar\b|\beggs?\b|\bbaking\b|\bcake\b", BAKING),
    (r"\btins?\b|\bcans?\b|\bbeans\b|\btuna\b|\bsoup\b|\bchickpeas\b|\blentils\b", TINS),
    (r"\bwrap\b|\bfoil\b|\bbaking paper\b|\bbags\b|\btoilet\b|\bpaper towel\b|\bliquid\b|\btissues\b|"
     r"\btoothpaste\b|\bshampoo\b|\bsoap\b|\bbatteries\b", OTHER),
]

# Everyday items suggested as you type on the shopping list, alongside every ingredient above.
GROCERY_SUGGESTIONS = (
    "Ravioli", "Tortellini", "Gnocchi", "Pasta sauce", "Pesto", "Salsa", "Jam", "Vegemite", "Nutella",
    "Penne", "Couscous", "Quinoa", "Cereal", "Weet-Bix", "Oats", "Muesli", "Coffee", "Tea", "Milo",
    "Chips", "Biscuits", "Crackers", "Chocolate", "Lollies", "Nuts", "Popcorn", "Juice", "Soft drink",
    "Mineral water", "Beer", "White wine", "Cider", "Ice cream", "Frozen pizza", "Frozen chips", "Ice",
    "Yoghurt", "Cheese slices", "Dip", "Hummus", "Tofu", "Bread rolls", "Wraps", "Crumpets",
    "English muffins", "Bagels", "Croissants", "Salami", "Prosciutto", "Olives", "Sliced ham", "Lamb",
    "Prawns", "Fish fillets", "Apples", "Bananas", "Grapes", "Berries", "Salad mix", "Tomatoes",
    "Tinned tuna", "Soup", "Chickpeas", "Lentils", "Baked beans", "Toilet paper", "Paper towel",
    "Dishwashing liquid", "Laundry liquid", "Bin bags", "Cling wrap", "Foil", "Baking paper",
    "Sandwich bags", "Tissues", "Toothpaste", "Shampoo", "Soap", "Batteries",
)

# Ingredient names that differ by country, for the Australia / UK / US switch on recipe pages
# and the shopping list. The book is written in Australian names; (pattern, US, UK, lines_only).
# "$1" carries a plural "s" through. lines_only entries swap only in ingredient lines, where the
# meaning is certain (a word that names one thing in a list but something else in prose).
NAMES = [
    (r"\bcornflour\b", "cornstarch", "cornflour", False),
    (r"\bplain flour\b", "all-purpose flour", "plain flour", False),
    (r"\bself-raising flour\b", "self-rising flour", "self-raising flour", False),
    (r"\bspring onion(s?)\b", "scallion$1", "spring onion$1", False),
    (r"\bbicarb soda\b", "baking soda", "bicarbonate of soda", False),
    (r"\bthickened (?:or pure )?cream\b", "heavy cream", "double cream", False),
    (r"\bbrown onion(s?)\b", "yellow onion$1", "brown onion$1", False),
    (r"\beschallot(s?)\b", "shallot$1", "shallot$1", False),
    (r"\bcapsicum(s?)\b", "bell pepper$1", "pepper$1", False),
    (r"\bcaster sugar\b", "superfine sugar", "caster sugar", False),
    (r"\bicing sugar\b", "powdered sugar", "icing sugar", False),
    (r"\b(beef|pork|chicken) mince\b", "ground $1", "$1 mince", False),
    (r"\bprawn(s?)\b", "shrimp", "prawn$1", False),
    (r"\bcos lettuce\b", "romaine lettuce", "cos lettuce", False),
    (r"\bstreaky bacon\b", "bacon", "streaky bacon", False),
    (r"\bfresh coriander\b|\bcoriander (leaves|sprigs)\b", "cilantro", "fresh coriander", False),
    (r"\bchilli flakes\b", "red pepper flakes", "chilli flakes", False),
    (r"\bzucchini\b", "zucchini", "courgette", False),
    (r"\beggplant(s?)\b", "eggplant$1", "aubergine$1", False),
    (r"\brocket\b", "arugula", "rocket", False),
    (r"\bbeetroot\b", "beet", "beetroot", False),
    (r"\bcob loa(f|ves)\b", "round loa$1", "cob loa$1", False),
    (r"\btinned\b", "canned", "tinned", False),
]


def name_variants(line):
    """Regex alternatives for the US and UK names of anything in this line, so method steps
    written in either still link back to it."""
    out = []
    for pattern, us, uk, _ in NAMES:
        m = re.search(pattern, line, re.I)
        if not m:
            continue
        group = m.group(1) if m.groups() else None
        for name in (us, uk):
            # A plural "(s?)" stays optional; a captured word ("beef") is filled in.
            fill = "s?" if group in ("", "s") else re.escape((group or "").lower())
            alt = r"\b" + re.escape(name.lower()).replace(r"\$1", "$1").replace("$1", fill).replace(r"\ ", " ") + r"\b"
            if alt not in out:
                out.append(alt)
    return out


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
                 "cherry", "baby", "bread", "self-raising", "tipo", "corn", "desiccated", "maple", "oyster", "chicken",
                 "curry"}


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
            if name:
                extra = [v for v in name_variants(line) if v not in item["p"].split("|")]
                if extra:
                    item["p"] = "|".join([item["p"]] + extra)
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
        # "5 garlic cloves" names its count after the ingredient: same unit as "5 cloves garlic".
        if not unit:
            after = re.match(rf"^\S+(?:\s*[–-]\s*\S+)?\s+\w+\s+({'|'.join(COUNTS)})\b", line, re.I)
            if after:
                item["u"] = after.group(1).lower()
    return item
