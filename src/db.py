import sqlite3
import json
import uuid
from datetime import datetime
from typing import Any, Mapping, Sequence

# Database file name (auto-created if missing)
DB_NAME = "skillscope.db"

# Creates user config table if it doesn't exist
USER_CONFIG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    consent TEXT,
    analysis_mode TEXT,
    advanced_scans TEXT,
    last_updated TEXT
)
"""


# Creates table to store project scan summaries + analysis metadata
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
    user_consent TEXT,      -- "Yes" or "No"
    analysis_mode TEXT,     -- "basic" or "advanced"
    project_id TEXT,        -- unique project identifier
    user_id TEXT,           -- user owning the project
    analysis_data TEXT,     -- JSON blob of analysis data
    file_tree TEXT,         -- JSON representation of file tree
    resume_bullets TEXT     -- JSON list of resume bullet strings
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
    score,
    user_consent,
    analysis_mode,
    project_id,
    user_id,
    analysis_data,
    file_tree,
    resume_bullets
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# Prevents re-running CREATE TABLE multiple times per process
db_initialized = False



def ensure_db_initialized(conn: sqlite3.Connection) -> None:
    """
    Ensures all required tables exist in the database.
    Only runs once per program execution.
    """
    global db_initialized
    if db_initialized:
        return

    # project summaries table
    conn.execute(CREATE_TABLE_SQL)

    # User config table
    conn.execute(USER_CONFIG_TABLE_SQL)

    db_initialized = True


def save_results(
    results_list: Sequence[Mapping[str, Any]],
    user_consent: bool,
    analysis_mode: str,
    user_id: str | None = None,
    project_id: str | None = None,
    file_tree: Any | None = None,
    resume_bullets: Sequence[str] | None = None,
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
        print("Error: No results to save.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    consent_str = "Yes" if user_consent else "No"

    rows = []
    for p in results_list:
        # Unique project ID (prefer project dict, then function arg, then UUID)
        pid = p.get("project_id") or project_id or str(uuid.uuid4())
        # User ID: prefer per-project, then function-level, else empty
        uid = p.get("user_id") or user_id or ""

        # Analysis data: if caller provides a structured object or string, store it.
        # Default fallback: the whole project dict.
        raw_analysis = p.get("analysis_data", p)
        if isinstance(raw_analysis, str):
            analysis_data_str = raw_analysis
        else:
            analysis_data_str = json.dumps(raw_analysis)

        # File tree: can be provided per-project or via argument
        ft_obj = p.get("file_tree", file_tree)
        if isinstance(ft_obj, str) or ft_obj is None:
            file_tree_str = ft_obj
        else:
            file_tree_str = json.dumps(ft_obj)

        # Resume bullets: per-project or function-level, stored as JSON list
        rb_obj = p.get("resume_bullets", resume_bullets)
        if rb_obj is None:
            resume_bullets_str = json.dumps([])
        elif isinstance(rb_obj, str):
            # Assume already serialized or simple text
            resume_bullets_str = rb_obj
        else:
            resume_bullets_str = json.dumps(list(rb_obj))

        rows.append(
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
                consent_str,
                analysis_mode,
                pid,
                uid,
                analysis_data_str,
                file_tree_str,
                resume_bullets_str,
            )
        )

    try:
        with sqlite3.connect(DB_NAME) as conn:
            ensure_db_initialized(conn)
            conn.executemany(INSERT_SQL, rows)
            conn.commit()

        print(f"Saved {len(rows)} project summaries to the database.")

    except Exception as e:
        print(f"Error saving results to database: {e}")


# ----------------------
# Generic read/write helpers
# ----------------------

def get_all_summaries() -> list[dict]:
    """
    Returns all rows from the project_summaries table as a list of dicts.
    """
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM project_summaries").fetchall()
        return [dict(row) for row in rows]


def get_summary_by_id(summary_id: int) -> dict | None:
    """
    Returns a single project summary by internal numeric ID.
    """
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM project_summaries WHERE id = ?",
            (summary_id,),
        ).fetchone()
        return dict(row) if row else None


def delete_summary(summary_id: int) -> bool:
    """
    Deletes a row by internal numeric ID. Returns True if a row was deleted.
    """
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute(
            "DELETE FROM project_summaries WHERE id = ?",
            (summary_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_summary(summary_id: int, fields: Mapping[str, Any]) -> bool:
    """
    Updates any subset of fields for a project summary.
    `fields` is a dict like {"score": 85, "project_name": "New Name"}.
    Returns True if a row was updated.
    """
    if not fields:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in fields.keys())
    values = list(fields.values()) + [summary_id]

    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute(
            f"UPDATE project_summaries SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount > 0


def search_by_project_name(name: str) -> list[dict]:
    """
    Performs a LIKE search on project_name. Case-insensitive by default in SQLite.
    """
    pattern = f"%{name}%"
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM project_summaries WHERE project_name LIKE ?",
            (pattern,),
        ).fetchall()
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
    resume_bullets: Sequence[str] | None = None,
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
    )


def list_project_summaries(user_id: str | None = None) -> list[dict]:
    """
    Retrieve previously generated portfolio information.

    Output: List of stored project summaries.

    If user_id is provided, only return that user's projects.
    """
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                """
                SELECT
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
                ORDER BY scan_date DESC
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
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
                ORDER BY scan_date DESC
                """
            ).fetchall()
    return [dict(row) for row in rows]


def get_resume_bullets(user_id: str | None = None) -> list[dict]:
    """
    Retrieve previously generated résumé items.

    Output: list of structured bullet points:
      [
        {
          "project_id": ...,
          "user_id": ...,
          "project_name": ...,
          "bullet": "Implemented X using Y to achieve Z"
        },
        ...
      ]
    """
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT project_id, user_id, project_name, resume_bullets "
                "FROM project_summaries WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT project_id, user_id, project_name, resume_bullets "
                "FROM project_summaries",
            ).fetchall()

    bullets: list[dict] = []
    for row in rows:
        rb_raw = row["resume_bullets"]
        try:
            parsed = json.loads(rb_raw) if rb_raw else []
        except json.JSONDecodeError:
            parsed = [rb_raw] if rb_raw else []

        for b in parsed:
            bullets.append(
                {
                    "project_id": row["project_id"],
                    "user_id": row["user_id"],
                    "project_name": row["project_name"],
                    "bullet": b,
                }
            )
    return bullets


def delete_project_insights(project_id: str) -> bool:
    """
    Delete previously generated insights for a given project_id.

    This removes stored analyses / derived data without touching original uploads
    (which should be stored elsewhere, e.g., on disk or in object storage).

    IMPORTANT: Callers (CLI / UI) should confirm deletion with the user
    BEFORE calling this function.

    Output: True if something was deleted, False otherwise.
    """
    with sqlite3.connect(DB_NAME) as conn:
        ensure_db_initialized(conn)
        cursor = conn.execute(
            "DELETE FROM project_summaries WHERE project_id = ?",
            (project_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

