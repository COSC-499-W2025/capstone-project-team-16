### This will act as our orchestrator for coordinating scan tasks

access = False
consent = ""

print("Welcome to Skill Scope!")
print("~~~~~~~~~~~~~~~~~~~~~~~")


### Prompts user's consent
while access == False:
    
    consent = input("Before proceeding, do you give consent to Skill Scope to access and view your personal data? (Y/N): ").strip().upper()

    print(consent)
    if consent not in ["Y", "N"]:
        print("Please enter Y or N.")
    elif consent == "N":
        print("Consent denied.")
        print("Exiting now.")
        break
    elif consent == "Y":
        print("Consent granted.")
        access = True
