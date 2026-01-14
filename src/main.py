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
    from db import save_full_scan, list_full_scans, get_full_scan_by_id

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