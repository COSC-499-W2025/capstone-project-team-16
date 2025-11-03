### This will act as our orchestrator for coordinating scan tasks
from permission_manager import get_user_consent
from file_parser import get_input_file_path
from metadata_extractor import base_extraction

print("Welcome to Skill Scope!")
print("~~~~~~~~~~~~~~~~~~~~~~~")

if (get_user_consent()):
    file_list = get_input_file_path()
else:
    exit()

if file_list:
    #call metadata extractor and pass file_path
    #should get a list of files with accompanying metadata.
    scraped_data = base_extraction(file_list)
    



