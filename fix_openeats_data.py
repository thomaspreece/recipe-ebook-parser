import json
import re 

with open('openeats_export/recipe_ingredients.json') as f:
    data = json.load(f)


measurements = []
books = []
max_tag = 0

for item in data:
    fields = item["fields"]
    if item["model"] == "ingredient.ingredient":
        if fields["measurement"]:
            measurements.append(fields["measurement"].lower())

    if item["model"] == "recipe.recipe":
        if len(fields["info"]) > 0:
            books.append(re.sub('p[0-9]+', '', fields["info"].lower()))
        if len(fields["directions"].split("\n")) <= 1:
            books.append(re.sub('p[0-9]+', '', fields["directions"].lower()))

    if item["model"] == "recipe_groups.tag":
        if item["pk"] > max_tag:
            max_tag = item["pk"]

measurements = list(set(measurements))
books = list(set(books))

print(json.dumps(books,indent=2))
#print(json.dumps(measurements, indent=2))

valid_measurements = [
  "pinch",
  "g",
  "litres",
  "level",
  "cm",
  "cans",
  "little",
  "large",
  "tin",
  "lean",
  "ml",
  "kg",
  "l",
  "bunch",
  "tbsp",
  "tsp",
  "small",
  "litre",
  "pack",
  "medium",
  "cm-piece",
  "grams"
]

tag_matching_foods = [
    {
        "name": "Meat",
        "slug": "Meat",
        "matches": [
            "chicken",
            "lamb",
            "beef",
            "pork",
            "bacon",
            "sausage",
            "turkey",
            "duck",
            "goose",
            "chorizo",
            "meat",
            "ham"
        ]
    },
    {
        "name": "Seafood",
        "slug": "Seafood",
        "matches": [
            "prawn",
            "salmon",
            "haddock",
            "scallop",
            "cod",
            "basa",
            "mackerel",
            "fish",
            "seafood"
        ]
    },
    {
        "name": "Cheese",
        "slug": "Cheese",
        "matches": [
            "feta",
            "mascarpone",
            "cheddar",
            "parmesan"
        ]
    },
]

tag_matching_books = [
    {
        "name": "Book: Pinch of Nom - Everyday Light (Red)",
        "slug": "PinchOfNom-EveryDayLight-Red",
        "matches": [
            "red pinch of nom",
            "pon red"
        ]
    },
    {
        "name": "Book: Pinch of Nom - Comfort Food (Yellow)",
        "slug": "PinchOfNom-ComfortFood-Red",
        "matches": [
            "yellow pinch of nom",
            "yellow pon"
        ]
    },
    {
        "name": "Book: Pinch of Nom (Green)",
        "slug": "PinchOfNom-Green",
        "matches": [
            "green pinch of nom",
            "green pon"
        ]
    },
    {
        "name": "Book: Pinch of Nom - Quick and Easy (Blue)",
        "slug": "PinchOfNom-QuickAndEasy-Blue",
        "matches": [
            "pinch of nom quick and easy"
        ]
    },
    {
        "name": "Book: Wagamama - Feel Your Soul",
        "slug": "Wagamama-FeedYourSoul",
        "matches": [
            "wagamama - feed your soul"
        ]
    },
    {
        "name": "Book: Slimming Eats",
        "slug": "SlimmingEats",
        "matches": [
            "slimming eats"
        ]
    },
    {
        "name": "Book: Recipes To Try",
        "slug": "RecipesToTry",
        "matches": [
            "recipes to try"
        ]
    },
    {
        "name": "Book: 30 Minute Mowgli",
        "slug": "30MinuteMowgli",
        "matches": [
            "30 minute mowgli"
        ]
    },
    {
        "name": "Book: 50 Great Curries of Thailand",
        "slug": "50GreatCurries",
        "matches": [
            "50 great curries of thailand"
        ]
    },
    {
        "name": "Book: The Hairy Bikers' - Great Curries",
        "slug": "TheHairyBikers-GreatCurries",
        "matches": [
            "the hairy bikers"
        ]
    },
    {
        "name": "Book: Two Chubby Cubs - Fast and Filling",
        "slug": "TwoChubbyCubs-FastAndFilling",
        "matches": [
            "two chubby cubs"
        ]
    },
    {
        "name": "Book: Leon",
        "slug": "Leon",
        "matches": [
            "leon"
        ]
    }
]

for tag in tag_matching_books:
    max_tag += 1
    tag_openeats = {
        "fields": {
            "slug": tag["slug"],
            "title": tag["name"]
        },
        "model": "recipe_groups.tag",
        "pk": max_tag
    }
    data.append(tag_openeats)
    tag["pk"] = max_tag 


for tag in tag_matching_foods:
    max_tag += 1
    tag_openeats = {
        "fields": {
            "slug": tag["slug"],
            "title": tag["name"]
        },
        "model": "recipe_groups.tag",
        "pk": max_tag
    }
    data.append(tag_openeats)
    tag["pk"] = max_tag 

max_tag += 1
tag_openeats = {
    "fields": {
        "slug": "Vegetarian",
        "title": "Vegetarian"
    },
    "model": "recipe_groups.tag",
    "pk": max_tag
}
data.append(tag_openeats)

for item in data:
    fields = item["fields"]
    if item["model"] == "ingredient.ingredient":
        if fields["measurement"]:
            if not fields["measurement"].lower() in valid_measurements:
                fields["title"] = fields["measurement"]+" "+fields["title"] 
                fields["measurement"] = None 
    if item["model"] == "recipe.recipe":
        for tag in tag_matching_books:
            if any(match in fields["info"].lower() for match in tag["matches"]) or any(match in fields["directions"].lower() for match in tag["matches"]):
                fields["tags"].append(tag["pk"])
        was_matched = False 
        for tag in tag_matching_foods:
            if (any(match in fields["info"].lower() for match in tag["matches"]) or 
              any(match in fields["directions"].lower() for match in tag["matches"]) or 
              any(match in fields["title"].lower() for match in tag["matches"])):
                fields["tags"].append(tag["pk"])
                was_matched = True 
        if not was_matched:
            fields["tags"].append(max_tag)
        fields["directions"]= fields["directions"].replace("\n", "\n\n") + "\n\n"


with open("openeats_export/fixed.json", "w") as f:
    json.dump(data, f, indent=2)