import sys

### Permission Manager for enforcing privacy rules

def get_yes_no(prompt: str) -> bool:
    """
    Prompts the user with a yes/no question.
    Returns True for 'Y', False for 'N'.
    """
    while True:
        choice = input(f"{prompt} (Y/N): ").strip().upper()
        if choice == "Y":
            return True
        elif choice == "N":
            return False
        else:
            print("Invalid input. Please enter Y or N.")


def get_user_consent() -> bool:
    """
    Prompts the user for consent to access personal data.
    Returns True if consent is granted, False otherwise.
    """
    consent_granted = get_yes_no(
        "Before proceeding, do you give consent to Skill Scope to access and view your personal data?"
    )
    
    if consent_granted:
        print("Consent granted.")
    else:
        print("Consent denied. Exiting now.")
    
    return consent_granted


def get_analysis_mode() -> str:
    """
    Prompts the user to choose an analysis mode.
    Returns "basic" or "advanced".
    """
    while True:
        print("\nSelect analysis mode:")
        print("1) Basic")
        print("2) Advanced")
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "basic"
        elif choice == "2":
            return "advanced"
        else:
            print("Invalid choice. Please enter 1 or 2.")


def get_advanced_options() -> dict:
    """
    Prompts the user for advanced analysis options.
    Returns a dictionary of boolean flags for each option.
    """
    print("\nAdvanced Analysis Options:")
    options = {}
    options["programming_scan"] = get_yes_no("Include programming scan?")
    options["framework_scan"] = get_yes_no("Include framework scan?")
    # Add more options here as needed
    return options