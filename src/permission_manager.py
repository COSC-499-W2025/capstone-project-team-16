import sys
### Permission Manager for enforcing privacy rules

### Prompts user's consent
def get_user_consent():
    consent = ""

    while True:
        
        consent = input("Before proceeding, do you give consent to Skill Scope to access and view your personal data? (Y/N): ").strip().upper()
        if consent not in ["Y", "N"]:
            print("Please enter Y or N.")
        elif consent == "N":
            print("Consent denied.")
            print("Exiting now.")
            return False
        elif consent == "Y":
            print("Consent granted.")
            return True
    