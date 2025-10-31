import json
import os


# We should do a shallow extraction regardless of the file type, and selectively deal with larger categorical extractions later 


# Loads the list of filters JSON and reverses it for easier identification
def load_filters(path="extractor_filters.json"):
    #TODO surround in try statement and provide alternative if JSON is not found
    with open(path, "r") as f:
        data = json.load(f)


    # Flips the category with extension for easier comparison
    ext_to_category= {}
    for category, extensions in data["categories"].items():
        for ext in extensions:
            ext_to_category[ext.lower()] = category

    return ext_to_category


# Loads filters and builds metadata
def base_extraction(file_list):
    filters = load_filters()
    extracted_data = []


    if filters:
        for f in file_list:
            _, ext = os.path.splittext(f["filename"])
            ext = ext.lower()
            filename = f["filename"]
            size = f["size"]
            last_modified = f["last_modified"]

            #If an extension is found, the item is given a category
            #TODO add uncategorized file extensions to log to be added to filter list
            category = filters.get(ext, "uncategorized")

            extracted_data.append(
                {
                    "filename": filename,
                    "size": size,
                    "last_modified": last_modified,
                    "extension": ext,
                    "category": category
                }
            )


        else:
            #TODO add this to error log
            
            print("Unable to load filters")