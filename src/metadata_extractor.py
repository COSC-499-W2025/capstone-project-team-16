import json
import os


# We should do a shallow extraction regardless of the file type, and selectively deal with larger categorical extractions later


# Loads the list of filters JSON and reverses it for easier identification
def load_filters(path="extractor_filters.json"):
    
    try:
        with open(path, "r") as f:
            data = json.load(f)

        # Flips the category with extension for easier comparison
        ext_to_category = {}
        for category, extensions in data["categories"].items():
            for ext in extensions:
                ext_to_category[ext.lower()] = category

        return ext_to_category

    except FileNotFoundError:
        print(f"Filter file not found: {path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
    except Exception as e:
        print(f"Unexpected error loading filters: {e}")

    # Provide fallback if JSON not found or failed
    return {}


# Loads filters and builds metadata
def base_extraction(file_list):
    filters = load_filters()
    extracted_data = []


    if filters:
        for f in file_list:
            filename = f["filename"]
            size = f["size"]
            last_modified = f["last_modified"]
            is_file = False

            #TODO: handle specific files like requirements.txt so they don't fall under broader categories like txt since it is a repo file
            if filename.endswith("/"):
                # Treat as folder
                ext = filename.rstrip("/")
                ext = os.path.basename(ext)
                category = filters.get(ext, "uncategorized")
            else:
                # Treat as a file and assign category
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                #TODO: add uncategorized file extensions to log to be added to filter list
                category = filters.get(ext, "uncategorized")
                is_file = True
                

            

            extracted_data.append(
                {
                    "filename": filename,
                    "size": size,
                    "last_modified": last_modified,
                    "extension": ext,
                    "category": category,
                    "isFile": is_file
                }
            )


    else:
    #TODO: add this to error log
            
        print("Unable to load filters")
    return extracted_data