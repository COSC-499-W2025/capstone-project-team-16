import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import Mapping, List, Dict

# Default DB file name
DEFAULT_DB_FILENAME = "skillscope.db"

# Determine writable DB directory
# Can override with environment variable (useful in Docker)
DB_DIR = os.environ.get("SKILLSCOPE_DB_DIR")
if not DB_DIR:
    # Local default: create 'data' folder next to src
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

# Ensure the folder exists
os.makedirs(DB_DIR, exist_ok=True)

# Full DB path
DB_NAME = os.path.join(DB_DIR, DEFAULT_DB_FILENAME)

# Creates table to store project scan summaries + analysis metadata
# ----------------------
# SQL definitions
# ----------------------

USER_CONFIG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    consent TEXT,
    analysis_mode TEXT,
    advanced_scans TEXT,
    last_updated TEXT
)
"""

# Table for storing complete scan results.
# Instead of normalizing every project into relational tables, we store the 
# entire analysis structure as a JSON blob in 'project_summaries_json'.
# This allows for flexible schema changes in the analysis logic without DB migrations.

# full scan summary table
CREATE_FULL_SCAN_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS full_scan_summaries (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    analysis_mode TEXT NOT NULL,
    user_consent TEXT NOT NULL,
    project_summaries_json TEXT NOT NULL
)
"""


# ----------------------
# Initialization
# ----------------------

def ensure_db_initialized(conn: sqlite3.Connection) -> None:
    """
    Ensures the 'project_summaries' table and 'user_config' exists in the database.
    Only runs once per program execution.
    """

    conn.execute(USER_CONFIG_TABLE_SQL)
    """Ensure the table for full scans exists."""
    conn.execute(CREATE_FULL_SCAN_TABLE_SQL)

# ----------------------
# Save results
# ----------------------


# For displaying in selection now.
def list_full_scans(db_path=DB_NAME):
    """
    Return minimal info (ID, timestamp, mode) about each scan for selection menus.
    Does NOT load the heavy JSON data, making it fast for listing.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT summary_id, timestamp, analysis_mode FROM full_scan_summaries ORDER BY timestamp DESC").fetchall()
        return [dict(row) for row in rows]

# Saving method for all data
def save_full_scan(
    analysis_results: Mapping[str, any], 
    analysis_mode: str,
    user_consent: bool,
    db_path: str = DB_NAME
) -> None:
    """
    Save a full scan, including summaries, resume bullets, skills over time, and chronological projects.
    The complex nested structure is serialized into a single JSON blob.
    """
    if not analysis_results or "project_summaries" not in analysis_results:
        return

    # Serialize datetime fields in projects
    def _serialize_project(p):
        p_copy = p.copy()
        for key in ["first_modified", "last_modified"]:
            if key in p_copy and isinstance(p_copy[key], datetime):
                p_copy[key] = p_copy[key].isoformat()
        return p_copy

    serialized_projects = [
        _serialize_project(p) for p in analysis_results["project_summaries"]
    ]

    # Construct the master dictionary to be saved as JSON
    full_scan_data = {
        "project_summaries": serialized_projects,
        "resume_summaries": analysis_results.get("resume_summaries", []),
        "skills_chronological": analysis_results.get("skills_chronological", []),
        "projects_chronological": analysis_results.get("projects_chronological", []),
        "contributor_profiles": analysis_results.get("contributor_profiles", {}),
        "analysis_mode": analysis_mode,
        "user_consent": "Yes" if user_consent else "No",
        "timestamp": datetime.now().isoformat()
    }

    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.execute(
            """
            INSERT INTO full_scan_summaries (timestamp, analysis_mode, user_consent, project_summaries_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                full_scan_data["timestamp"],
                analysis_mode,
                full_scan_data["user_consent"],
                json.dumps(full_scan_data, ensure_ascii=False, default=str),
            )
        )
        conn.commit()

def get_full_scan_by_id(summary_id, db_path=DB_NAME):
    """
    Return a single full scan by ID, including the parsed JSON data.
    Used when the user selects a specific scan to view or generate reports from.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM full_scan_summaries WHERE summary_id = ?", (summary_id,)).fetchone()
        if row:
            # Load the JSON blob which contains the FULL scan data (projects, contributors, skills, etc.)
            scan_data = json.loads(row["project_summaries_json"]) if row["project_summaries_json"] else {}
            
            # Debug: Verify keys loaded
            # print(f"DEBUG: DB Loaded keys: {list(scan_data.keys())}")

            return {
                "summary_id": row["summary_id"],
                "timestamp": row["timestamp"],
                "analysis_mode": row["analysis_mode"],
                "user_consent": row["user_consent"],
                "scan_data": scan_data
            }
        return None

def delete_full_scan_by_id(summary_id, db_path=DB_NAME):
    """Permanently delete a scan record by its ID."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("DELETE FROM full_scan_summaries WHERE summary_id = ?", (summary_id,))
        conn.commit()
        return cursor.rowcount > 0

