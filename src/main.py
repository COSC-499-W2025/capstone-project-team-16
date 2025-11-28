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
import db 
import sqlite3

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
        print("\n===== SKILL SCOPE HOME =====")
        print("1. Run a new scan")
        print("2. Scan Manager (view/manage previous scans)")
        print("3. Quit")

        choice = input("Choose an option: ").strip()

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
        print("\n===== SCAN MANAGER =====")
        print("1. View stored project analyses (portfolio)")
        print("2. View stored résumé items")
        print("3. Delete stored insights")
        print("4. Return to home screen")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_project_analyses()

        elif choice == "2":
            view_resume_items()

        elif choice == "3":
            delete_insights()

        elif choice == "4":
            break

        else:
            print("Invalid input. Try again.")

# ----------------------
# Scan Manager helpers
# ----------------------

def view_project_analyses():
    from db import get_all_summaries
    summaries = get_all_summaries()
    if not summaries:
        print("No project analyses found.")
        return

    for s in summaries:
        print(f"- {s['project_name']} (Score: {s['score']}, Files: {s['total_files']}, Date: {s['scan_date']})")


def view_resume_items():
    from db import get_resume_bullets
    bullets = get_resume_bullets()
    if not bullets:
        print("No résumé items found.")
        return

    for b in bullets:
        print(f"- {b['project_name']}: {b['bullet']}")


def delete_insights():
    from db import list_project_summaries, delete_project_insights

    summaries = list_project_summaries()
    if not summaries:
        print("No project analyses found to delete.")
        return

    print("Select a project to delete insights for:")
    for i, s in enumerate(summaries, start=1):
        print(f"{i}. {s['project_name']}")

    choice = input("Enter number (or 0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        print("Deletion canceled.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(summaries):
        print("Invalid selection.")
        return

    project_id = summaries[idx]["project_id"]
    confirmed = input(f"Are you sure you want to delete insights for '{summaries[idx]['project_name']}'? (y/n): ").strip().lower()
    if confirmed == "y":
        success = delete_project_insights(project_id)
        if success:
            print("Insights deleted.")
        else:
            print("Failed to delete insights.")
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

    # Step 4: Extract metadata
    filters = load_filters()
    scraped_data = base_extraction(file_list, filters)

    detailed_data = None
    if analysis_mode == "advanced":
        "TODO: pass advanced parameters for scanning"
        detailed_data = detailed_extraction(scraped_data)

    # Step 5: Run analysis on the extracted metadata
    analyze_projects(scraped_data, filters)

    print("\nReturning to home screen...\n")

   


# --------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------
if __name__ == "__main__":
    try:
        config = initialize_app()
        home_screen(config)  # handles loop until quit
    except KeyboardInterrupt:
        print("\nGoodbye!")
