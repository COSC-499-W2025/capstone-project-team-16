import sqlite3
import json
import uuid
from datetime import datetime
from typing import Any, Mapping, Sequence, Optional, List, Dict

# Default database file name
DB_NAME = "skillscope.db"

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
    scan_date, project_name, total_files, duration_days,
    code_files, test_files, doc_files, design_files,
    languages, frameworks, skills, is_collaborative,
    score, user_consent, analysis_mode,
    project_id, user_id, analysis_data, file_tree, resume_bullets
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ----------------------
# Initialization
# ----------------------

def ensure_db_initialized(conn: sqlite3.Connection) -> None:
    """Ensure all tables exist."""
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(USER_CONFIG_TABLE_SQL)

# ----------------------
# Save results
# ----------------------

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
    """Save a list of project summaries into SQLite."""
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

def list_project_summaries(user_id: Optional[str] = None, db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_db_initialized(conn)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                """SELECT project_id, user_id, project_name, score, total_files, duration_days,
                          languages, frameworks, skills, scan_date
                   FROM project_summaries
                   WHERE user_id = ?
                   ORDER BY scan_date DESC""",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT project_id, user_id, project_name, score, total_files, duration_days,
                          languages, frameworks, skills, scan_date
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
