### Orchestrator for coordinating scan tasks

import shutil
import sys
import time

from user_config import UserConfig
from permission_manager import (
    get_user_consent,
    get_analysis_mode,
    get_advanced_options
)
from file_parser import get_input_file_path
from services.scan_service import analyze_scan, save_scan
from scan_manager import scan_manager

# --------------------------------------------------------
# CLI helpers
# --------------------------------------------------------
def _center_text(text):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def _animate_goodbye(text="Goodbye!", delay=0.03):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    padding = max((width - len(text)) // 2, 0)
    sys.stdout.write(" " * padding)
    sys.stdout.flush()
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def _print_banner(title, line_char="~", min_width=23):
    line_width = max(len(title), min_width)
    line = line_char * line_width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))


def _print_menu(title, options, prompt="Choose an option: "):
    _print_banner(title)
    for key, label in options:
        print(_center_text(f"{key}. {label}"))
    return input(_center_text(prompt)).strip()


# --------------------------------------------------------
# INITIALIZATION (runs once per app start)
# --------------------------------------------------------
def initialize_app():
    print()
    print(_center_text("~~~~~~~~~~~~~~~~~~~~~~~"))
    print(_center_text("Welcome to Skill Scope!"))
    print(_center_text("~~~~~~~~~~~~~~~~~~~~~~~"))
    print()
    intro_lines = [
        "Skill Scope scans a project folder to summarize languages, frameworks,",
        "timelines, and contributions, then saves the results for later review.",
        "",
        "1) Run a new scan: choose files and an analysis mode to generate a report.",
        "2) Scan Manager: view previous scans, generate resumes/portfolios, or delete scans.",
        "3) Quit: exit the program.",
    ]
    for line in intro_lines:
        print(_center_text(line))
    print()
    initial_choice = input(_center_text("Choose an option (1-3): ")).strip()

    # Load existing config if it exists
    config = UserConfig.load_from_db()
    if config is None:
        config = UserConfig()

    if initial_choice == "3":
        return config, initial_choice

    # Ensure consent exists
    if not config.consent:
        consent = get_user_consent()
        if not consent:
            exit()
        config.consent = True
        config.save_to_db()

    return config, initial_choice

# --------------------------------------------------------
# HOME SCREEN (loops until quit)
# --------------------------------------------------------
def home_screen(config, initial_choice=None):
    pending_choice = initial_choice
    while True:
        if pending_choice is None:
            choice = _print_menu(
                "SKILL SCOPE HOME",
                [
                    ("1", "Run a new scan: choose files and an analysis mode to generate a report."),
                    ("2", "Scan Manager: view previous scans, generate resumes/portfolios, or delete scans."),
                    ("3", "Quit: exit the program."),
                ],
                prompt="Choose an option (1-3): ",
            )
        else:
            choice = pending_choice
            pending_choice = None

        if choice == "1":
            orchestrator(config)

        elif choice == "2":
            scan_manager()

        elif choice == "3":
            _animate_goodbye()
            exit()

        else:
            print(_center_text("Invalid input. Try again."))

# --------------------------------------------------------
# ORCHESTRATOR (handles running a scan)
# --------------------------------------------------------
def orchestrator(config):
    _print_banner("NEW SCAN")

    # Step 1: Ask for analysis mode EACH TIME
    analysis_mode = get_analysis_mode()
    if analysis_mode is None:
        return
    analysis_mode_key = analysis_mode.lower()

    # Step 2: Advanced mode logic
    advanced_options = {}
    if analysis_mode_key == "advanced":
        advanced_options = get_advanced_options()

    # Step 3: Select project files
    file_list = get_input_file_path()
    if not file_list:
        print(_center_text("No files selected. Returning to home."))
        return

    # Step 4: Run analysis on the extracted metadata and save data to DB
    analysis_results = analyze_scan(file_list, analysis_mode, advanced_options)

    try:
        save_scan(analysis_results, analysis_mode, config.consent)
        print(_center_text("Scan successfully saved."))
    except Exception as e:
        print(_center_text(f"[WARN] Could not store project analysis: {e}"))

   


# --------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------
if __name__ == "__main__":
    try:
        config, initial_choice = initialize_app()
        home_screen(config, initial_choice=initial_choice)  # handles loop until quit
    except KeyboardInterrupt:
        print()
        _animate_goodbye()
