# this checks all the projects and trys to guess what kind of work it was (code, doc, design etc)
# it also counts stuff, finds duration, lang, frameworks n skills

import json
from datetime import datetime
from collections import defaultdict, Counter
import os


# turns that (2025, 10, 30, 15, 45, 0) thing from the zip into real date
def _to_datetime(val):
    if isinstance(val, (list, tuple)) and len(val) >= 6:
        y, mo, d, h, mi, s = val[:6]
        return datetime(y, mo, d, h, mi, s)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", ""))
        except Exception:
            pass
    return datetime.now()


# gets project name from the path, like "myproject/main.py" to "myproject"
def _project_name(filename: str) -> str:
    path = filename.replace("\\", "/")
    return path.split("/")[0] if "/" in path else "root"


# reads the json filters
def _load_filters(path="src/extractor_filters.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"cant load filter file lol: {e}")
        return {"categories": {}, "languages": {}}


# this just checks what kinda file it is. like test file, docs, code etc
def _detect_activity(category: str, filename: str) -> str:
    low = filename.lower()
    if "test" in low or low.endswith((".spec.js", ".test.js", ".test.py", ".spec.ts")):
        return "test"
    if category == "documentation":
        return "documentation"
    if category == "assets":
        return "design"
    return "code"


# trys to guess frameworks from file names
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


# main part that does everything
def analyze_projects(extracted_data, filters_path="src/extractor_filters.json", write_csv=True):
    filters = _load_filters(filters_path)
    lang_map = filters.get("languages", {})

    # group files by project name
    projects = defaultdict(list)
    for row in extracted_data:
        proj = _project_name(row["filename"])
        projects[proj].append(row)

    project_summaries = []

    # loop each project and get infos
    for proj_name, files in projects.items():
        # gets first and last edit date, so we can tell how long project lasted
        mod_times = [_to_datetime(f["last_modified"]) for f in files]
        first_mod = min(mod_times)
        last_mod = max(mod_times)
        duration_days = (last_mod - first_mod).days + 1

        # make counters for diff file types
        activity_counts = Counter()
        langs = set()
        frameworks = set()
        skills = set()

        # if .git is found then its collab project
        is_collab = any(".git" in f["filename"] for f in files)

        # go through all files in this project
        for f in files:
            filename = f["filename"]
            ext = f.get("extension", "").lower()
            category = f.get("category", "uncategorized")

            # check what type of activity
            act = _detect_activity(category, filename)
            activity_counts[act] += 1

            # check language
            lang = lang_map.get(ext, "Unknown")
            if lang != "Unknown":
                langs.add(lang)

            # check if any frameworks
            fw = _detect_framework(filename)
            if fw != "None":
                frameworks.add(fw)

            # check skill
            s = _skill_from_ext(ext)
            if s:
                skills.add(s)

        # make a score for project (just for ranking)
        score = (
            len(files)
            + duration_days
            + activity_counts["code"] * 2  # give extra points for code
        )

        # save all data
        project_summaries.append({
            "project": proj_name,
            "total_files": len(files),
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

    # print all the info
    print(f"\n{'Project':18} {'Files':>5} {'Days':>5} {'Code':>5} {'Test':>5} {'Doc':>5} {'Des':>5}  {'Langs':18} {'Frameworks':18} {'Collab':>6} {'Score':>6}")
    print("-" * 130)

    for p in project_summaries:
        print(
            f"{p['project']:18} {p['total_files']:5} {p['duration_days']:5} {p['code_files']:5} {p['test_files']:5} {p['doc_files']:5} {p['design_files']:5}  "
            f"{p['languages'][:18]:18} {p['frameworks'][:18]:18} {p['is_collaborative']:>6} {p['score']:6}"
        )

    # saves it to a csv file? don't really need.
    if write_csv:
        import csv
        os.makedirs("out", exist_ok=True)
        with open("out/project_contribution_summary.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "project", "total_files", "duration_days",
                    "code_files", "test_files", "doc_files", "design_files",
                    "languages", "frameworks", "skills",
                    "is_collaborative", "score"
                ]
            )
            writer.writeheader()
            writer.writerows(project_summaries)
        print("saved file to out/project_contribution_summary.csv")

    return project_summarie_
