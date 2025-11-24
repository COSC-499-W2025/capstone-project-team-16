
from __future__ import annotations
import sys
from permission_manager import get_user_consent
from file_parser import get_input_file_path 
from metadata_extractor import base_extraction, detailed_extraction
from alternative_analysis import analyze_projects
import database_manager  

print("Welcome to Skill Scope!")
print("~~~~~~~~~~~~~~~~~~~~~~~")

if (get_user_consent()):
    file_list = get_input_file_path()
else:
    sys.exit()

if file_list:
    # 1. Base Extraction
    scraped_data = base_extraction(file_list)

    # 2. Detailed Extraction (Modifies in-place)
    detailed_extraction(scraped_data)
    
    # 3. Analysis
    # Capture the return value so to save it
    # Pass write_csv=True to maintain existing functionality
    results = analyze_projects(scraped_data, write_csv=True)

    # 4. Save to Database
    print("Saving to database...")
    database_manager.save_scan_results(results)