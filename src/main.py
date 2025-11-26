### Orchestrator for coordinating scan tasks

import sqlite3
from user_config import UserConfig
from permission_manager import (
    get_user_consent,
    get_analysis_mode,
    get_advanced_options
)
from file_parser import get_input_file_path
from metadata_extractor import base_extraction, detailed_extraction, load_filters
from alternative_analysis import analyze_projects


def orchestrator():
    print("Welcome to Skill Scope!")
    print("~~~~~~~~~~~~~~~~~~~~~~~")


    # --- Step 1: Try loading the previous session ---
    #TODO load database if available. if not create a new one. conn is blank for now until DB is implemented
    conn = ""

    # Load userconfig if available. if not, create one,
    #TODO: load config once DB is implemented. blank for now
    config = UserConfig()
    if config is None:
        config = UserConfig()

    # --- Step 2: Ensure consent is recorded ---
    if config.consent is False:
        # meaning user has not given consent yet
        consent = get_user_consent()
        if not consent:
            exit()
        config.consent = True
        config.save_to_db(conn)

    # --- Step 3: Ensure analysis mode is recorded ---
    if config.analysis_mode == "default":
        config.analysis_mode = get_analysis_mode()
        config.save_to_db(conn)

    # --- Step 4: If advanced mode, ensure advanced options are stored ---
    advanced_options = {}
    if config.analysis_mode == "advanced":
        advanced_options = get_advanced_options()
        # Could store these later if desired

    # --- Step 5: Get project files ---
    file_list = get_input_file_path()

    if file_list:
        filters = load_filters()

        scraped_data = base_extraction(file_list, filters)

        if config.analysis_mode == "advanced":
            detailed_data = detailed_extraction(scraped_data)
        else:
            detailed_data = None
        """
        TODO: integrarte detailed_data with analyze and scan options
        # Step 7: Run analysis with metadata and any advanced options
        analyze_projects(
            scraped_data,
            filters,
            analysis_mode=analysis_mode,
            advanced_options=advanced_options,
            detailed_data=advanced_data
        )
        """

        #for analysis part
        analyze_projects(scraped_data, filters)

#Runs orchestrator
if __name__ == "__main__":
    orchestrator()

