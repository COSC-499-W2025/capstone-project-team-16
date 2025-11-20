# this checks all the projects and tries to guess what kind of work it was
# (code, docs, design etc). also counts stuff, finds duration, langs, frameworks, skills

import json
import os
from datetime import datetime
from collections import defaultdict, Counter


def _project_name(filename: str) -> str:
    """guess project name from first folder in the path"""
    path = filename.replace("\\", "/")
    if "/" in path:
        # take folder before first /
        return path.split("/")[0] or "project"
    # if file is just 'main.py' with no folder
    return "project"


def _to_datetime(dt_value):
    """
    zipfile gives time as tuple (Y, M, D, H, M, S)
    just try best, and if it dies, use 'now'.
    """
    #datas from zipfile
    if isinstance(dt_value, (list, tuple)) and len(dt_value) >= 6:
        try:
            y, mo, d, h, mi, s = dt_value[:6]
            return datetime(y, mo, d, h, mi, s)
        except Exception:
            pass

    # ISO string like "2025-11-19T01:23:45"
    if isinstance(dt_value, str):
        try:
            return datetime.fromisoformat(dt_value.replace("Z", ""))
        except Exception:
            pass

    # if everything fails, just return now so code doesn’t crash
    return datetime.now()


# reads the json filters. 
def _load_filters(filename: str = "extractor_filters.json") -> dict:
    
    here = os.path.dirname(__file__)
    path = os.path.join(here, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Filter file not found: {path}")
    except Exception as e:
        print(f"cant load filter file: {e}")

    # fallback if anything broke
    return {"categories": {}, "languages": {}}


    #figure out if this file is code / test / docs / design

def _detect_activity(category: str, filename: str) -> str:

    low = filename.lower()

    # anything with 'test' in name or common test patterns
    if "test" in low or low.endswith((".spec.js", ".test.js", ".test.py", ".spec.ts")):
        return "test"

    if category == "documentation":
        return "documentation"

    if category == "assets":
        return "design"

    # default to code if we are not sure
    return "code"

 #guessing for frameworks based on file names
def _detect_framework(filename: str) -> str:
   
    fn = filename.lower()

    if "package.json" in fn:
        return "Node / React"

    if "requirements.txt" in fn or "pyproject.toml" in fn:
        return "Python (requirements)"

    if "pom.xml" in fn:
        return "Java (Maven)"

    if "build.gradle" in fn:
        return "Java/Kotlin (Gradle)"

    if "cargo.toml" in fn:
        return "Rust (Cargo)"

    return "None"


 # just matches file extensions with skills, like .py -> python skill
def _skill_from_ext(ext: str) -> str | None:
 
    ext = ext.lower()

    if ext == ".py":
        return "Python Programming"

    if ext in (".js", ".ts", ".jsx", ".tsx"):
        return "JavaScript / Frontend"

    if ext in (".html", ".css"):
        return "Web Dev"

    if ext in (".java",):
        return "Java Stuff"

    if ext in (".md", ".pdf", ".docx", ".txt"):
        return "Docs / Writing"

    return None


#main part
def analyze_projects(extracted_data, filters_filename="extractor_filters.json", write_csv=True):
    # read languages etc from json file
    filters = _load_filters(filters_filename)
    lang_map = filters.get("languages", {})

    # group files by project name
    projects = defaultdict(list)
    for row in extracted_data:
        proj = _project_name(row["filename"])
        projects[proj].append(row)

    project_summaries = []

    for proj_name, files in projects.items():
        # only real files, no folders, no junks, added this cause file count wasn't matching. I think it might have been reading junks or hidden files.
        #need to fix later. it is counting the folders as a file.
        clean_files = []
        for f in files:
            name = f["filename"]

            # skip folders
            if not f.get("isFile", True):
                continue

            # skip __MACOSX folder stuff from mac zip
            if "/__MACOSX/" in name or name.startswith("__MACOSX/"):
                continue

            # skip "._" resource files mac adds for each file
            if os.path.basename(name).startswith("._"):
                continue

            clean_files.append(f)

        # if nothing real here then skip this project
        if not clean_files:
            continue

        # duration: based on first + last modified timestamps
        mod_times = [_to_datetime(f["last_modified"]) for f in clean_files]
        first_mod = min(mod_times)
        last_mod = max(mod_times)
        duration_days = (last_mod - first_mod).days + 1

        # counters + sets
        activity_counts = Counter()
        langs = set()
        frameworks = set()
        skills = set()

        # simple collab guess: if we see a .git folder/file anywhere
        is_collab = any(".git" in f["filename"] for f in files)

        # go through all real files in this project
        for f in clean_files:
            filename = f["filename"]
            ext = f.get("extension", "").lower()
            category = f.get("category", "uncategorized")

            # activity type
            act = _detect_activity(category, filename)
            activity_counts[act] += 1

            # language
            lang = lang_map.get(ext, "Unknown")
            if lang != "Unknown":
                langs.add(lang)

            # frameworks
            fw = _detect_framework(filename)
            if fw != "None":
                frameworks.add(fw)

            # skills
            s = _skill_from_ext(ext)
            if s:
                skills.add(s)

        # simple score for ranking
        score = (
            len(clean_files)                 # only count real files
            + duration_days
            + activity_counts["code"] * 2    # give extra points for code
        )

        project_summaries.append({
            "project": proj_name,
            "total_files": len(clean_files),
            "duration_days": duration_days,
            "code_files": activity_counts["code"],
            "test_files": activity_counts["test"],
            "doc_files": activity_counts["documentation"],
            "design_files": activity_counts["design"],
            "languages": ", ".join(sorted(langs)) if langs else "Unknown",
            "frameworks": ", ".join(sorted(frameworks)) if frameworks else "None",
            "skills": ", ".join(sorted(skills)) if skills else "None",
            "is_collaborative": "Yes" if is_collab else "No",
            "score": score,
        })

    # sort projects so biggest score first
    project_summaries.sort(key=lambda x: x["score"], reverse=True)

    # print summary table
    print(f"\n{'Project':18} {'Files':>5} {'Days':>5} {'Code':>5} {'Test':>5} "
          f"{'Doc':>5} {'Des':>5}  {'Langs':18} {'Frameworks':18} {'Collab':>6} {'Score':>6}")
    print("-" * 130)

    for p in project_summaries:
        print(
            f"{p['project']:18} {p['total_files']:5} {p['duration_days']:5} {p['code_files']:5} "
            f"{p['test_files']:5} {p['doc_files']:5} {p['design_files']:5}  "
            f"{p['languages'][:18]:18} {p['frameworks'][:18]:18} {p['is_collaborative']:>6} {p['score']:6}"
        )

    # write csv file if we want
    if write_csv:
        os.makedirs("out", exist_ok=True)
        out_path = os.path.join("out", "project_contribution_summary.csv")
        import csv
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "project", "total_files", "duration_days",
                    "code_files", "test_files", "doc_files", "design_files",
                    "languages", "frameworks", "skills",
                    "is_collaborative", "score",
                ],
            )
            writer.writeheader()
            writer.writerows(project_summaries)
        print(f"saved file to {out_path}")

    return project_summaries
