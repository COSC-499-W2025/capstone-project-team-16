import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import Any, Mapping, Sequence, Optional, List, Dict

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
    score INTEGER,
    user_consent TEXT,
    analysis_mode TEXT,
    project_id TEXT,
    user_id TEXT,
    analysis_data TEXT,
    file_tree TEXT,
    resume_bullets TEXT
)
"""

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
    score, 
    user_consent, 
    analysis_mode,
    project_id, 
    user_id, 
    analysis_data, 
    file_tree, 
    resume_bullets
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


# ----------------------
# Initialization
# ----------------------

def ensure_db_initialized(conn: sqlite3.Connection) -> None:
    """
    Ensures the 'project_summaries' table and 'user_config' exists in the database.
    Only runs once per program execution.
    """
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(USER_CONFIG_TABLE_SQL)
    """Ensure the table for full scans exists."""
    conn.execute(CREATE_FULL_SCAN_TABLE_SQL)

# ----------------------
# Save results
# ----------------------


""" 

Temporary, generic, short term DB saving. Our returned data is changing so much that it makes more sense to save the entire summary as one data type rather than refactor it everytime something is added.

"""
# For displaying in selection now.
def list_full_scans(db_path=DB_NAME):
    """Return minimal info about each scan for selection menus."""
    scans = get_all_full_scans(db_path)
    return [{"summary_id": s["summary_id"], "timestamp": s["timestamp"], "analysis_mode": s["analysis_mode"]} for s in scans]

# Saving method for all data
def save_full_scan(
    analysis_results: Mapping[str, any], 
    analysis_mode: str,
    user_consent: bool,
    db_path: str = DB_NAME
) -> None:
    """
    Save a full scan, including summaries, resume bullets, skills over time, and chronological projects.
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

    full_scan_data = {
        "project_summaries": serialized_projects,
        "resume_summaries": analysis_results.get("resume_summaries", []),
        "skills_chronological": analysis_results.get("skills_chronological", []),
        "projects_chronological": analysis_results.get("projects_chronological", []),
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
                json.dumps(full_scan_data, ensure_ascii=False),
            )
        )
        conn.commit()

def get_all_full_scans(db_path=DB_NAME):
    """Return all full scans stored in the DB as a list of dicts."""
    import sqlite3, json

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM full_scan_summaries ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "summary_id": row["summary_id"],
                "timestamp": row["timestamp"],
                "analysis_mode": row["analysis_mode"],
                "user_consent": row["user_consent"],
                "project_summaries_json": json.loads(row["project_summaries_json"]) if row["project_summaries_json"] else {}
            })
        return results
    

def delete_full_scan_by_id(summary_id, db_path=DB_NAME):
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM full_scan_summaries WHERE summary_id = ?", (summary_id,))
        conn.commit()
        return True




# Full save results (needs to be reconfigured to support final data types)
def save_results(
    results_list: Sequence[Mapping[str, Any]],
    user_consent: bool,
    analysis_mode: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    file_tree: Optional[Any] = None,
    resume_bullets: Optional[Sequence[str]] = None,
    db_path: str = DB_NAME
) -> None:
    """
    Saves a list of project-analysis dictionaries to the SQLite database.
    Each row includes:
      - a unique project_id
      - user_id (if available)
      - analysis_data (JSON)
      - file_tree (JSON)
      - resume_bullets (JSON list)
      - all the summary metrics (files, score, etc.)
      - user_consent + analysis_mode
    Backwards-compatible: existing callers can still use
      save_results(results, user_consent, analysis_mode)
    and omit the rest.
    """
    if not results_list:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    consent_str = "Yes" if user_consent else "No"
    rows = []

    for p in results_list:
        pid = p.get("project_id") or project_id or str(uuid.uuid4())
        uid = p.get("user_id") or user_id or ""

        # Analysis data JSON
        raw_analysis = p.get("analysis_data", p)
        analysis_data_str = raw_analysis if isinstance(raw_analysis, str) else json.dumps(raw_analysis)

        # File tree JSON
        ft_obj = p.get("file_tree", file_tree)
        file_tree_str = ft_obj if isinstance(ft_obj, str) or ft_obj is None else json.dumps(ft_obj)

        # Resume bullets JSON
        rb_obj = p.get("resume_bullets", resume_bullets)
        if rb_obj is None:
            resume_bullets_str = json.dumps([])
        elif isinstance(rb_obj, str):
            resume_bullets_str = rb_obj
        else:
            resume_bullets_str = json.dumps(list(rb_obj))

        rows.append((
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
            consent_str,
            analysis_mode,
            pid,
            uid,
            analysis_data_str,
            file_tree_str,
            resume_bullets_str,
        ))

    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.executemany(INSERT_SQL, rows)
        conn.commit()

# ----------------------
# Generic helpers
# ----------------------

def get_all_summaries(db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM project_summaries").fetchall()]

def get_summary_by_id(summary_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM project_summaries WHERE id = ?", (summary_id,)).fetchone()
        return dict(row) if row else None

def delete_summary(summary_id: int, db_path: str = DB_NAME) -> bool:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute("DELETE FROM project_summaries WHERE id = ?", (summary_id,))
        conn.commit()
        return cursor.rowcount > 0

def update_summary(summary_id: int, fields: Mapping[str, Any], db_path: str = DB_NAME) -> bool:
    if not fields:
        return False
    set_clause = ", ".join(f"{col} = ?" for col in fields.keys())
    values = list(fields.values()) + [summary_id]
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute(f"UPDATE project_summaries SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return cursor.rowcount > 0

def search_by_project_name(name: str, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    pattern = f"%{name}%"
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM project_summaries WHERE project_name LIKE ?", (pattern,)).fetchall()
        return [dict(row) for row in rows]

# ----------------------
# Requirement-specific helpers
# ----------------------

def store_project_insights(
    project: Mapping[str, Any],
    user_id: str,
    project_id: str,
    user_consent: bool,
    analysis_mode: str,
    file_tree: Any,
    resume_bullets: Optional[Sequence[str]] = None,
    db_path: str = DB_NAME
) -> None:
    """
    Convenience wrapper to store a single project's insights:
    Output row conceptually matches:
      {project_id, user_id, analysis_data}
    where:
      - project_id: provided
      - user_id: provided
      - analysis_data: JSON representation of `project` dict
    """
    save_results(
        [project],
        user_consent=user_consent,
        analysis_mode=analysis_mode,
        user_id=user_id,
        project_id=project_id,
        file_tree=file_tree,
        resume_bullets=resume_bullets,
        db_path=db_path,
    )



    """
    Retrieve previously generated portfolio information.
    Output: List of stored project summaries.
    If user_id is provided, only return that user's projects.
    """

def list_project_summaries(user_id: Optional[str] = None, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                """SELECT 
                        project_id, 
                        user_id, 
                        project_name, 
                        score, 
                        total_files, 
                        duration_days,
                        languages, 
                        frameworks, 
                        skills, 
                        scan_date
                   FROM project_summaries
                   WHERE user_id = ?
                   ORDER BY scan_date DESC""",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT 
                        project_id, 
                        user_id, 
                        project_name, 
                        score, 
                        total_files, 
                        duration_days,
                        languages, 
                        frameworks, 
                        skills, 
                        scan_date
                   FROM project_summaries
                   ORDER BY scan_date DESC"""
            ).fetchall()
        return [dict(row) for row in rows]

def get_resume_bullets(user_id: Optional[str] = None, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT project_id, user_id, project_name, resume_bullets FROM project_summaries WHERE user_id = ?",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT project_id, user_id, project_name, resume_bullets FROM project_summaries"
            ).fetchall()
    bullets: List[Dict[str, Any]] = []
    for row in rows:
        rb_raw = row["resume_bullets"]
        try:
            parsed = json.loads(rb_raw) if rb_raw else []
        except json.JSONDecodeError:
            parsed = [rb_raw] if rb_raw else []
        for b in parsed:
            bullets.append({
                "project_id": row["project_id"],
                "user_id": row["user_id"],
                "project_name": row["project_name"],
                "bullet": b
            })
    return bullets

def delete_project_insights(project_id: str, db_path: str = DB_NAME) -> bool:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute("DELETE FROM project_summaries WHERE project_id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0



