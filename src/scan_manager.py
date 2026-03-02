import os
import shutil
from datetime import datetime

from db import delete_full_scan_by_id, get_full_scan_by_id, list_full_scans, update_full_scan
from file_parser import get_input_file_path
from permission_manager import get_yes_no
from resume_generator import generate_resume, generate_contributor_portfolio, edit_contributor_descriptions
from portfolio_generator import manage_portfolio_showcase, generate_and_save_portfolio
from services.scan_service import analyze_scan, merge_scans
from datetime import datetime


from print_utils import (
    print_repo_summary,
    print_project_rankings,
    print_chronological_projects,
    print_skills_timeline,
    print_resume_summaries,
    print_contributor_stats,
    is_noise,
    print_scan_list,
    format_timestamp
)


# --------------------------------------------------------
# MAIN SCAN MANAGER
# --------------------------------------------------------

def scan_manager():
    """
    Provides a loop for viewing, generating portfolios, and deleting past scans.
    Provides a loop for viewing, generating portfolios, and deleting past scans.

    """
    while True:
        choice = _print_menu(
            "SCAN MANAGER",
            [
                ("0", "Return to home screen"),
                ("1", "View stored project analyses"),
                ("2", "Update an existing scan"),
                ("3", "Generate Resume/Portfolio"),
                ("4", "Delete stored scans"),
                ("5", "Customize (ranking/chronology/skills/showcase)")
            ],
            prompt="Choose an option (0–5): ",
        )

        if choice == "1":
            view_full_scan_details()
        elif choice == "2":
            update_scan_workflow()
        elif choice == "3":
            generate_portfolio_menu()
        elif choice == "4":
            delete_full_scan()
        elif choice == "5":
            customize_scan_output()
        elif choice == "0":
            break
        else:
            print(_center_text("Invalid input. Try again."))


# --------------------------------------------------------
# VIEW SCAN DETAILS
# --------------------------------------------------------

"""
    Lists all saved scans, allows the user to select one, and prints a detailed report.
    The report includes project rankings, timelines, skills, and contributor stats.
"""

def view_full_scan_details():
    scans = list_full_scans()
    if not scans:
        print(_center_text("No scans found."))
        return

    # 1. List available scans (lightweight metadata only)
    print()
    print(_center_text("Select a scan to view:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        print(_center_text("Canceled."))
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print(_center_text("Invalid selection."))
        return

    # 2. Fetch the full heavy JSON data for the selected scan
    scan = get_full_scan_by_id(scans[idx]["summary_id"])
    if not scan:
        print(_center_text("Error: Could not retrieve scan data."))
        return

    data = scan["scan_data"]
    _apply_customizations_to_project_summaries(data)

        # Extract specific sections from the JSON blob

    project_summaries = data.get("project_summaries", [])
    resume_summaries = data.get("resume_summaries", [])
    skills_chronological = data.get("skills_chronological", [])
    projects_chronological = data.get("projects_chronological", [])

    # 3. Display the report sections using helper functions
    _print_header("FULL SCAN DETAILS")
    print(f"Timestamp: {format_timestamp(scan['timestamp'])}")
    print(f"Mode: {scan['analysis_mode']}")
    print("=" * 28)

        # Print various sections of the report

    print_project_rankings(project_summaries)

    projects_chronological = []
    for p in project_summaries:
    # first_modified / last_modified might be datetime or string 
        first = str(p.get("first_modified", ""))[:10]
        last = str(p.get("last_modified", ""))[:10]
        projects_chronological.append({"name": p.get("project", "Unknown"), "first_used": first, "last_used": last})

    projects_chronological.sort(key=lambda x: x["first_used"])

    print_chronological_projects(projects_chronological)
    print_skills_timeline(skills_chronological)
    print_resume_summaries(resume_summaries)
    print_contributor_stats(project_summaries)

    print(_center_text("\nEnd of scan view.\n"))

        # Option to export the displayed report to a text file

    if get_yes_no("Export this report to a text file?"):
        from file_parser import OUTPUT_DIR
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        filename = f"scan_report_{scan['timestamp'].replace(':', '-')}.txt"
        path = os.path.join(OUTPUT_DIR, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                print(f"Scan Report — {format_timestamp(scan['timestamp'])}", file=f)
                print("=" * 60, file=f)
                print_project_rankings(project_summaries, file=f)
                print_chronological_projects(projects_chronological, file=f)
                print_skills_timeline(skills_chronological, file=f)
                print_resume_summaries(resume_summaries, file=f)
                print_contributor_stats(project_summaries, file=f)

            print(_center_text(f"Saved to: {path}"))
        except Exception as e:
            print(f"Error saving report: {e}")


# --------------------------------------------------------
# UPDATE SCAN
# --------------------------------------------------------

def update_scan_workflow():
    _print_header("UPDATE EXISTING SCAN")
    
    # 1. Select existing scan
    scans = list_full_scans()
    if not scans:
        print(_center_text("No existing scans found to update."))
        return

    print(_center_text("Select a scan to update:"))
    print_scan_list(scans)
    
    choice = input(_center_text(f"Choose (1-{len(scans)} or 0 to cancel): ")).strip()
    if not choice.isdigit():
        return
    idx = int(choice)
    if idx == 0 or idx > len(scans):
        return
    
    target_scan_meta = scans[idx-1]
    summary_id = target_scan_meta['summary_id']
    
    # Load full data
    existing_record = get_full_scan_by_id(summary_id)
    if not existing_record:
        print(_center_text("Error loading scan data."))
        return
    
    existing_data = existing_record['scan_data']

    # 2. Select new file
    print(_center_text("Select the new ZIP file to add:"))
    result = get_input_file_path()
    if not result:
        return
    file_list, zip_hash = result
    
    # Check if this file is already in the scan
    current_hashes = set(existing_data.get("source_hashes", []))
        
    if zip_hash in current_hashes:
        print(_center_text("This file has already been added to this scan."))
        return

    # 3. Analyze
    print(_center_text("Analyzing new files..."))
    analysis_mode = existing_record['analysis_mode']
    # Use default advanced options (empty dict defaults to True in detailed_extraction)
    new_results = analyze_scan(file_list, analysis_mode, {})
    if new_results:
        new_results["source_hashes"] = [zip_hash]
    
    # 4. Merge
    merged_results = merge_scans(existing_data, new_results)
    
    # 5. Save
    try:
        update_full_scan(summary_id, merged_results)
        print(_center_text("Portfolio updated successfully."))
    except Exception as e:
        print(_center_text(f"Error updating portfolio: {e}"))

# --------------------------------------------------------
# DELETE SCAN
# --------------------------------------------------------
"""
    Lists all saved scans and allows the user to permanently delete one from the database.
"""

def delete_full_scan():
    scans = list_full_scans()
    if not scans:
        print(_center_text("No saved scans found to delete."))
        return
        
    # Display list for deletion

    print()
    print(_center_text("Select a scan to delete:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        print(_center_text("Deletion canceled."))
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print(_center_text("Invalid selection."))
        return

    scan = scans[idx]

    # Confirm before deletion

    if get_yes_no(f"Are you sure you want to delete the scan from {scan['timestamp']}?"):
        success = delete_full_scan_by_id(scan["summary_id"])
        print(_center_text("Scan deleted.") if success else "Failed to delete scan.")
    else:
        print(_center_text("Deletion canceled."))


# PORTFOLIO GENERATION
# --------------------------------------------------------


def generate_portfolio_menu():
    """
    Menu for generating Word documents from a saved scan.
    Options:
    1) Full Project Resume (summary of all projects in the scan).
    2) Individual Contributor Resume (Word)
    3) Individual Contributor Portfolio (Markdown)specific to one person).
    """
    scans = list_full_scans()
    if not scans:
        print(_center_text("No scans found."))
        return

    # Select scan first

    print()
    print(_center_text("Select a scan to generate portfolio from:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print(_center_text("Invalid selection."))
        return

    # Fetch full data to access contributor profiles and project details

    scan = get_full_scan_by_id(scans[idx]["summary_id"])
    data = scan["scan_data"]
    _apply_customizations_to_project_summaries(data)

    while True:
        _print_header("GENERATION OPTIONS", width=48, sep="-")
        print(_center_text("1) Full Project Resume"))
        print(_center_text("2) Contributor Resume (Word)"))
        print(_center_text("3) Contributor Portfolio (Markdown)"))
        print(_center_text("4) Edit Resume"))
        print(_center_text("5) Edit Portfolio"))
        print(_center_text("0) Back"))

        choice = input(_center_text("Enter number: ")).strip()

        if choice == "0":
            break

        if choice == "1":
            docx = generate_resume(
                data.get("project_summaries", []),
                data.get("projects_chronological", []),
                data.get("skills_chronological", []),
                scan_timestamp=scan["timestamp"],
            )
            if docx:
                print(_center_text(f"Saved:\n{docx}"))
            input(_center_text("Press Enter to continue..."))
            continue

        if choice == "4":
            edit_contributor_descriptions(target_scan=scan)
            continue

        if choice == "5":
            manage_portfolio_showcase(target_scan=scan)
            continue

        if choice not in ("2", "3"):
            continue

        # --- Contributor Portfolio Logic ---

        contributors = [
            c for c in sorted(data.get("contributor_profiles", {}).keys())
            if not is_noise(c)
        ]

        if not contributors:
            print(_center_text("No valid contributors found."))
            continue

        print()
        print(_center_text("Select contributor:"))
        for i, c in enumerate(contributors, 1):
            print(_center_text(f"{i}. {c}"))

        sel = input(_center_text("Enter number (0 to back): ")).strip()
        if not sel.isdigit():
            continue

        idx = int(sel) - 1
        if idx < 0 or idx >= len(contributors):
            continue

        user = contributors[idx]
        profile = data["contributor_profiles"][user]
        
        if choice == "3":
            out = generate_and_save_portfolio(data, user, use_custom_fields=True)
            if out:
                print(_center_text(f"Saved portfolio to:\n{out}"))
            else:
                print(_center_text("Error: Could not generate portfolio for selected user."))
        elif choice == "2":
            # Default to chronological sorting
            sort_mode = "date"

            project_map = {p["project"]: p for p in data.get("project_summaries", [])}
            out = generate_contributor_portfolio(
                user,
                profile,
                project_map,
                scan_timestamp=None,
                sort_mode=sort_mode
            )

            if out:
                print(_center_text(f"Saved resume to:\n{out}"))
        
        input(_center_text("Press Enter to continue..."))


# --------------------------------------------------------
# UI HELPERS
# --------------------------------------------------------

def _center_text(text):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text)) // 2
    return " " * padding + text


def _print_header(title, width=28, sep="="):
    print()
    print(_center_text(sep * width))
    print(_center_text(title))
    print(_center_text(sep * width))


def _print_menu(title, options, prompt="Choose an option: "):
    print()
    print(_center_text(title))
    print(_center_text("=" * len(title)))
    for key, label in options:
        print(_center_text(f"{key}) {label}"))
    return input(_center_text(prompt)).strip()


def _print_scan_list(scans):
    for i, s in enumerate(scans, start=1):
        ts = format_timestamp(s['timestamp'])
        print(
            _center_text(
                f"{i}. Scan {s['summary_id']} - {ts} ({s['analysis_mode']})"
            )
        )

def _apply_customizations_to_project_summaries(data: dict) -> None:
    """
    Applies saved user choices (ranking, chronology corrections, highlighted skills,
    showcase selection, comparison attributes) to the project_summaries list
    b4 printing / generating.
    """
    custom = data.get("project_customizations") or {}
    projects = data.get("project_summaries") or []

    for p in projects:
        pname = p.get("project")
        if not pname:
            continue
        c = custom.get(pname) or {}

        # 1) Re-ranking
        if isinstance(c.get("ranking"), int):
            p["_custom_rank"] = c["ranking"]

        # 2) Chronology correction (override first/last)
        chrono = c.get("chronology_correction")
        if isinstance(chrono, dict):
            if chrono.get("first_used"):
                p["first_modified"] = chrono["first_used"]
            if chrono.get("last_used"):
                p["last_modified"] = chrono["last_used"]

        # 3) Comparison attributes (just store on project)
        if isinstance(c.get("comparison_attributes"), dict):
            p["comparison_attributes"] = c["comparison_attributes"]

        # 4) Skills to highlight
        if isinstance(c.get("highlighted_skills"), list):
            p["highlighted_skills"] = c["highlighted_skills"]

        # 5) Selected for showcase
        if isinstance(c.get("selected_for_showcase"), bool):
            p["selected_for_showcase"] = c["selected_for_showcase"]

# Also update the separate chronological list if it exists
    chrono_list = data.get("projects_chronological") or []
    if chrono_list:
        by_name = {e.get("name") or e.get("project"): e for e in chrono_list if isinstance(e, dict)}
        for p in projects:
            name = p.get("project")
            if not name or name not in by_name:
                continue
            entry = by_name[name]
            if p.get("first_modified"):
                entry["first_used"] = str(p["first_modified"])[:10]
            if p.get("last_modified"):
                entry["last_used"] = str(p["last_modified"])[:10]
        data["projects_chronological"] = chrono_list

    # Sort project_summaries: custom rank first, otherwise by score
    def sort_key(p):
        if isinstance(p.get("_custom_rank"), int):
            return (0, p["_custom_rank"])
        return (1, -(p.get("score") or 0))

    data["project_summaries"] = sorted(projects, key=sort_key)


def _is_valid_date_yyyy_mm_dd(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except Exception:
        return False


def _prompt_date(label: str) -> str:
    """Prompt until blank or valid YYYY-MM-DD."""
    while True:
        s = input(_center_text(f"{label} (YYYY-MM-DD, blank to skip): ")).strip()
        if not s:
            return ""
        if _is_valid_date_yyyy_mm_dd(s):
            return s
        print(_center_text("Invalid date. Please use YYYY-MM-DD (example: 2026-02-25)."))

def customize_scan_output():
    scans = list_full_scans()
    if not scans:
        print(_center_text("No scans found."))
        return

    print()
    print(_center_text("Select a scan to customize:"))
    _print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print(_center_text("Invalid selection."))
        return

    scan = get_full_scan_by_id(scans[idx]["summary_id"])
    if not scan:
        print(_center_text("Could not load scan."))
        return

    summary_id = scan["summary_id"]
    data = scan["scan_data"]
    data.setdefault("project_customizations", {})
    projects = data.get("project_summaries", []) or []

    if not projects:
        print(_center_text("No projects in this scan."))
        return

    while True:
        _print_header("EDIT STORED SCAN (CUSTOMIZE OUTPUT)", width=56, sep="=")
        print(_center_text("Edits are saved to this scan and used in reports / portfolio generation."))
        print(_center_text("1) Set project ranking (re-order)"))
        print(_center_text("2) Correct chronology (first/last date)"))
        print(_center_text("3) Set project tags/attributes (for comparison)"))
        print(_center_text("4) Pick skills to highlight"))
        print(_center_text("5) Mark project for showcase"))
        print(_center_text("0) Save + Exit"))

        action = input(_center_text("Choose: ")).strip()
        if action == "0":
            break
        if action not in {"1", "2", "3", "4", "5"}:
            continue

        print()
        for i, p in enumerate(projects, 1):
            print(_center_text(f"{i}. {p.get('project', f'Project {i}')}"))
        psel = input(_center_text("Pick project number (0 to back): ")).strip()
        if not psel.isdigit() or int(psel) == 0:
            continue

        pidx = int(psel) - 1
        if pidx < 0 or pidx >= len(projects):
            continue

        proj = projects[pidx]
        pname = proj.get("project", f"Project {pidx+1}")
        pc = data["project_customizations"].setdefault(pname, {})

        if action == "1":
    # Re-order projects against each other (1st, 2nd, 3rd...)
            custom = data.get("project_customizations") or {}
            names = [p.get("project", f"Project {i+1}") for i, p in enumerate(projects)]

            ranked = []
            for name in names:
                r = (custom.get(name) or {}).get("ranking")
                ranked.append((name, r))

    # If any ranks exist, sort by them (smaller = higher priority)
            if any(isinstance(r, int) for _, r in ranked):
                ranked.sort(key=lambda x: (x[1] if isinstance(x[1], int) else 10**9))
                ordered_names = [n for n, _ in ranked]
            else:
                ordered_names = names[:]

            print()
            print(_center_text("Current project order (1 = highest priority):"))
            for i, n in enumerate(ordered_names, 1):
                print(_center_text(f"{i}. {n}"))

            move_raw = input(_center_text("Pick project to move (0 to back): ")).strip()
            if not move_raw.isdigit() or int(move_raw) == 0:
                continue
            move_i = int(move_raw) - 1
            if move_i < 0 or move_i >= len(ordered_names):
                continue

            pos_raw = input(_center_text(f"New position (1-{len(ordered_names)}): ")).strip()
            if not pos_raw.isdigit():
                continue
            new_pos = int(pos_raw)
            if new_pos < 1 or new_pos > len(ordered_names):
                continue

            picked_name = ordered_names.pop(move_i)
            ordered_names.insert(new_pos - 1, picked_name)

    # Save back as unique ranks for ALL projects
            for i, n in enumerate(ordered_names, 1):
                data["project_customizations"].setdefault(n, {})["ranking"] = i

            print(_center_text("Saved new ranking order."))

            print()
            print(_center_text("Updated project order:"))
            for i, n in enumerate(ordered_names, 1):
                print(_center_text(f"{i}. {n}"))
            input(_center_text("Press Enter to continue..."))

        elif action == "2":
            pc.setdefault("chronology_correction", {})
            first = _prompt_date("First used")
            last = _prompt_date("Last used")
            if first:
                pc["chronology_correction"]["first_used"] = first
            if last:
                pc["chronology_correction"]["last_used"] = last

        elif action == "3":
            print()
            print(_center_text("Add short tags/attributes so the portfolio can show a quick comparison."))
            print(_center_text("Use key=value pairs (role=backend, difficulty=high, focus=DB)."))

            raw = input(_center_text(
                "Enter tags as key=value (comma-separated). Example: audience=recruiter, focus=backend (blank clears): "
            )).strip()

            attrs = {}
            for part in raw.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k:
                        attrs[k] = v

            pc["comparison_attributes"] = attrs if raw else {}

        elif action == "4":
            skills = proj.get("skills") or []

            # If skills is a string like "Python, SQL, ..."
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",") if s.strip()]

            # If skills is something else unexpected, fallback
            if not isinstance(skills, list):
                skills = []
            if not skills:
                print(_center_text("No detected skills for this project."))
                input(_center_text("Press Enter..."))
                continue
            print(_center_text("Detected skills:"))
            for i, s in enumerate(skills, 1):
                print(_center_text(f"{i}. {s}"))
            raw = input(_center_text("Pick numbers (ex: 1 3 5): ")).strip()
            picked = []
            for tok in raw.split():
                if tok.isdigit():
                    si = int(tok) - 1
                    if 0 <= si < len(skills):
                        picked.append(skills[si])
            pc["highlighted_skills"] = picked
            

        elif action == "5":
            pc["selected_for_showcase"] = get_yes_no("Select this project for showcase?")

    update_full_scan(summary_id, data)
    print(_center_text("Saved customization choices."))
