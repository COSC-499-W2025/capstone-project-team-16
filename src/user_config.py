from datetime import datetime
import json

class UserConfig:
    """
    Represents persistent user preferences for the Skill Scope application.
    Only ONE row will ever exist in the database.
    """

    def __init__(self, consent=False, analysis_mode="default", advanced_scans=None, last_updated=None):
        self.consent = consent

    # ---------------------------------------------------------
    # Database Methods TODO:Integrate and save into DB
    # ---------------------------------------------------------

    def save_to_db(self, conn):
        """
        Insert/update the single UserConfig row.
        """

    @classmethod
    def load_from_db(cls, conn):
        """
        Loads the ONE config row. Returns UserConfig or None.
        """
        
    def delete_from_db(self, conn):
        """
        Deletes the single config entry.
        """
