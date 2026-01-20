import os
import json
import toml  
import yaml  
import shutil
from repository_extractor import analyze_repo_type


def _center_text(text):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def _print_banner(title, line_char="~", min_width=23):
    line_width = max(len(title), min_width)
    line = line_char * line_width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))


def _print_repo_skip(path):
    _print_banner("REPO SKIPPED")
    print(_center_text("Invalid or failed repo:"))
    print(_center_text(path))

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
        print(f"[metadata_extractor] Filter file not found: {filename}")
    except json.JSONDecodeError as e:
        print(f"[metadata_extractor] JSON decode error in {filename}: {e}")
    except Exception as e:
        print(f"[metadata_extractor] Unexpected error loading filters: {e}")

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
        msg = "[metadata_extractor] Unable to load filters; using empty mappings."
        filters.setdefault("error_log", []).append(msg)
        print(msg)
    return extracted_data


def detect_frameworks(framework_file_entry):
    """
    Given a framework file entry, extract dependencies.
    Returns a list of dependency names.
    """
    filename = os.path.basename(framework_file_entry["filename"]).lower()
    full_path = framework_file_entry["filename"]
    dependencies = []

    try:
        # ---- PYTHON ----
        if filename in ("requirements.txt", "environment.yml", "pipfile", "pyproject.toml"):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                with open(full_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                for pkg in data.get("dependencies", []):
                    dependencies.append(pkg)
            else:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                for line in lines:
                    if line and not line.startswith("#"):
                        pkg = line.split("==")[0].split(">=")[0].strip()
                        if pkg:
                            dependencies.append(pkg)

        # ---- NODE ----
        elif filename == "package.json":
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies", {})
            dev = data.get("devDependencies", {})
            dependencies.extend(list(deps.keys()))
            dependencies.extend(list(dev.keys()))

        # ---- RUST ----
        elif filename in ("cargo.toml", "Cargo.toml"):
            with open(full_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
            deps = data.get("dependencies", {})
            dependencies.extend(list(deps.keys()))

        # ---- GO ----
        elif filename == "go.mod":
            with open(full_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("require "):
                        pkg = line.replace("require", "").strip().split()[0]
                        dependencies.append(pkg)

        # ---- JAVA (Maven) ----
        elif filename == "pom.xml":
            dependencies.append("See pom.xml")  # TODO: implement

        # ---- JAVA (Gradle) ----
        elif filename in ("build.gradle", "settings.gradle"):
            dependencies.append("See build.gradle")  # TODO: implement

        # ---- RUBY ----
        elif filename.lower() == "gemfile":
            with open(full_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("gem "):
                        pkg = line.split()[1].strip("\"'")
                        dependencies.append(pkg)

        # ---- DOCKER ----
        elif filename.lower() in ("dockerfile", "docker-compose.yml"):
            dependencies.append("Dockerfile dependencies")  # TODO: implement

    except Exception:
        pass  # silently skip errors for extraction

    return dependencies


# Handle detailed extractions. Loops through extracted data and handles it based on category
def detailed_extraction(extracted_data, advanced_options, filters=None):
    repositories = []
    if advanced_options is None:
    # default: everything ON
        advanced_options = {
            "programming_scan": True,
            "framework_scan": True,
            "skills_gen": True,
            "resume_gen": True
        }

      # Identify repo roots and gather repo metadata
    for entry in extracted_data:
        if entry["category"] == "repository":
            repo_info = analyze_repo_type(entry)

            if repo_info and repo_info.get("is_valid", False):
                
                # Enrich contributor stats with categories (e.g. .py -> source_code)
                if filters and "contributors" in repo_info:
                    ext_map = filters.get("extensions", {})
                    for contrib in repo_info["contributors"]:
                        loc_by_cat = {}
                        for ext, stats in contrib.get("loc_by_type", {}).items():
                            cat = ext_map.get(ext.lower(), "uncategorized")
                            if cat not in loc_by_cat:
                                loc_by_cat[cat] = {"insertions": 0, "deletions": 0}
                            loc_by_cat[cat]["insertions"] += stats.get("insertions", 0)
                            loc_by_cat[cat]["deletions"] += stats.get("deletions", 0)
                        contrib["loc_by_category"] = loc_by_cat

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
                _print_repo_skip(entry["filename"])

    #Attach files to the correct project
    for project in repositories:
        root = project["repo_root"]

        # initialize a set to accumulate dependencies
        project_dependencies = set()

        for file_entry in extracted_data:
            # If file path starts with the repo root, it's part of that project
            if file_entry["filename"].startswith(root):
                project["files"].append(file_entry)

                # If the file is a framework file, extract dependencies from it
                if file_entry["category"] == "framework" and advanced_options.get("framework_scan", True):
                    deps = detect_frameworks(file_entry)  # returns a list
                    project_dependencies.update(deps)  # accumulate in a set

        # Store the final list of dependencies in the project
        project["frameworks"] = list(project_dependencies)

            
        # Return both structures
    return {
        "files": extracted_data,
        "projects": repositories
    }
