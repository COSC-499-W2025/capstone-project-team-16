import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from db import DB_NAME, ensure_db_initialized


CREATE_PRIVACY_SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_privacy_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    settings_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

CREATE_PROJECT_CUSTOMIZATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_project_customizations (
    project_id TEXT PRIMARY KEY,
    customization_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

CREATE_RESUME_ARTIFACTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_resume_artifacts (
    resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_summary_id INTEGER,
    title TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

CREATE_PORTFOLIO_ARTIFACTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_portfolio_artifacts (
    portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_summary_id INTEGER,
    title TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def ensure_api_tables(conn: sqlite3.Connection) -> None:
    ensure_db_initialized(conn)
    conn.execute(CREATE_PRIVACY_SETTINGS_TABLE_SQL)
    conn.execute(CREATE_PROJECT_CUSTOMIZATIONS_TABLE_SQL)
    conn.execute(CREATE_RESUME_ARTIFACTS_TABLE_SQL)
    conn.execute(CREATE_PORTFOLIO_ARTIFACTS_TABLE_SQL)


def _now_iso() -> str:
    return datetime.now().isoformat()


def _load_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def get_privacy_settings(db_path: str = DB_NAME) -> Dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT settings_json, updated_at FROM api_privacy_settings WHERE id = 1"
        ).fetchone()
        if not row:
            return {
                "consent": False,
                "external_services_allowed": False,
                "notes": "",
                "updated_at": None,
            }
        settings = _load_json(row["settings_json"], {})
        settings["updated_at"] = row["updated_at"]
        return settings


def set_privacy_settings(settings: Dict[str, Any], db_path: str = DB_NAME) -> Dict[str, Any]:
    updated_at = _now_iso()
    payload = dict(settings)
    payload.pop("updated_at", None)
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.execute(
            """
            INSERT INTO api_privacy_settings (id, settings_json, updated_at)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                settings_json = excluded.settings_json,
                updated_at = excluded.updated_at
            """,
            (json.dumps(payload, ensure_ascii=False), updated_at),
        )
        conn.commit()
    payload["updated_at"] = updated_at
    return payload


def get_project_customization(project_id: str, db_path: str = DB_NAME) -> Dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        row = conn.execute(
            "SELECT customization_json, updated_at FROM api_project_customizations WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return {}
        data = _load_json(row[0], {})
        if isinstance(data, dict):
            data["updated_at"] = row[1]
            return data
        return {}


def upsert_project_customization(
    project_id: str,
    patch: Dict[str, Any],
    db_path: str = DB_NAME,
) -> Dict[str, Any]:
    existing = get_project_customization(project_id, db_path=db_path)
    existing.pop("updated_at", None)
    merged = dict(existing)
    for key, value in patch.items():
        if value is None:
            continue
        merged[key] = value

    updated_at = _now_iso()
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.execute(
            """
            INSERT INTO api_project_customizations (project_id, customization_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                customization_json = excluded.customization_json,
                updated_at = excluded.updated_at
            """,
            (project_id, json.dumps(merged, ensure_ascii=False), updated_at),
        )
        conn.commit()
    merged["updated_at"] = updated_at
    return merged


def list_project_customizations(db_path: str = DB_NAME) -> Dict[str, Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT project_id, customization_json, updated_at FROM api_project_customizations"
        ).fetchall()
    output: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        data = _load_json(row["customization_json"], {})
        if isinstance(data, dict):
            data["updated_at"] = row["updated_at"]
            output[row["project_id"]] = data
    return output


def create_resume_artifact(
    data: Dict[str, Any],
    scan_summary_id: Optional[int] = None,
    title: Optional[str] = None,
    db_path: str = DB_NAME,
) -> Dict[str, Any]:
    now = _now_iso()
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        cur = conn.execute(
            """
            INSERT INTO api_resume_artifacts (scan_summary_id, title, data_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_summary_id, title, json.dumps(data, ensure_ascii=False), now, now),
        )
        resume_id = cur.lastrowid
        conn.commit()
    return get_resume_artifact(resume_id, db_path=db_path)  # type: ignore[arg-type]


def get_resume_artifact(resume_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT resume_id, scan_summary_id, title, data_json, created_at, updated_at
            FROM api_resume_artifacts WHERE resume_id = ?
            """,
            (resume_id,),
        ).fetchone()
        if not row:
            return None
    return {
        "resume_id": row["resume_id"],
        "scan_summary_id": row["scan_summary_id"],
        "title": row["title"],
        "data": _load_json(row["data_json"], {}),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def update_resume_artifact(
    resume_id: int,
    patch: Dict[str, Any],
    db_path: str = DB_NAME,
) -> Optional[Dict[str, Any]]:
    existing = get_resume_artifact(resume_id, db_path=db_path)
    if not existing:
        return None
    data = dict(existing["data"])
    for key, value in patch.items():
        if key == "title":
            continue
        if value is not None:
            data[key] = value
    title = patch.get("title", existing["title"])
    updated_at = _now_iso()
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.execute(
            """
            UPDATE api_resume_artifacts
            SET title = ?, data_json = ?, updated_at = ?
            WHERE resume_id = ?
            """,
            (title, json.dumps(data, ensure_ascii=False), updated_at, resume_id),
        )
        conn.commit()
    return get_resume_artifact(resume_id, db_path=db_path)


def create_portfolio_artifact(
    data: Dict[str, Any],
    scan_summary_id: Optional[int] = None,
    title: Optional[str] = None,
    db_path: str = DB_NAME,
) -> Dict[str, Any]:
    now = _now_iso()
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        cur = conn.execute(
            """
            INSERT INTO api_portfolio_artifacts (scan_summary_id, title, data_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (scan_summary_id, title, json.dumps(data, ensure_ascii=False), now, now),
        )
        portfolio_id = cur.lastrowid
        conn.commit()
    return get_portfolio_artifact(portfolio_id, db_path=db_path)  # type: ignore[arg-type]


def get_portfolio_artifact(portfolio_id: int, db_path: str = DB_NAME) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT portfolio_id, scan_summary_id, title, data_json, created_at, updated_at
            FROM api_portfolio_artifacts WHERE portfolio_id = ?
            """,
            (portfolio_id,),
        ).fetchone()
        if not row:
            return None
    return {
        "portfolio_id": row["portfolio_id"],
        "scan_summary_id": row["scan_summary_id"],
        "title": row["title"],
        "data": _load_json(row["data_json"], {}),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def update_portfolio_artifact(
    portfolio_id: int,
    patch: Dict[str, Any],
    db_path: str = DB_NAME,
) -> Optional[Dict[str, Any]]:
    existing = get_portfolio_artifact(portfolio_id, db_path=db_path)
    if not existing:
        return None
    data = dict(existing["data"])
    for key, value in patch.items():
        if key == "title":
            continue
        if value is not None:
            data[key] = value
    title = patch.get("title", existing["title"])
    updated_at = _now_iso()
    with sqlite3.connect(db_path) as conn:
        ensure_api_tables(conn)
        conn.execute(
            """
            UPDATE api_portfolio_artifacts
            SET title = ?, data_json = ?, updated_at = ?
            WHERE portfolio_id = ?
            """,
            (title, json.dumps(data, ensure_ascii=False), updated_at, portfolio_id),
        )
        conn.commit()
    return get_portfolio_artifact(portfolio_id, db_path=db_path)
