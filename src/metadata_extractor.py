import json
import os
from repository_extractor import analyze_repo_type

# We should do a shallow extraction regardless of the file type, and selectively deal with larger categorical extractions later
# TODO: run extractors by file type (repo). For repos, validate to make sure it's actually repo. 

# Loads the list of filters JSON and reverses it for easier identification
def load_filters(path="extractor_filters.json"):
    
    try:
        with open(path, "r") as f:
            data = json.load(f)

         # Build extension to category mapping
        ext_to_category = {}
        for category, extensions in data["categories"].items():
            for ext in extensions:
                ext_to_category[ext.lower()] = category

        # Build extension to language mapping
        ext_to_language = {}
        for ext, lang in data.get("languages", {}).items():
            ext_to_language[ext.lower()] = lang

        return ext_to_category, ext_to_language

    except FileNotFoundError:
        print(f"Filter file not found: {path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {path}: {e}")
    except Exception as e:
        print(f"Unexpected error loading filters: {e}")

    # Provide fallback if JSON not found or failed
    return {}, {}


# Loads filters and builds metadata
def base_extraction(file_list):
    extensions, languages = load_filters()
    extracted_data = []


    if extensions:
        for f in file_list:
            filename = f["filename"]
            size = f["size"]
            last_modified = f["last_modified"]
            is_file = False
            language = "undefined"

            #TODO: handle specific files like requirements.txt so they don't fall under broader categories like txt since it is a repo file
            if filename.endswith("/"):
                # Treat as folder
                ext = filename.rstrip("/")
                ext = os.path.basename(ext)
                category = extensions.get(ext, "uncategorized")
                language = ""
            else:
                # Treat as a file and assign category
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                #TODO: add uncategorized file extensions to log to be added to filter list
                category = extensions.get(ext, "uncategorized")
                is_file = True
                
                if category == "source_code" or category == "web_code":
                    language = languages.get(ext, "undefined")

            

            extracted_data.append(
                {
                    "filename": filename,
                    "size": size,
                    "last_modified": last_modified,
                    "extension": ext,
                    "category": category,
                    "isFile": is_file,
                    "language": language
                }
            )


    else:
    #TODO: add this to error log
            
        print("Unable to load filters")
    return extracted_data


# Handle detailed extractions. Loops through extracted data and handles it based on category
def detailed_extraction(extracted_data):
    for entry in extracted_data:
        # Repository extraction
        if entry["category"] == "repository":
            repo_info = analyze_repo_type(entry)
            # If repo extraction succeeded, merge results into this entry
            if repo_info and repo_info.get("is_valid", False):
                entry.update(repo_info)
                # Print the repo information for debugging
                print("Repo analysis succeeded:")
                print(f"  Name: {repo_info.get('repo_name')}")
                print(f"  Root: {repo_info.get('repo_root')}")
                print(f"  Authors: {repo_info.get('authors')}")
                print(f"  Branch count: {repo_info.get('branch_count')}")
                print(f"  Has merges: {repo_info.get('has_merges')}")
                print(f"  Project type: {repo_info.get('project_type')}")
            else:
                print(f"Skipping invalid or failed repo: {entry['filename']}")
            