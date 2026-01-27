# this checks all the projects and tries to guess what kind of work it was
# (code, docs, design etc). also counts stuff, finds duration, langs, frameworks, skills

import json
import os
import shutil
from datetime import datetime
from analysis_utils import center_text, to_datetime
from classification import detect_activity, detect_framework, get_skill
from contributor_utils import apply_contributor_breakdown
from scoring_utils import compute_project_score

from collections import defaultdict, Counter
import csv
from resume_generator import build_project_line
from print_utils import (
    print_repo_summary,
    print_project_rankings,
    print_chronological_projects,
    print_skills_timeline,
    print_resume_summaries,
    print_contributor_stats,
)






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





# --------------------------------------------------------
# MAIN ANALYSIS FUNCTION
# --------------------------------------------------------
def analyze_projects(extracted_data, filters, advanced_options, detailed_data=None, write_csv=True ):
    if advanced_options is None:
    # default: everything ON
        advanced_options = {
            "programming_scan": True,
            "framework_scan": True,
            "skills_gen": True,
            "resume_gen": True
        }


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

    contributor_profiles = defaultdict(lambda: {
        "skills": set(),
        "projects": []
    })

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
        mod_times = [to_datetime(f["last_modified"]) for f in clean_files]
        first_mod = min(mod_times)
        last_mod = max(mod_times)
        duration_days = (last_mod - first_mod).days + 1
        

        # counters + sets
        activity_counts = Counter()
        langs = set()
        skills = set()


        # --- Extract frameworks from detailed_data only ---
        frameworks = set()
        if advanced_options.get("framework_scan", True) and detailed_data:
            project_meta = next(
                (p for p in detailed_data.get("projects", []) if p.get("repo_name") == proj_name),
                None,
            )
            if project_meta and "frameworks" in project_meta:
                # just take them as-is
                frameworks.update(project_meta["frameworks"])

        # if no frameworks detected, assign "NA"
        if not frameworks:
            frameworks.add("NA")




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
            act = detect_activity(category, filename)
            activity_counts[act] += 1

            # language (prefer per-file language, fall back to filters)
            lang = f.get("language") or lang_map.get(ext, "Unknown")

            if lang != "Unknown":
                langs.add(lang)




            if advanced_options.get("skills_gen", True):
                # skills
                s = get_skill(
                    ext=ext,
                    lang=lang,
                    skill_map=filters.get("skills"),
                    ext_map=filters.get("languages")
                )
                if s:
                    skills.add(s)

                    # track global usage for chronological skill list
                    file_time = to_datetime(f["last_modified"])
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

        # if no frameworks detected, assign "NA"
        if not frameworks:
            frameworks.add("NA")

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

        score = compute_project_score(
             volume_score=volume_score,
             activity_score=activity_score,
            variety_score=variety_score,
             duration_score=duration_score,
            collab_bonus=collab_bonus,
            branch_bonus=branch_bonus,
            merge_bonus=merge_bonus,
            commit_bonus=commit_bonus,
)

        project_meta = None
        if detailed_data:
            project_meta = next(
            (p for p in detailed_data.get("projects", [])
            if p.get("repo_name") == proj_name),
            None,
    )

    # ----------------------------------------------------
# Per-contributor breakdown
# ----------------------------------------------------
        per_contributor_scores, per_contributor_pct, per_contributor_skills = apply_contributor_breakdown(
            proj_name=proj_name,
            score=score,
            filters=filters,
            project_meta=project_meta,
            contributor_profiles=contributor_profiles,
            detect_activity=detect_activity,
            get_skill=get_skill,
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
                "frameworks": ", ".join(sorted(frameworks)),
                "skills": ", ".join(sorted(skills)) if skills else "NA",
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
                "per_contributor_scores": per_contributor_scores,
                "per_contributor_pct": per_contributor_pct,
                "per_contributor_skills": {k: sorted(list(v)) for k, v in per_contributor_skills.items()},

            }
        )

    


    # --------------------------------------------------------
    # OUTPUT PART 1: ranked project table
    # --------------------------------------------------------
    # sort projects so biggest score first
    project_summaries.sort(key=lambda x: x["score"], reverse=True)
    print_project_rankings(project_summaries)

    # --------------------------------------------------------
    # OUTPUT PART 2: chronological list of projects
    # --------------------------------------------------------
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
    print_chronological_projects(chronological_projects)

    # --------------------------------------------------------
    # OUTPUT PART 3: chronological list of skills exercised
    # --------------------------------------------------------
    
    skills_output = []
    if advanced_options.get("skills_gen", True):
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
        print_skills_timeline(skills_output)

    # --------------------------------------------------------
    # OUTPUT PART 4: resume style summaries of top projects
    # --------------------------------------------------------
    TOP_N = 3
    top_projects = project_summaries[:TOP_N]
    resume_summaries = []
    for p in top_projects:
        line = build_project_line(p)
        resume_summaries.append(line)
    print_resume_summaries(resume_summaries)
    

    # --------------------------------------------------------
    # OUTPUT PART 5: Per-Contributor Rankings (per person)
    # --------------------------------------------------------
    print_contributor_stats(project_summaries)
    



    # --------------------------------------------------------
    # CSV OUTPUT (we might not need this anymore since we have word doc now. can delete later. just here for now.)
    # --------------------------------------------------------
    if write_csv:
        from file_parser import OUTPUT_DIR
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(OUTPUT_DIR, "project_contribution_summary.csv")

        while True:
            try:
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
                            "per_contributor_scores",
                            "per_contributor_pct",
                            "per_contributor_skills",
                        ],
                    )
                    writer.writeheader()
                    writer.writerows(
                        [{k: v for k, v in p.items() if k in writer.fieldnames}
                            for p in project_summaries]
                    )

                print(center_text(f"saved file to {out_path}"))
                break
            except PermissionError:
                print()
                print(center_text(f"[!] Could not save CSV to '{out_path}' because it is open."))
                print(center_text("Please close the file and press Enter to retry, or type 'cancel' to skip."))
                if input("> ").strip().lower() == "cancel":
                    break
            except Exception as e:
                print()
                print(center_text(f"[WARN] Could not save CSV: {e}"))
                break



    # Serialize contributor profiles (sets to lists)
    final_contributor_profiles = {}
    for k, v in contributor_profiles.items():
        final_contributor_profiles[k] = {
            "skills": sorted(list(v["skills"])),
            "projects": v["projects"]
        }
    
    # --------------------------------------------------------
    # To make text and doc file from analysis
    # --------------------------------------------------------

    return {
    "project_summaries": project_summaries,
    "resume_summaries": resume_summaries,        # résumé-style top projects
    "skills_chronological": skills_output,      # skills exercised over time
    "projects_chronological": chronological_projects,  # projects in chronological order
    "contributor_profiles": final_contributor_profiles,
}
