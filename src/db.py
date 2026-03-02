import sqlite3
import json
import os
from datetime import datetime
from typing import Any, Mapping, Optional

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

# Table to store file hashes for deduplication (One-to-Many relationship)
CREATE_SCAN_HASHES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scan_hashes (
    hash_id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    FOREIGN KEY(summary_id) REFERENCES full_scan_summaries(summary_id)
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
    # Ensure the table for full scans exists.
    conn.execute(CREATE_FULL_SCAN_TABLE_SQL)
    conn.execute(CREATE_SCAN_HASHES_TABLE_SQL)

# ----------------------
# Save results
# ----------------------


""" 

Temporary, generic, short term DB saving. Our returned data is changing so much that it makes more sense to save the entire summary as one data type rather than refactor it everytime something is added.

"""
# For displaying in selection now.
def list_full_scans(db_path=DB_NAME):
    """
    Return minimal info (ID, timestamp, mode) about each scan for selection menus.
    Does NOT load the heavy JSON data, making it fast for listing.
    """
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT summary_id, timestamp, analysis_mode FROM full_scan_summaries ORDER BY timestamp DESC").fetchall()
        return [dict(row) for row in rows]

# Saving method for all data
def save_full_scan(
    analysis_results: Mapping[str, Any], 
    analysis_mode: str,
    user_consent: bool,
    db_path: str = DB_NAME
) -> Optional[int]:
    """
    Save a full scan, including summaries, resume bullets, skills over time, and chronological projects.
    The complex nested structure is serialized into a single JSON blob.
    """
    if not analysis_results or "project_summaries" not in analysis_results:
        return None

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
        "source_hashes": [analysis_results.get("zip_hash")] if analysis_results.get("zip_hash") else [],
        "timestamp": datetime.now().isoformat()
    }
    
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute(
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
        summary_id = cursor.lastrowid

        # Save hashes to the lookup table for fast deduplication
        hashes = full_scan_data.get("source_hashes", [])
        if hashes:
            conn.executemany(
                "INSERT INTO scan_hashes (summary_id, file_hash) VALUES (?, ?)",
                [(summary_id, h) for h in hashes]
            )
        conn.commit()
        return summary_id

def update_full_scan(summary_id, merged_data, db_path=DB_NAME):
    """
    Updates the JSON data for an existing scan record.
    Used when adding incremental information to a portfolio.
    """
    # Helper to serialize datetimes (similar to save_full_scan)
    def _serialize_project(p): 
        p_copy = p.copy()
        for key in ["first_modified", "last_modified"]:
            if key in p_copy and isinstance(p_copy[key], datetime):
                p_copy[key] = p_copy[key].isoformat()
        return p_copy

    if "project_summaries" in merged_data:
        merged_data["project_summaries"] = [
            _serialize_project(p) for p in merged_data["project_summaries"]
        ]

    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.execute(
            "UPDATE full_scan_summaries SET project_summaries_json = ? WHERE summary_id = ?",
            (json.dumps(merged_data, ensure_ascii=False, default=str), summary_id)
        )
        
        # Update hashes table: Remove old entries and re-insert the current list
        conn.execute("DELETE FROM scan_hashes WHERE summary_id = ?", (summary_id,))
        
        hashes = merged_data.get("source_hashes", [])
        if hashes:
            conn.executemany(
                "INSERT INTO scan_hashes (summary_id, file_hash) VALUES (?, ?)",
                [(summary_id, h) for h in hashes]
            )
        conn.commit()

def get_full_scan_by_id(summary_id, db_path=DB_NAME):
    """
    Return a single full scan by ID, including the parsed JSON data.
    Used when the user selects a specific scan to view or generate reports from.
    """
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
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
        ensure_db_initialized(conn)
        cursor = conn.execute("DELETE FROM full_scan_summaries WHERE summary_id = ?", (summary_id,))
        conn.execute("DELETE FROM scan_hashes WHERE summary_id = ?", (summary_id,))
        conn.commit()
    return cursor.rowcount > 0

def scan_exists(zip_hash, db_path=DB_NAME):
    """Checks if a scan with the given zip_hash already exists."""
    if not zip_hash:
        return False
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        row = conn.execute("SELECT 1 FROM scan_hashes WHERE file_hash = ?", (zip_hash,)).fetchone()
        return row is not None
