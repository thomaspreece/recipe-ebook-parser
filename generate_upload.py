
import os 
import json
import sqlite3
import re 
from datetime import datetime
from slugify import slugify
import unicodedata as ud
from unicodedata import numeric

OUTPUT_LOCATION = "output"

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

def get_number(text):
    return int(re.sub("[^0-9]*","", text))

def get_vulgar_fraction_number(i):
    # samples = ["3¼","19¼","3 ¼","10"]
    if len(i) == 1:
        v = numeric(i)
    elif i[-1].isdigit():
        # normal number, ending in [0-9]
        v = float(i)
    else:
        # Assume the last character is a vulgar fraction
        v = float(i[:-1]) + numeric(i[-1])
    return v

def parse_ingredient(ingredient):
    parsed_ingredient = {
        "measurement": None,
        "number": 0,
        "title": ""
    }

    # Look for vulgar fractions at start of ingredient 
    vulgar_fraction = re.search("^([0-9]+\ ?)?[\u2150-\u215E\u00BC-\u00BE]", ingredient, flags=re.MULTILINE)
    if vulgar_fraction:
        number = get_vulgar_fraction_number(vulgar_fraction[0])
        ingredient = ingredient[0:vulgar_fraction.start()] + str(number) + ingredient[vulgar_fraction.end():]

    ingredient_splits = ingredient.split(" ")

    # Split apart number and measurement e.g. 5ml
    s = re.search(r"([0-9]+(\.[0-9]+)?)([^0-9\.]+)", ingredient_splits[0])
    if s:
        g = s.groups()
        ingredient_splits.pop(0)
        ingredient_splits.insert(0, g[2])
        ingredient_splits.insert(0, g[0])

    try:
        parsed_ingredient["number"] = float(ingredient_splits[0].strip())
        ingredient_splits.pop(0)
    except ValueError:
        pass

    if ingredient_splits[0].lower() in valid_measurements:
        parsed_ingredient["measurement"] = ingredient_splits[0].strip()
        ingredient_splits.pop(0)
    
    parsed_ingredient["title"] = " ".join(ingredient_splits)
    return parsed_ingredient

print("------------------------")
print("Reading Recipes")
print("------------------------")

if not os.path.isfile(f"{OUTPUT_LOCATION}/recipes.db"):
    raise ValueError("Cannot find: {OUTPUT_LOCATION}/recipes.db")

conn = sqlite3.connect(f"{OUTPUT_LOCATION}/recipes.db")
cur = conn.cursor()

cur.execute('SELECT title, image_filename, description, preptime, cooktime, serves, ingredients, steps, tags from recipes')

openeats_output = []

recipe_obj_index = 1
ingredientgroup_obj_index = 1
tag_obj_index = 1
ingredient_obj_index = 1

tag_objs = {}

rows = cur.fetchall()
for row in rows:
    print(row[0])
    title = row[0]
    image_filename = row[1]
    description = row[2]
    preptime = row[3]
    cooktime = row[4]
    serves = row[5] 
    ingredients = json.loads(row[6])
    steps = json.loads(row[7])
    tags = json.loads(row[8])
    tag_indexes = []

    for tag in tags:
        if not tag in tag_objs:
            tag_objs[tag] = {
                "fields": {
                    "slug": slugify(tag),
                    "title": tag
                },
                "model": "recipe_groups.tag",
                "pk": tag_obj_index
            }
            tag_obj_index += 1
        tag_indexes.append(tag_objs[tag]["pk"])
        

    date_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    recipe_obj = {
        "fields": {
            "author": 1,
            "cook_time": get_number(cooktime),
            "prep_time": get_number(preptime),
            "course": '',
            "cuisine": '',
            "directions": "\n\n".join(steps),
            "info": "",
            "pub_date": date_time,
            "public": True,
            "servings": get_number(serves),
            "slug": slugify(title),
            "source": "",
            "tags": tag_indexes,
            "title": title,
            "update_date": date_time
        },
        "model": "recipe.recipe",
        "pk": recipe_obj_index
    }
    if image_filename:
        recipe_obj["fields"]["photo"] = f"recipe-parser/{image_filename}"

    openeats_output.append(recipe_obj)

    ingredientgroup_obj = {
        "fields": {
            "recipe": recipe_obj_index,
            "title": ""
        },
        "model": "ingredient.ingredientgroup",
        "pk": ingredientgroup_obj_index
    }
    openeats_output.append(ingredientgroup_obj)

    for ingredient in ingredients:
        parsed_ingredient = parse_ingredient(ingredient)
        ingredient_obj = {
            "fields": {
                "denominator": 1.0,
                "ingredient_group": ingredientgroup_obj_index,
                "measurement": parsed_ingredient["measurement"],
                "numerator": float(parsed_ingredient["number"]),
                "title": parsed_ingredient["title"]
            },
            "model": "ingredient.ingredient",
            "pk": ingredient_obj_index
        }
        ingredient_obj_index += 1
        openeats_output.append(ingredient_obj)


    recipe_obj_index += 1
    ingredientgroup_obj_index += 1
    
    for i,k in enumerate(tag_objs):
        openeats_output.append(tag_objs[k])

if conn:
    conn.close()

with open(f"{OUTPUT_LOCATION}/recipes.json", "w") as f:
    json.dump(openeats_output, f, indent=2)