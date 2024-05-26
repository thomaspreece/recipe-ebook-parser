# Recipe Ebook Parser

Provides a framework to parse recipe ebooks and then upload recipes to [tandoor](https://github.com/TandoorRecipes/recipes)

## Running 

1. First you'll need to run parse.py to grab content from Recipe book. This will create a recipes.db which can be edited/viewed in DB Viewer for SQLite. 
2. Edit recipes.db to fix parsing issues
3. Fix Image sizes by running fix_images.sh
3. Run generate_upload.py to create a OpenEats style JSON export file that can be uploaded to Tandoor to import recipes. Note: you'll need to manually move the images from output folder.
4. Profit 
