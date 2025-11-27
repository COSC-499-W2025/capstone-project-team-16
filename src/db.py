import sqlite3
from datetime import datetime
from typing import Any, Mapping, Sequence

# Database file name (auto-created if missing)
DB_NAME = "skillscope.db"

# Creates table to store project scan summaries
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS project_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TEXT,
    project_name TEXT,
    total_files INTEGER,
    duration_days INTEGER,
    code_files INTEGER,
    test_files INTEGER,
    doc_files INTEGER,
    design_files INTEGER,
    languages TEXT,
    frameworks TEXT,
    skills TEXT,
    is_collaborative TEXT,
    score INTEGER
)
"""
# Inserts project summary data into the table
INSERT_SQL = """
INSERT INTO project_summaries (
    scan_date,
    project_name,
    total_files,
    duration_days,
    code_files,
    test_files,
    doc_files,
    design_files,
    languages,
    frameworks,
    skills,
    is_collaborative,
    score
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
# Prevents re-running CREATE TABLE multiple times per process
db_initialized = False

def ensure_db_initialized(conn: sqlite3.Connection) -> None:
    """
    Ensures the 'project_summaries' table exists in the database.
    Only runs once per program execution.
    """
    global db_initialized
    if db_initialized:
        return
    conn.execute(CREATE_TABLE_SQL)
    db_initialized = True

def save_results(results_list: Sequence[Mapping[str, Any]]) -> None:
    """
    Saves a list of project-analysis dictionaries to the SQLite database.
    Missing fields are safely filled with default values.
    """
    if not results_list:
        print("Error: No results to save.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Convert each project dict into a DB row
    rows = [
        (
            timestamp,
            p.get("project", "Unknown"),
            p.get("total_files", 0),
            p.get("duration_days", 0),
            p.get("code_files", 0),
            p.get("test_files", 0),
            p.get("doc_files", 0),
            p.get("design_files", 0),
            p.get("languages", ""),
            p.get("frameworks", ""),
            p.get("skills", ""),
            p.get("is_collaborative", "No"),
            p.get("score", 0),
        )
        for p in results_list
    ]

    try:
        # Open DB connection safely
        with sqlite3.connect(DB_NAME) as conn:
            # Create table if necessary
            ensure_db_initialized(conn)
            # Insert all data in one batch
            conn.executemany(INSERT_SQL, rows)
            conn.commit()

        print(f"Saved {len(rows)} project summaries to the database.")

    except Exception as e:
        print(f"Error saving results to database: {e}")