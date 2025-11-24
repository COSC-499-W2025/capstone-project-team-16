from __future__ import annotations
import sys
from permission_manager import get_user_consent
from file_parser import get_input_file_path 
from metadata_extractor import base_extraction, detailed_extraction, load_filters  # <- Added load_filters
from alternative_analysis import analyze_projects
import database_manager  

print("Welcome to Skill Scope!")
print("~~~~~~~~~~~~~~~~~~~~~~~")

if get_user_consent():
    file_list = get_input_file_path()
else:
    sys.exit()

if file_list:
    # Load filters first
    filters = load_filters()
    
    # 1. Base Extraction
    scraped_data = base_extraction(file_list, filters)  # <- Added filters

    # 2. Detailed Extraction 
    detailed_data = detailed_extraction(scraped_data)  # <- Capture return value
    
    # 3. Analysis
    results = analyze_projects(scraped_data, filters, write_csv=True)  # <- Added filters
    
    # 4. Save to Database
    print("Saving to database...")
    database_manager.save_scan_results(results)