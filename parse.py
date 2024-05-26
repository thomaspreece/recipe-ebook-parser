
import ebooklib
from ebooklib import epub
import argparse
import os 
import json
from bs4 import BeautifulSoup
import sqlite3
from slugify import slugify
import shutil 

parser_pon_comfort = {
    "combine_pages": False, 
    "required": [
    ],
    "title_selector": {
        "type": "h2",
        "attrs": {
            "class": "recipe_head"
        }
    },
    "description_selector": {
        "type": "p",
        "attrs": {
            "class": lambda L: L and L in ["recipe_description", "recipe_intro", "recipe_text"]
        }
    },
    "steps_selector": {
        "type": "p",
        "attrs": {
            "class": "recipe_text"
        },
        "number": 0
    },
    "ingredients_selector": {
        "type": "p",
        "attrs": {
            "class": lambda L: L and L in ["ing", "ingT", "ing_head"]
        },
        "number": 0
    },
    "image_selector": {
        "type": "img",
        "attrs": {
            "class": lambda L: L and (L.startswith('portrait') or L.startswith('imglandscape'))
        }
    },
    "preptime_selector": {
        "type": "img",
        "attrs": {
            "src": "docimages/time.jpg"
        },
        "next_element": "span"
    },
    "cooktime_selector": {
        "type": "img",
        "attrs": {
            "src": "docimages/cock.jpg"
        },
        "next_element": "span"
    },
    "serves_selector": {
        "type": "img",
        "attrs": {
            "src": "docimages/spoon.jpg"
        },
        "next_element": "span"
    },

}

parsers = {
    "pon-comfort": parser_pon_comfort
}

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="filename", required=True,
                    help="input epub book", metavar="FILE",
                    type=lambda x: is_valid_file(parser, x))
parser.add_argument("-p", dest="parser" ,help="parser to use with provided file", required=True, choices=parsers.keys())
parser.add_argument("-b", dest="bookname" ,help="Name of book", required=True)
parser.add_argument('-v', dest='verbose', action='store_true')
parser.set_defaults(verbose=False)
args = parser.parse_args()


ACTIVE_PARSER = args.parser
BOOK_PATH = args.filename
BOOK_NAME = args.bookname
OUTPUT_LOCATION = "output"
IMAGE_OUTPUT_LOCATION = f"{OUTPUT_LOCATION}/images"

shutil.rmtree(IMAGE_OUTPUT_LOCATION)

os.makedirs(OUTPUT_LOCATION, exist_ok=True)
os.makedirs(IMAGE_OUTPUT_LOCATION, exist_ok=True)



VERBOSE = args.verbose

parser_settings = parsers[ACTIVE_PARSER]

def get_text_between_tags(cur,end):
    return ' '.join([text for text in between(cur,end)])

def between(cur, end):
    while cur and cur != end:
        yield str(cur)
        cur = cur.next_sibling

def apply_selector(selector_key, tag_key):
    selector = parser_settings[selector_key]
    selector_occurrence = selector.get("occurrence", 0)
    selector_number = selector.get("number", 1)
    selector_separator = selector.get("separator", None)
    selector_next = selector.get("next_element", None)

    return_items = []

    tags = subsoup.find_all(selector["type"], attrs=selector["attrs"])
    if selector_number == 0:
        selector_number = len(tags) - selector_occurrence
    if len(tags) >= selector_occurrence + selector_number:
        for i in range(0, selector_number):
            tag = tags[selector_occurrence+i]
            if selector_next:
                tag = tag.find_next(selector_next)            
            if tag_key == "text":
                return_items.append(tag.text)
            else:
                return_items.append(tag[tag_key])
        if len(return_items) == 1:
            return return_items[0]
        elif selector_separator != None:
            return selector_separator.join(return_items)
        else:
            return return_items
    else:
        if selector_key in parser_settings["required"]:
            raise ValueError(f"Could not extract required key: {selector_key}")
        else:
            return None 



def extract_image(image_key, image_slug):
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_IMAGE and item.get_name() and item.get_name().endswith(image_key):
            extention = image_key.split(".")[-1]
            file_name = f"{image_slug}.{extention}"

            file_path = f"{IMAGE_OUTPUT_LOCATION}/{file_name}"
            with open(file_path, "wb") as image_file:
                image_file.write(item.get_content())
            return {
                "filename": file_name,
                "filepath": file_path,
                "blob": item.get_content()
            }


tag_matching_foods = [
    {
        "name": "Meat",
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
        "matches": [
            "feta",
            "mascarpone",
            "cheddar",
            "parmesan",
            "halloumi",
            "edam",
            "paneer"
        ]
    },
]

book = epub.read_epub(BOOK_PATH)

# Read Sections
html_sections = []
if parser_settings["combine_pages"]:
    html_sections.append("")

print("------------------------")
print("Parsing Pages of Epub")
print("------------------------")
for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        print('NAME : ', item.get_name())
        if parser_settings["combine_pages"]:
            html_sections[0] += item.get_content()
        else:
            html_sections.append(item.get_content())

print("------------------------")
print("Parsing Recipes")
print("------------------------")

if os.path.isfile(f"{OUTPUT_LOCATION}/recipes.db"):
    os.remove(f"{OUTPUT_LOCATION}/recipes.db")

conn = sqlite3.connect(f"{OUTPUT_LOCATION}/recipes.db")
cur = conn.cursor()

cur.execute("CREATE TABLE recipes(title, image, description, preptime, cooktime, serves, ingredients, steps, tags, image_filename)")


for html_section in html_sections:
    soup = BeautifulSoup(html_section, features="lxml")
    previous_title = None 
    if "section_selector" in parser_settings:
        section_selector = parser_settings["section_selector"]
        title_selector = parser_settings["title_selector"]
    else:
        section_selector = parser_settings["title_selector"]
        title_selector = parser_settings["title_selector"]

    recipe_section_tags = []
    recipe_sections = []

    # Extract Title Tags and Split HTML into sections based on these titles
    for recipe_title_tag in soup.find_all(section_selector["type"], attrs=section_selector["attrs"]):
        recipe_section_tags.append(recipe_title_tag)
    
    for i in range(0,len(recipe_section_tags)-1):
        recipe_sections.append(get_text_between_tags(recipe_section_tags[i], recipe_section_tags[i+1]))        

    if len(recipe_section_tags) > 0:
        recipe_sections.append(get_text_between_tags(recipe_section_tags[-1], None))        
        
    for recipe_section in recipe_sections:
        subsoup = BeautifulSoup(recipe_section, features="lxml")
        recipe_title_tag = subsoup.find(title_selector["type"], attrs=title_selector["attrs"])
        recipe_title = recipe_title_tag.text
        print(recipe_title)
        
        try:
            description = apply_selector("description_selector", "text")
            if description == None:
                description = ""
            steps = apply_selector("steps_selector", "text")
            ingredients = apply_selector("ingredients_selector", "text")
            recipe_image = apply_selector("image_selector", "src")
            preptime = apply_selector("preptime_selector", "text")
            cooktime = apply_selector("cooktime_selector", "text")
            serves = apply_selector("serves_selector", "text")
            recipe_tags = []

            was_matched = False 
            for tag in tag_matching_foods:
                if (any(match in description.lower() for match in tag["matches"]) or 
                any(match in " ".join(steps).lower() for match in tag["matches"]) or 
                any(match in " ".join(ingredients).lower() for match in tag["matches"]) or 
                any(match in recipe_title.lower() for match in tag["matches"])):
                    recipe_tags.append(tag["name"])
                    was_matched = True 
            if not was_matched:
                recipe_tags.append("Vegetarian")
            recipe_tags.append(f'Book: {BOOK_NAME}')

            if recipe_image:
                image = extract_image(recipe_image, slugify(recipe_title))
                image_blob = image["blob"]
                image_filename = image["filename"]
            else:
                image_blob = None 
                image_filename = None

            cur.execute("INSERT INTO recipes VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                recipe_title,
                image_blob,
                description,
                preptime,
                cooktime,
                serves,
                json.dumps(ingredients),
                json.dumps(steps),
                json.dumps(recipe_tags),
                image_filename
            ])
            conn.commit()

            if VERBOSE:
                print(f"title: {recipe_title}")     
                print(f"desc: {description}")
                print(f"steps: {steps}")
                print(f"ingredients: {ingredients}")
                print(f"image: {recipe_image}")
                print(f"prep: {preptime}")
                print(f"cook: {cooktime}")            
                print(f"serves: {serves}")       
        except ValueError as e:
            print(f"WARNING: {recipe_title} failed to parse: {e}")

if conn:
    conn.close()