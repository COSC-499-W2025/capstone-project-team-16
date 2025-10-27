### This will act as our orchestrator for coordinating scan tasks
from permission_manager import get_user_consent
from file_parser import get_input_file_path

print("Welcome to Skill Scope!")
print("~~~~~~~~~~~~~~~~~~~~~~~")

if (get_user_consent()):
    get_input_file_path()


