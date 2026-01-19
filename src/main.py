### Orchestrator for coordinating scan tasks

from user_config import UserConfig
from permission_manager import (
    get_user_consent,
    get_analysis_mode,
    get_advanced_options
)
from file_parser import get_input_file_path
from metadata_extractor import base_extraction, detailed_extraction, load_filters
from alternative_analysis import analyze_projects
from scan_manager import scan_manager
import db 
import sqlite3

# --------------------------------------------------------
# CLI helpers
# --------------------------------------------------------
def _print_menu(title, options, prompt="Choose an option: "):
    print(f"\n{title}")
    for key, label in options:
        print(f"{key}. {label}")
    return input(prompt).strip()

def _prompt_number(prompt):
    return input(prompt).strip()


def _print_section(title, width=28, sep="="):
    line = sep * width
    print(f"\n{line}\n {title}\n{line}\n")


def _truncate(text, max_len):
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# --------------------------------------------------------
# INITIALIZATION (runs once per app start)
# --------------------------------------------------------
def initialize_app():
    print("Welcome to Skill Scope!")
    print("~~~~~~~~~~~~~~~~~~~~~~~")

    # Load existing config if it exists
    config = UserConfig.load_from_db()
    if config is None:
        config = UserConfig()

    # Ensure consent exists
    if not config.consent:
        consent = get_user_consent()
        if not consent:
            exit()
        config.consent = True
        config.save_to_db()

    return config

# --------------------------------------------------------
# HOME SCREEN (loops until quit)
# --------------------------------------------------------
def home_screen(config):
    while True:
        choice = _print_menu(
            "===== SKILL SCOPE HOME =====",
            [
                ("1", "Run a new scan"),
                ("2", "Scan Manager (view/manage previous scans)"),
                ("3", "Quit"),
            ],
        )

        if choice == "1":
            orchestrator(config)

        elif choice == "2":
            scan_manager()

        elif choice == "3":
            print("Goodbye!")
            exit()

        else:
            print("Invalid input. Try again.")

# --------------------------------------------------------
# SCAN MANAGER (View + future management actions)
# --------------------------------------------------------
def scan_manager():
    while True:
        choice = _print_menu(
            "===== SCAN MANAGER =====",
            [
                ("1", "View stored project analyses"),
                ("2", "Delete stored scans"),
                ("3", "Return to home screen"),
            ],
        )

        if choice == "1":
            view_full_scan_details()

        elif choice == "2":
            delete_full_scan()

        elif choice == "3":
            break

        else:
            print("Invalid input. Try again.")

# ----------------------
# Scan Manager helpers
# ----------------------

def view_full_scan_details():
    from db import list_full_scans, get_all_full_scans
    import json

    scans = list_full_scans()
    if not scans:
        print("No scans found.")
        return

    print("Select a scan to view:")
    for i, s in enumerate(scans, start=1):
        print(f"{i}. {s['timestamp']} ({s['analysis_mode']})")

    choice = _prompt_number("Enter number (0 to return): ")
    if not choice.isdigit() or int(choice) == 0:
        print("Return to Scan Manager.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print("Invalid selection.")
        return

    scan = get_all_full_scans()[idx]
    data = scan["project_summaries_json"]

    project_summaries = data.get("project_summaries", [])
    resume_summaries = data.get("resume_summaries", [])
    skills_chronological = data.get("skills_chronological", [])
    projects_chronological = data.get("projects_chronological", [])

    _print_section("FULL SCAN DETAILS")
    print(f"Timestamp: {scan['timestamp']}")
    print(f"Mode: {scan['analysis_mode']}")

    _print_section("SUMMARY", width=12, sep="-")
    print(f"Projects analyzed: {len(project_summaries)}")
    print(f"Chronological projects: {len(projects_chronological)}")
    print(f"Skills tracked: {len(skills_chronological)}")
    print(f"Resume bullets: {len(resume_summaries)}")

    # -------------------------
    # 1. Ranked Project Table
    # -------------------------
    if project_summaries:
        _print_section("RANKED PROJECTS", width=18, sep="-")
        print(
            f"\n{'Project':<30} "
            f"{'Files':>6} {'Days':>6} {'Code':>6} {'Test':>6} "
            f"{'Doc':>6} {'Des':>6} "
            f"{'Languages':<25} {'Frameworks':<40} "
            f"{'Collab':>7} {'Score':>7}"
        )
        print("-" * 155)

        for p in project_summaries:
            # Truncate long language/framework lists for display
            langs_str = _truncate(p.get("languages", ""), 25)
            fw_str = _truncate(p.get("frameworks", ""), 40)

            print(
                f"{p.get('project', 'Unknown')[:30]:<30} "
                f"{p.get('total_files', 0):6} {p.get('duration_days', 0):6} {p.get('code_files', 0):6} "
                f"{p.get('test_files', 0):6} {p.get('doc_files', 0):6} {p.get('design_files', 0):6} "
                f"{langs_str:<25} {fw_str:<40} "
                f"{p.get('is_collaborative', 'No'):>7} {p.get('score', 0):7.1f}"
            )


    # -------------------------
    # 2. Chronological Projects
    # -------------------------
    if projects_chronological:
        _print_section("PROJECTS IN CHRONOLOGICAL ORDER", width=34, sep="-")
        for p in projects_chronological:
            print(
                f"- {p['name']}: {p['first_used']} → {p['last_used']}"
            )

    # -------------------------
    # 3. Skills Over Time
    # -------------------------
    if skills_chronological:
        _print_section("SKILLS EXERCISED OVER TIME", width=29, sep="-")
        for s in skills_chronological:
            print(
                f"- {s['first_used']} → {s['last_used']}: {s['skill']}"
            )

    # -------------------------
    # 4. Resume Summaries
    # -------------------------
    if resume_summaries:
        _print_section("TOP PROJECT RESUME SUMMARIES", width=30, sep="-")
        for bullet in resume_summaries:
            print(f"- {bullet}")

    print("\nEnd of scan.\n")



def delete_full_scan():
    from db import list_full_scans, delete_full_scan_by_id
    from permission_manager import get_yes_no

    scans = list_full_scans()
    if not scans:
        print("No saved scans found to delete.")
        return

    print("\nSelect a scan to delete:")
    for i, s in enumerate(scans, start=1):
        print(f"{i}. [{s['timestamp']}]  Mode: {s['analysis_mode']}")

    choice = _prompt_number("Enter number (0 to return): ")
    if not choice.isdigit() or int(choice) == 0:
        print("Return to Scan Manager.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print("Invalid selection.")
        return

    scan = scans[idx]

    if get_yes_no(f"Are you sure you want to delete the scan from {scan['timestamp']}?"):
        success = delete_full_scan_by_id(scan["summary_id"])
        print("Scan deleted." if success else "Failed to delete scan.")
    else:
        print("Deletion canceled.")


# --------------------------------------------------------
# ORCHESTRATOR (handles running a scan)
# --------------------------------------------------------
def orchestrator(config):
    print("\n=== New Scan ===")

    # Step 1: Ask for analysis mode EACH TIME
    analysis_mode = get_analysis_mode()

    # Step 2: Advanced mode logic
    advanced_options = {}
    if analysis_mode == "advanced":
        advanced_options = get_advanced_options()

    # Step 3: Select project files
    file_list = get_input_file_path()
    if not file_list:
        print("No files selected. Returning to home.")
        return

    # Step 4: Load filters and extract metadata
    filters = load_filters()
    scraped_data = base_extraction(file_list, filters)

    detailed_data = None
    if analysis_mode == "advanced":
        detailed_data = detailed_extraction(scraped_data, advanced_options, filters)

    # Step 5: Run analysis on the extracted metadata and save data to DB
    from db import save_full_scan  

    analysis_results = analyze_projects(scraped_data, filters, advanced_options, detailed_data)

    try:
        save_full_scan(analysis_results, analysis_mode, config.consent)
        print("Scan successfully saved.")
    except Exception as e:
        print(f"[WARN] Could not store project analysis: {e}")

   


# --------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------
if __name__ == "__main__":
    try:
        config = initialize_app()
        home_screen(config)  # handles loop until quit
    except KeyboardInterrupt:
        print("\nGoodbye!")
