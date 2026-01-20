import sys
import shutil

### Permission Manager for enforcing privacy rules

def _center_text(text):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def _print_banner(title, line_char="~", min_width=23):
    line_width = max(len(title), min_width)
    line = line_char * line_width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))

def get_yes_no(prompt: str) -> bool:
    """
    Prompts the user with a yes/no question.
    Returns True for 'Y', False for 'N'.
    """
    while True:
        choice = input(_center_text(f"{prompt} (Y/N): ")).strip().upper()
        if choice == "Y":
            return True
        elif choice == "N":
            return False
        else:
            print(_center_text("Invalid input. Please enter Y or N."))


def get_user_consent() -> bool:
    """
    Prompts the user for consent to access personal data.
    Returns True if consent is granted, False otherwise.
    """
    consent_granted = get_yes_no(
        "Before proceeding, do you give consent to Skill Scope to access and view your personal data?"
    )
    
    if consent_granted:
        print(_center_text("Consent granted."))
    else:
        print(_center_text("Consent denied. Exiting now."))
    
    return consent_granted


def get_analysis_mode() -> str:
    """
    Prompts the user to choose an analysis mode.
    Returns "Basic", "Advanced", or None if the user goes back.
    """
    while True:
        _print_banner("ANALYSIS MODE")
        print(_center_text("0. Back"))
        print(_center_text("1. Basic (Does not open file content)"))
        print(_center_text("2. Advanced (Opens file content)"))
        choice = input(_center_text("Choose an option (0-2): ")).strip()
        if choice == "0":
            return None
        if choice == "1":
            return "Basic"
        elif choice == "2":
            return "Advanced"
        else:
            print(_center_text("Invalid choice. Please enter 0, 1, or 2."))


def get_advanced_options() -> dict:
    """
    Prompts the user for advanced analysis options.
    Returns a dictionary of boolean flags for each option.
    """
    _print_banner("ADVANCED OPTIONS")
    options = {}
    options["programming_scan"] = get_yes_no("Include programming analysis?")
    options["framework_scan"] = get_yes_no("Include framework detection?")
    options["skills_gen"] = get_yes_no("Generate skills used?")
    options["resume_gen"] = get_yes_no("Generate resume?")
    
    
    # Add more options here as needed
    return options
