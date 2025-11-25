import json
import os
from repository_extractor import analyze_repo_type

# We should do a shallow extraction regardless of the file type, and selectively deal with larger categorical extractions later


# Loads the list of filters JSON and reverses it for easier identification
def load_filters(filename=None):

    if filename is None:
        here = os.path.dirname(__file__)
        filename = os.path.join(here, "extractor_filters.json")
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
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

        framework_files = set(name.lower() for name in data.get("frameworks", []))



        return{"extensions":ext_to_category, "languages":ext_to_language, "frameworks":framework_files}

    except FileNotFoundError:
        print(f"Filter file not found: {filename}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {filename}: {e}")
    except Exception as e:
        print(f"Unexpected error loading filters: {e}")

    # Provide fallback if JSON not found or failed
    return {}


# Loads filters and builds metadata
def base_extraction(file_list, filters):
    #extensions, languages = load_filters()
    extracted_data = []
    extensions = filters.get("extensions", {})
    languages = filters.get("languages", {})
    frameworks_list = filters.get("frameworks", {})

    if extensions:
        for f in file_list:
            filename = f["filename"]
            size = f["size"]
            last_modified = f["last_modified"]
            is_file = f["isFile"]
            language = ""

            
            if not is_file:
                # Treat as folder
                ext = filename.rstrip("/")
                ext = os.path.basename(ext)
                category = extensions.get(ext, "uncategorized")
                language = ""
            else:
                
                is_file = True

                # Check if it's a framework file
                basename = os.path.basename(filename).lower()
                if basename in frameworks_list:
                    category = "framework"
                    ext = ""
                    language = ""
                else: 
                        # It is not a framework file. Continue on
                        # Extract extension, and assign a category based on it 
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower()

                    #TODO: add uncategorized file extensions to log to be added to filter list
                    category = extensions.get(ext, "uncategorized")


                    # Assign programming language if detected as source_code or web_code
                    if category in( "source_code", "web_code"):
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


def detect_frameworks(framework_file_entry):
    """
    Given a framework file entry, extract the ecosystem and dependencies.
    """
    filename = os.path.basename(framework_file_entry["filename"]).lower()
    full_path = framework_file_entry["filename"]
    result = {"ecosystem": None, "detected": []}

    # ---- PYTHON ----
    if filename in ("requirements.txt", "environment.yml", "pipfile", "pyproject.toml"):
        result["ecosystem"] = "python"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            for line in lines:
                if line and not line.startswith("#"):
                    pkg = line.split("==")[0].split(">=")[0].strip()
                    if pkg:
                        result["detected"].append(pkg)

        except Exception:
            pass  # No crash — this runs inside extraction

    # ---- NODE ----
    elif filename == "package.json":
        result["ecosystem"] = "node"
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            deps = data.get("dependencies", {})
            dev = data.get("devDependencies", {})

            result["detected"] = list(deps.keys()) + list(dev.keys())

        except Exception:
            pass

    # ---- RUST ----
    elif filename == "cargo.toml":
        result["ecosystem"] = "rust"

    # ---- GO ----
    elif filename == "go.mod":
        result["ecosystem"] = "go"

    # ---- JAVA (Maven) ----
    elif filename == "pom.xml":
        result["ecosystem"] = "java"

    # ---- JAVA (Gradle) ----
    elif filename == "build.gradle":
        result["ecosystem"] = "java"

    # ---- RUBY ----
    elif filename == "gemfile":
        result["ecosystem"] = "ruby"

    # ---- DOCKER ----
    elif filename == "dockerfile":
        result["ecosystem"] = "docker"

    return result


# Handle detailed extractions. Loops through extracted data and handles it based on category
def detailed_extraction(extracted_data):
    repositories = []

      # Identify repo roots and gather repo metadata
    for entry in extracted_data:
        if entry["category"] == "repository":
            repo_info = analyze_repo_type(entry)

            if repo_info and repo_info.get("is_valid", False):
                # Create a new project object
                repositories.append({
                    "repo_name": repo_info["repo_name"],
                    "repo_root": repo_info["repo_root"],
                    "authors": repo_info["authors"],
                    "contributors": repo_info["contributors"],
                    "branch_count": repo_info["branch_count"],
                    "has_merges": repo_info["has_merges"],
                    "project_type": repo_info["project_type"],
                    "duration_days": repo_info["duration_days"],
                    "commit_frequency": repo_info["commit_frequency"],
                    "files": []  # will fill in the next step
                })

            else:
                print(f"Skipping invalid or failed repo: {entry['filename']}")

    #Attach files to the correct project
    for project in repositories:
        root = project["repo_root"]

        for file_entry in extracted_data:
            # If file path starts with the repo root, it's part of that project
            if file_entry["filename"].startswith(root):
                project["files"].append(file_entry)

                # If the file is a detected framework, then analyze it.
                if file_entry["category"] == "framework":
                    framework_info = detect_frameworks(file_entry)
                    project.setdefault("frameworks", []).append(framework_info)


            
        # Return both structures
    return {
        "files": extracted_data,
        "projects": repositories
    }

