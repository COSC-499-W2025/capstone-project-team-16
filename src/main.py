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

# --------------------------------------------------------
# INITIALIZATION (runs once per app start)
# --------------------------------------------------------
def initialize_app():
    print("Welcome to Skill Scope!")
    print("~~~~~~~~~~~~~~~~~~~~~~~")

    conn = ""  # placeholder until DB implemented
    config = UserConfig()

    # A) Ensure consent exists
    if not config.consent:
        consent = get_user_consent()
        if not consent:
            exit()
        config.consent = True
        config.save_to_db(conn)

    return config, conn

# --------------------------------------------------------
# HOME SCREEN (loops until quit)
# --------------------------------------------------------
def home_screen(config, conn):
    while True:
        print("\n===== SKILL SCOPE HOME =====")
        print("1. Run a new scan")
        print("2. Scan Manager (view/manage previous scans)")
        print("3. Quit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            orchestrator(config, conn)

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
               " view_project_analyses()"
               "TODO: get way to view analyses"

            elif choice == "2":
                "view_resume_items()"
                "TODO: get way to view resume items"

            elif choice == "3":
                "delete_insights()"
                "TODO: get way to delete analyses"

            elif choice == "4":
                break

            else:
                print("Invalid input. Try again.")

# --------------------------------------------------------
# ORCHESTRATOR (handles running a scan)
# --------------------------------------------------------
def orchestrator(config, conn):
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
        config, conn = initialize_app()
        home_screen(config, conn)  # handles loop until quit
    except KeyboardInterrupt:
        print("\nGoodbye!")
