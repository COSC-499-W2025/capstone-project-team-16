# this checks all the projects and tries to guess what kind of work it was
# (code, docs, design etc). also counts stuff, finds duration, langs, frameworks, skills

import json
import os
from datetime import datetime
from collections import defaultdict, Counter


# printing repo

def print_repo_summary(
    proj_name,
    repo_name,
    repo_root,
    repo_authors,
    repo_contributors,
    branch_count,
    has_merges,
    project_type,
    repo_duration_days,
    commit_frequency,
):
    print("\n[Repository Metadata]")
    print(f" Project:          {proj_name}")
    print(f" Repo Name:        {repo_name}")
    print(f" Repo Root:        {repo_root}")
    print(
        f" Authors:          {', '.join(sorted(repo_authors)) if repo_authors else 'None'}"
    )
    print(
        f" Contributors:     {', '.join(sorted(repo_contributors)) if repo_contributors else 'None'}"
    )
    print(f" Branch Count:     {branch_count}")
    print(f" Has Merges:       {has_merges}")
    print(f" Project Type:     {project_type}")
    print(f" Repo Duration:    {repo_duration_days} days")
    print(f" Commit Freq:      {commit_frequency}")
    print("-----------------------------------------------")


# --------------------------------------------------------
# guessing project / dates / activity

# TODO: move to extractor. Possibly rework as the guessing can be improved
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
    zipfile gives time as tuple (Y, M, D, H, M, S).
    also supports ISO strings. if it dies, use 'now'.
    """
    # data from zipfile
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



# figure out if this file is code / test / docs / design
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


# guessing for frameworks based on file names
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
def _skill_from_ext(ext: str):
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


# MAIN ANALYSIS FUNCTION

def analyze_projects(extracted_data, filters, detailed_data=None, write_csv=True):

    # not heavily used now, but keep in case we want lang fallback later
    lang_map = filters.get("languages", {})

    # map each file path to its repo metadata (if advanced scan ran)
    file_to_repo = {}
    if isinstance(detailed_data, dict):
        for repo in detailed_data.get("projects", []):
            for f in repo.get("files", []):
                fname = f.get("filename")
                if fname:
                    file_to_repo[fname] = repo

    # group files by project name
    projects = defaultdict(list)
    for row in extracted_data:
        proj = _project_name(row["filename"])
        projects[proj].append(row)

    project_summaries = []

    for proj_name, files in projects.items():
        # only real files, no folders, no junk
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

        # repo / git infos (from detailed_extraction / repo_extractor)
        repo_names = set()
        repo_roots = set()
        repo_authors = set()
        repo_contributors = set()
        branch_counts = []
        has_merges_flags = []
        project_types = []
        repo_duration_vals = []
        commit_freqs = []

        # go through all real files in this project
        for f in clean_files:
            filename = f["filename"]
            ext = f.get("extension", "").lower()
            category = f.get("category", "uncategorized")

            # activity type
            act = _detect_activity(category, filename)
            activity_counts[act] += 1

            # language (prefer per-file language, fall back to filters)
            lang = f.get("language") or lang_map.get(ext, "Unknown")
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

            # attach repo metadata if this file belongs to a git repo
            repo_meta = file_to_repo.get(filename)
            if repo_meta:
                repo_names.add(repo_meta.get("repo_name", ""))
                repo_roots.add(repo_meta.get("repo_root", ""))

                # authors is just a list of names
                for a in repo_meta.get("authors", []):
                    if a:
                        repo_authors.add(str(a))

                # contributors might be dicts with stats
                for c in repo_meta.get("contributors", []):
                    if isinstance(c, dict):
                        name = c.get("name")
                        if name:
                            repo_contributors.add(name)
                    elif c:
                        repo_contributors.add(str(c))

                bc = repo_meta.get("branch_count")
                if bc is not None:
                    branch_counts.append(bc)

                hm = repo_meta.get("has_merges")
                if hm is not None:
                    has_merges_flags.append(hm)

                pt = repo_meta.get("project_type")
                if pt:
                    project_types.append(pt)

                rd = repo_meta.get("duration_days")
                if rd is not None:
                    repo_duration_vals.append(rd)

                cf = repo_meta.get("commit_frequency")
                if cf:
                    commit_freqs.append(cf)

        # basic numbers
        total_files = len(clean_files)
        code_files = activity_counts["code"]
        test_files = activity_counts["test"]
        doc_files = activity_counts["documentation"]
        design_files = activity_counts["design"]

        # pick some "main" values from the aggregated repo info
        repo_name = next(iter(repo_names), proj_name)
        repo_root = next(iter(repo_roots), "")
        branch_count = max(branch_counts) if branch_counts else 0
        has_merges = (
            "Yes"
            if any(has_merges_flags)
            else "No"
            if has_merges_flags
            else "Unknown"
        )
        project_type = next(iter(project_types), "Unknown")
        repo_duration_days = (
            max(repo_duration_vals) if repo_duration_vals else duration_days
        )
        commit_frequency = next(iter(commit_freqs), "Unknown")

        # collab guess: .git present or multiple authors/contributors
        is_collab = (
            any(".git" in f["filename"] for f in files)
            or len(repo_authors) > 1
            or len(repo_contributors) > 1
        )

        # simple score for ranking (will make smarter in next update)
        score = total_files + duration_days + code_files * 2

        # print repo info to terminal
        if detailed_data:
            print_repo_summary(
                proj_name,
                repo_name,
                repo_root,
                repo_authors,
                repo_contributors,
                branch_count,
                has_merges,
                project_type,
                repo_duration_days,
                commit_frequency,
            )

        project_summaries.append(
            {
                "project": proj_name,
                "total_files": total_files,
                "duration_days": duration_days,
                "code_files": code_files,
                "test_files": test_files,
                "doc_files": doc_files,
                "design_files": design_files,
                "languages": ", ".join(sorted(langs)) if langs else "Unknown",
                "frameworks": ", ".join(sorted(frameworks)) if frameworks else "None",
                "skills": ", ".join(sorted(skills)) if skills else "None",
                "is_collaborative": "Yes" if is_collab else "No",
                # GIT / REPO FIELDS (for advanced mode & reports)
                "repo_name": repo_name,
                "repo_root": repo_root,
                "authors": ", ".join(sorted(repo_authors)) if repo_authors else "",
                "contributors": ", ".join(sorted(repo_contributors))
                if repo_contributors
                else "",
                "branch_count": branch_count,
                "has_merges": has_merges,
                "project_type": project_type,
                "repo_duration_days": repo_duration_days,
                "commit_frequency": commit_frequency,
                "score": score,
            }
        )

    # sort projects so biggest score first
    project_summaries.sort(key=lambda x: x["score"], reverse=True)

    # print summary table (just core stuff so it fits)
    print(
        f"\n{'Project':18} {'Files':>5} {'Days':>5} {'Code':>5} {'Test':>5} "
        f"{'Doc':>5} {'Des':>5}  {'Langs':18} {'Frameworks':18} {'Collab':>6} {'Score':>6}"
    )
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
                    "project",
                    "total_files",
                    "duration_days",
                    "code_files",
                    "test_files",
                    "doc_files",
                    "design_files",
                    "languages",
                    "frameworks",
                    "skills",
                    "is_collaborative",
                    "repo_name",
                    "repo_root",
                    "authors",
                    "contributors",
                    "branch_count",
                    "has_merges",
                    "project_type",
                    "repo_duration_days",
                    "commit_frequency",
                    "score",
                ],
            )
            writer.writeheader()
            writer.writerows(project_summaries)
        print(f"saved file to {out_path}")

    return project_summaries
