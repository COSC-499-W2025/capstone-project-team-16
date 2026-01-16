import json
import sqlite3
import pytest
import db
from datetime import datetime
import os


@pytest.fixture
def db_path(tmp_path):
    """Temporary DB path for each test."""
    return str(tmp_path / "test_metrics.db")


@pytest.fixture(autouse=True)
def reset_db_init_flag():
    """
    Reset the internal db_initialized flag before each test.

    This keeps behavior predictable while still allowing the
    optimization (create table once per process) to be tested.
    """
    if hasattr(db, "db_initialized"):
        db.db_initialized = False


def _fetch_all(db_path: str, query: str, params=()):
    """Run a query and return all rows."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


# ----------------------------------------------------------------------
# New tests for full_scan_summaries logic
# ----------------------------------------------------------------------

def test_save_full_scan_creates_tables_and_inserts_data(db_path):
    # Prepare dummy analysis results
    analysis_results = {
        "project_summaries": [
            {
                "project": "TestProj", 
                "score": 100, 
                "first_modified": datetime(2023, 1, 1, 12, 0, 0),
                "last_modified": datetime(2023, 1, 2, 12, 0, 0)
            }
        ],
        "resume_summaries": ["Bullet 1"],
        "skills_chronological": [],
        "projects_chronological": [],
        "contributor_profiles": {"user1": {"skills": ["Python"]}}
    }

    # Action
    db.save_full_scan(analysis_results, "advanced", True, db_path=db_path)

    # Verify tables exist
    tables = _fetch_all(
        db_path,
        "SELECT name FROM sqlite_master WHERE type='table';"
    )
    table_names = [t[0] for t in tables]
    assert "full_scan_summaries" in table_names
    assert "user_config" in table_names

    # Verify data insertion
    rows = _fetch_all(
        db_path, 
        "SELECT timestamp, analysis_mode, user_consent, project_summaries_json FROM full_scan_summaries"
    )
    assert len(rows) == 1
    ts, mode, consent, json_str = rows[0]

    assert mode == "advanced"
    assert consent == "Yes"
    
    # Verify JSON content
    data = json.loads(json_str)
    assert data["analysis_mode"] == "advanced"
    assert data["user_consent"] == "Yes"
    assert len(data["project_summaries"]) == 1
    
    # Verify datetime serialization
    p_summary = data["project_summaries"][0]
    assert p_summary["project"] == "TestProj"
    assert p_summary["first_modified"] == "2023-01-01T12:00:00"
    assert p_summary["last_modified"] == "2023-01-02T12:00:00"
    
    # Verify other fields
    assert data["contributor_profiles"]["user1"]["skills"] == ["Python"]


def test_list_full_scans_returns_lightweight_metadata(db_path):
    # Save two scans
    db.save_full_scan({"project_summaries": []}, "basic", True, db_path=db_path)
    db.save_full_scan({"project_summaries": []}, "advanced", False, db_path=db_path)

    # Action
    scans = db.list_full_scans(db_path=db_path)

    # Assertions
    assert len(scans) == 2
    # Check structure (should not contain the heavy JSON)
    first_scan = scans[0]
    assert "summary_id" in first_scan
    assert "timestamp" in first_scan
    assert "analysis_mode" in first_scan
    assert "project_summaries_json" not in first_scan


def test_get_full_scan_by_id_returns_parsed_json(db_path):
    # Save a scan
    analysis_results = {
        "project_summaries": [{"project": "DeepData"}],
        "contributor_profiles": {"dev": {}}
    }
    db.save_full_scan(analysis_results, "advanced", True, db_path=db_path)
    
    # Get ID
    scans = db.list_full_scans(db_path=db_path)
    summary_id = scans[0]["summary_id"]

    # Action
    full_scan = db.get_full_scan_by_id(summary_id, db_path=db_path)

    # Assertions
    assert full_scan is not None
    assert full_scan["summary_id"] == summary_id
    assert full_scan["analysis_mode"] == "advanced"
    assert full_scan["user_consent"] == "Yes"
    
    # Check that JSON was parsed back into a dict
    json_data = full_scan["project_summaries_json"]
    assert isinstance(json_data, dict)
    assert json_data["project_summaries"][0]["project"] == "DeepData"


def test_delete_full_scan_by_id(db_path):
    # Save a scan
    db.save_full_scan({"project_summaries": []}, "basic", True, db_path=db_path)
    scans = db.list_full_scans(db_path=db_path)
    summary_id = scans[0]["summary_id"]

    # Action: Delete
    success = db.delete_full_scan_by_id(summary_id, db_path=db_path)
    assert success is True

    # Verify it's gone
    scans_after = db.list_full_scans(db_path=db_path)
    assert len(scans_after) == 0
    
    # Verify get returns None
    assert db.get_full_scan_by_id(summary_id, db_path=db_path) is None


def test_delete_non_existent_scan_returns_false(db_path):
    # Initialize DB with one record
    db.save_full_scan({"project_summaries": []}, "basic", True, db_path=db_path)
    
    # Try to delete a non-existent ID
    success = db.delete_full_scan_by_id(999, db_path=db_path)
    assert success is False
    
    # Verify original is still there
    scans = db.list_full_scans(db_path=db_path)
    assert len(scans) == 1


def test_save_full_scan_ignores_empty_results(db_path):
    # If project_summaries is missing, it should return without saving
    db.save_full_scan({}, "basic", True, db_path=db_path)
    
    # Check if table exists (it might not if ensure_db_initialized wasn't reached)
    # or if it exists but is empty.
    if not os.path.exists(db_path):
        return

    rows = _fetch_all(db_path, "SELECT * FROM full_scan_summaries")
    assert len(rows) == 0
