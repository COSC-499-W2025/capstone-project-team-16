# this checks all the projects and tries to guess what kind of work it was
# (code, docs, design etc). also counts stuff, finds duration, langs, frameworks, skills

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import csv



# --------------------------------------------------------
# print for repo metadata
# --------------------------------------------------------
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
# for guessing project / dates / activity
# --------------------------------------------------------

# TODO: move to extractor. Possibly rework as the guessing can be improved
def _project_name(filename: str) -> str:
    """Guess project name from first folder component."""
    path = filename.replace("\\", "/")
    parts = [p for p in path.split("/") if p]  # drop empty from leading "/"
    if not parts:
        return "project"
    return parts[0]


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


# --------------------------------------------------------
# this is to build resume for a project
# --------------------------------------------------------
def _project_resume_summary(p: dict) -> str:
    """build a short sentence about a project."""
    name = p["project"]
    langs = p.get("languages", "Unknown")
    frameworks = p.get("frameworks", "None")
    duration = p.get("duration_days", 0)
    code_files = p.get("code_files", 0)
    test_files = p.get("test_files", 0)
    project_type = p.get("project_type", "software")

    pieces = []

    # main clause
    main = f"Contributed to a {project_type.lower()} project '{name}'"
    if langs and langs != "Unknown":
        main += f" using {langs}"
    pieces.append(main)

    # details
    details = []
    if code_files:
        details.append(f"{code_files} code files")
    if test_files:
        details.append(f"{test_files} test files")
    if duration:
        details.append(f"over {duration} days")

    if details:
        pieces.append("working on " + ", ".join(details))

    if frameworks and frameworks != "None":
        pieces.append(f"with frameworks such as {frameworks}")

    return "; ".join(pieces) + "."


# --------------------------------------------------------
# MAIN ANALYSIS FUNCTION
# --------------------------------------------------------
def analyze_projects(extracted_data, filters, detailed_data=None, write_csv=True):
   

    # not heavily used now, but keep in case we want ext->lang fallback later
    lang_map = filters.get("languages", {})

    # track global skill usage over time for chronological skills output
    skill_usage = {}  # skill -> {"first": datetime, "last": datetime, "count": int}

    # map each file path to its repo metadata (if advanced scan ran)
    file_to_repo = {}
    if isinstance(detailed_data, dict):
        for repo in detailed_data.get("projects", []):
            for f in repo.get("files", []):
                fname = f.get("filename")
                if fname:
                    file_to_repo[fname] = repo

    # group files by project prefer Git repo name (repo_name) when we have it, otherwise fall back to guessing from the path
    
    projects = defaultdict(list)

    for row in extracted_data:
        filename = row["filename"]

        # relative path inside the zip, if we stored it
        path_for_project = row.get("logical_path") or filename

        repo_meta = file_to_repo.get(filename)

        if repo_meta and repo_meta.get("repo_name"):
            proj = repo_meta["repo_name"]
        else:
            # basic mode or files not tied to a git repo
            proj = _project_name(path_for_project)

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

                # track global usage for chronological skill list
                file_time = _to_datetime(f["last_modified"])
                info = skill_usage.get(s)
                if info is None:
                    skill_usage[s] = {
                        "first": file_time,
                        "last": file_time,
                        "count": 1,
                    }
                else:
                    if file_time < info["first"]:
                        info["first"] = file_time
                    if file_time > info["last"]:
                        info["last"] = file_time
                    info["count"] += 1

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

        # collab guess: .git present OR multiple authors/contributors
        is_collab = (
            any(".git" in f["filename"] for f in files)
            or len(repo_authors) > 1
            or len(repo_contributors) > 1
        )

        # ----------------------------------------------------
        # "depth + variety" score for ranking projects
        # ----------------------------------------------------
        skills_count = len(skills)
        languages_count = len(langs)

        # size (capped so giant repos don't dominate everything)
        volume_score = min(total_files, 60) * 1.0

        # type of work
        activity_score = (
            code_files * 3
            + test_files * 2
            + doc_files * 1
            + design_files * 1
        )

        # variety of skills / languages
        variety_score = skills_count * 2 + languages_count * 1.5

        # duration (how long you worked on it)
        duration_score = min(duration_days, 90) * 0.5

        # collab / repo sophistication
        collab_bonus = 8 if is_collab else 0
        branch_bonus = min(branch_count, 5) * 1.5
        merge_bonus = 5 if has_merges == "Yes" else 0

        # small bonus for higher commit frequency if numeric ("ex. 15.6 commits/week")
        commit_bonus = 0
        try:
            num_commits = float(str(commit_frequency).split()[0])
            commit_bonus = min(num_commits, 30) * 0.2
        except Exception:
            pass

        score = (
            volume_score
            + activity_score
            + variety_score
            + duration_score
            + collab_bonus
            + branch_bonus
            + merge_bonus
            + commit_bonus
        )

        # print repo info to terminal in advanced mode
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
                # dates for chronological project list (NEW)
                "first_modified": first_mod,
                "last_modified": last_mod,
                # final score used for ranking (NEW)
                "score": score,
            }
        )

    # --------------------------------------------------------
    # OUTPUT PART 1: ranked project table
    # --------------------------------------------------------
    # sort projects so biggest score first
    project_summaries.sort(key=lambda x: x["score"], reverse=True)

    print(
    f"\n{'Project':30} "
    f"{'Files':>6} {'Days':>6} {'Code':>6} {'Test':>6} "
    f"{'Doc':>6} {'Des':>6} "
    f"{'Langs':25} {'Frameworks':25} "
    f"{'Collab':>7} {'Score':>7}"
)
    print("-" * 150)

    for p in project_summaries:
        print(
            f"{p['project'][:30]:30} "
            f"{p['total_files']:6} {p['duration_days']:6} {p['code_files']:6} "
            f"{p['test_files']:6} {p['doc_files']:6} {p['design_files']:6} "
            f"{p['languages'][:25]:25} {p['frameworks'][:25]:25} "
            f"{p['is_collaborative']:>7} {p['score']:7.1f}"
    )


    # --------------------------------------------------------
    # OUTPUT PART 2: chronological list of projects
    # --------------------------------------------------------
    print("\nProjects in chronological order (by first activity)")
    print("-" * 80)

    projects_chrono = sorted(
        project_summaries,
        key=lambda x: x["first_modified"],
    )

    chronological_projects = []
    for p in projects_chrono:
        first_date = p["first_modified"].date().isoformat()
        last_date = p["last_modified"].date().isoformat()
        chronological_projects.append(
            {
                "name": p["project"],
                "first_used": first_date,
                "last_used": last_date,
            }
        )
        print(
            f"- {p['project']}: {first_date} → {last_date} "
            f"({p['duration_days']} days, score {p['score']:.1f})"
        )

    # --------------------------------------------------------
    # OUTPUT PART 3: chronological list of skills exercised
    # --------------------------------------------------------
    print("\nSkills exercised over time")
    print("-" * 80)

    skills_chrono = sorted(
        (
            {
                "skill": skill,
                "first_used": info["first"],
                "last_used": info["last"],
                "count": info["count"],
            }
            for skill, info in skill_usage.items()
        ),
        key=lambda x: x["first_used"],
    )

    skills_output = []
    for row in skills_chrono:
        first_date = row["first_used"].date().isoformat()
        last_date = row["last_used"].date().isoformat()
        skills_output.append(
            {
                "skill": row["skill"],
                "first_used": first_date,
                "last_used": last_date,
            }
        )
        print(
            f"- {first_date} → {last_date}: {row['skill']} "
            f"(used in {row['count']} files)"
        )

    # --------------------------------------------------------
    # OUTPUT PART 4: resume style summaries of top projects
    # --------------------------------------------------------
    TOP_N = 3
    top_projects = project_summaries[:TOP_N]

    print(f"\nTop {TOP_N} projects (résumé-style summaries)")
    print("-" * 80)
    resume_summaries = []

    for p in top_projects:
        line = _project_resume_summary(p)
        resume_summaries.append(line)
        print(f"- {line}")

    # --------------------------------------------------------
    # CSV OUTPUT (need to change to a resume doc from csv)
    # --------------------------------------------------------
    if write_csv:
        os.makedirs("out", exist_ok=True)
        out_path = os.path.join("out", "project_contribution_summary.csv")

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
                    "first_modified",
                    "last_modified",
                    "score",
                ],
            )
            writer.writeheader()
            writer.writerows(project_summaries)

        print(f"saved file to {out_path}")

        # we still just return project_summaries so main.py doesn't break
    return {
    "project_summaries": project_summaries,
    "resume_summaries": resume_summaries,        # résumé-style top projects
    "skills_chronological": skills_output,      # skills exercised over time
    "projects_chronological": chronological_projects,  # projects in chronological order
}
