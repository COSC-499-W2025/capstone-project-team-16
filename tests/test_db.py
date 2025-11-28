import json
import sqlite3
from unittest.mock import patch

import pytest
import db


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
# Original-style tests (updated to pass user_consent + analysis_mode)
# ----------------------------------------------------------------------

def test_save_single_record_creates_table_and_defaults(db_path):
    """
    Single record should:
      - Auto-create table
      - Save given fields
      - Apply defaults for missing ones
    """
    data = [{"project": "TestProj", "score": 50}]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=True, analysis_mode="advanced")

    # Table exists?
    tables = _fetch_all(
        db_path,
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='project_summaries';"
    )
    assert tables == [("project_summaries",)]

    # Row content (only one row expected)
    rows = _fetch_all(
        db_path,
        """
        SELECT
            project_name,
            score,
            total_files,
            duration_days,
            code_files,
            test_files,
            doc_files,
            design_files,
            languages,
            frameworks,
            skills,
            is_collaborative
        FROM project_summaries
        """
    )
    assert len(rows) == 1

    (
        project_name,
        score,
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
    ) = rows[0]

    assert project_name == "TestProj"
    assert score == 50

    # Numeric defaults
    assert total_files == 0
    assert duration_days == 0
    assert code_files == 0
    assert test_files == 0
    assert doc_files == 0
    assert design_files == 0

    # Text defaults
    assert languages == ""
    assert frameworks == ""
    assert skills == ""
    assert is_collaborative == "No"


def test_missing_keys_use_defaults(db_path):
    """
    Missing keys should not crash and should use default values.
    """
    data = [{"project": "Incomplete", "total_files": 5}]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=False, analysis_mode="basic")

    rows = _fetch_all(
        db_path,
        """
        SELECT
            project_name,
            total_files,
            duration_days,
            score
        FROM project_summaries
        """
    )
    assert len(rows) == 1

    project_name, total_files, duration_days, score = rows[0]
    assert project_name == "Incomplete"
    assert total_files == 5          # Provided value
    assert duration_days == 0        # Default
    assert score == 0                # Default


def test_multiple_records_persist_correctly(db_path):
    """
    Multiple records should all be saved with correct values.
    """
    data = [
        {"project": "ProjA", "score": 10, "total_files": 1},
        {"project": "ProjB", "score": 20, "total_files": 2},
        {"project": "ProjC", "score": 30, "total_files": 3},
    ]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=True, analysis_mode="basic")

    rows = _fetch_all(
        db_path,
        """
        SELECT project_name, score, total_files
        FROM project_summaries
        ORDER BY project_name
        """
    )
    assert len(rows) == 3

    # Turn into a dict for quick lookup
    result = {name: (score, total_files) for name, score, total_files in rows}
    assert result["ProjA"] == (10, 1)
    assert result["ProjB"] == (20, 2)
    assert result["ProjC"] == (30, 3)


def test_db_initialized_flag_behavior(db_path):
    """
    db_initialized should:
      - Start False
      - Become True after first call
      - Still allow subsequent calls to write data
    """
    assert hasattr(db, "db_initialized")
    assert db.db_initialized is False

    with patch("db.DB_NAME", db_path):
        db.save_results([{"project": "First", "score": 1}], True, "basic")
        assert db.db_initialized is True

        db.save_results([{"project": "Second", "score": 2}], False, "advanced")

    rows = _fetch_all(
        db_path,
        "SELECT project_name, score FROM project_summaries ORDER BY project_name"
    )
    assert len(rows) == 2
    result = {name: score for name, score in rows}
    assert result["First"] == 1
    assert result["Second"] == 2


def test_user_consent_and_analysis_mode_persist(db_path):
    """
    user_consent and analysis_mode should be stored correctly.
    """
    data = [{"project": "ConsentProj", "score": 42}]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=True, analysis_mode="advanced")

    rows = _fetch_all(
        db_path,
        """
        SELECT project_name, user_consent, analysis_mode
        FROM project_summaries
        """
    )
    assert len(rows) == 1
    project_name, consent, mode = rows[0]

    assert project_name == "ConsentProj"
    assert consent == "Yes"
    assert mode == "advanced"


# ----------------------------------------------------------------------
# Tests for generic helpers (get/update/delete/search)
# ----------------------------------------------------------------------

def test_get_all_and_get_by_id_helpers(db_path):
    """
    get_all_summaries and get_summary_by_id should return dicts
    including the new fields.
    """
    data = [
        {"project": "ProjA", "score": 10},
        {"project": "ProjB", "score": 20},
    ]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=True, analysis_mode="basic")

        summaries = db.get_all_summaries()
        assert len(summaries) == 2

        ids = {s["project_name"]: s["id"] for s in summaries}
        proj_a_id = ids["ProjA"]

        proj_a = db.get_summary_by_id(proj_a_id)
        assert proj_a is not None
        assert proj_a["project_name"] == "ProjA"
        assert proj_a["score"] == 10
        assert proj_a["user_consent"] == "Yes"
        assert proj_a["analysis_mode"] == "basic"


def test_update_summary_helper(db_path):
    """
    update_summary should update only the specified fields.
    """
    data = [{"project": "ToUpdate", "score": 50}]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=False, analysis_mode="basic")
        summaries = db.get_all_summaries()
        summary_id = summaries[0]["id"]

        updated = db.update_summary(summary_id, {
            "score": 99,
            "analysis_mode": "advanced",
        })
        assert updated

        refreshed = db.get_summary_by_id(summary_id)
        assert refreshed["score"] == 99
        assert refreshed["analysis_mode"] == "advanced"
        # unchanged
        assert refreshed["project_name"] == "ToUpdate"


def test_delete_summary_helper(db_path):
    """
    delete_summary should remove the row and return True.
    """
    data = [{"project": "ToDelete", "score": 1}]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=True, analysis_mode="basic")
        summaries = db.get_all_summaries()
        summary_id = summaries[0]["id"]

        deleted = db.delete_summary(summary_id)
        assert deleted

        remaining = db.get_all_summaries()
        assert remaining == []


def test_search_by_project_name_helper(db_path):
    """
    search_by_project_name should use LIKE and match partial names.
    """
    data = [
        {"project": "API Server", "score": 10},
        {"project": "Frontend UI", "score": 20},
        {"project": "Another API Tool", "score": 30},
    ]

    with patch("db.DB_NAME", db_path):
        db.save_results(data, user_consent=True, analysis_mode="advanced")

        # Exact-ish match
        results = db.search_by_project_name("API Server")
        assert len(results) == 1
        assert results[0]["project_name"] == "API Server"

        # Partial match
        results_partial = db.search_by_project_name("API")
        names = {r["project_name"] for r in results_partial}
        assert names == {"API Server", "Another API Tool"}


# ----------------------------------------------------------------------
# Tests for requirement-specific helpers
# ----------------------------------------------------------------------

def test_store_project_insights_inserts_full_row(db_path):
    """
    store_project_insights should save:
      - project_id, user_id
      - analysis_data JSON
      - file_tree JSON
      - resume_bullets JSON
    """
    project = {
        "project": "InsightsProj",
        "score": 88,
        "total_files": 12,
        "languages": "Python",
    }
    user_id = "user-123"
    project_id = "proj-abc"
    file_tree = {"root": ["main.py", "README.md"]}
    resume_bullets = ["Built analysis pipeline", "Improved performance by 20%"]

    with patch("db.DB_NAME", db_path):
        db.store_project_insights(
            project=project,
            user_id=user_id,
            project_id=project_id,
            user_consent=True,
            analysis_mode="advanced",
            file_tree=file_tree,
            resume_bullets=resume_bullets,
        )

    rows = _fetch_all(
        db_path,
        """
        SELECT
            project_name,
            user_id,
            project_id,
            analysis_data,
            file_tree,
            resume_bullets,
            user_consent,
            analysis_mode,
            score
        FROM project_summaries
        """
    )
    assert len(rows) == 1

    (
        project_name,
        uid,
        pid,
        analysis_data_str,
        file_tree_str,
        resume_bullets_str,
        consent,
        mode,
        score,
    ) = rows[0]

    assert project_name == "InsightsProj"
    assert uid == user_id
    assert pid == project_id
    assert consent == "Yes"
    assert mode == "advanced"
    assert score == 88

    analysis_data = json.loads(analysis_data_str)
    assert analysis_data["project"] == "InsightsProj"
    assert analysis_data["score"] == 88

    file_tree_obj = json.loads(file_tree_str)
    assert file_tree_obj == file_tree

    resume_bullets_obj = json.loads(resume_bullets_str)
    assert resume_bullets_obj == resume_bullets


def test_list_project_summaries_filters_by_user(db_path):
    """
    list_project_summaries should return portfolio-style summaries,
    optionally filtered by user_id.
    """
    data_user1 = [
        {"project": "User1Proj1", "score": 10},
        {"project": "User1Proj2", "score": 20},
    ]
    data_user2 = [
        {"project": "User2Proj1", "score": 30},
    ]

    with patch("db.DB_NAME", db_path):
        # user1
        db.save_results(
            data_user1,
            user_consent=True,
            analysis_mode="basic",
            user_id="user1",
            project_id="proj-u1-1",  # will be overridden per row if project dict has its own id, but fine here
        )
        # user2
        db.save_results(
            data_user2,
            user_consent=True,
            analysis_mode="advanced",
            user_id="user2",
            project_id="proj-u2-1",
        )

        all_summaries = db.list_project_summaries()
        assert len(all_summaries) == 3

        user1_summaries = db.list_project_summaries(user_id="user1")
        assert len(user1_summaries) == 2
        assert {s["project_name"] for s in user1_summaries} == {
            "User1Proj1",
            "User1Proj2",
        }

        user2_summaries = db.list_project_summaries(user_id="user2")
        assert len(user2_summaries) == 1
        assert user2_summaries[0]["project_name"] == "User2Proj1"


def test_get_resume_bullets_returns_structured_items(db_path):
    """
    get_resume_bullets should flatten stored JSON arrays into structured
    bullet records with project_id, user_id, project_name, and bullet text.
    """
    project_a = {"project": "ProjA", "score": 10}
    project_b = {"project": "ProjB", "score": 20}

    with patch("db.DB_NAME", db_path):
        db.store_project_insights(
            project=project_a,
            user_id="user1",
            project_id="projA",
            user_consent=True,
            analysis_mode="basic",
            file_tree={},
            resume_bullets=["A bullet 1", "A bullet 2"],
        )
        db.store_project_insights(
            project=project_b,
            user_id="user1",
            project_id="projB",
            user_consent=True,
            analysis_mode="advanced",
            file_tree={},
            resume_bullets=["B bullet 1"],
        )

        bullets = db.get_resume_bullets(user_id="user1")
        assert len(bullets) == 3

        # Check structure
        for b in bullets:
            assert "project_id" in b
            assert "user_id" in b
            assert "project_name" in b
            assert "bullet" in b
            assert b["user_id"] == "user1"

        proj_ids = {b["project_id"] for b in bullets}
        assert proj_ids == {"projA", "projB"}


def test_delete_project_insights_by_project_id(db_path):
    """
    delete_project_insights should delete all rows for a given project_id
    and return True if something was deleted.
    """
    with patch("db.DB_NAME", db_path):
        db.store_project_insights(
            project={"project": "ProjA", "score": 10},
            user_id="user1",
            project_id="projA",
            user_consent=True,
            analysis_mode="basic",
            file_tree={},
            resume_bullets=["A bullet"],
        )
        db.store_project_insights(
            project={"project": "ProjB", "score": 20},
            user_id="user1",
            project_id="projB",
            user_consent=True,
            analysis_mode="advanced",
            file_tree={},
            resume_bullets=["B bullet"],
        )

        # Ensure two rows exist
        all_rows_before = db.get_all_summaries()
        assert len(all_rows_before) == 2

        # Delete projA
        deleted = db.delete_project_insights("projA")
        assert deleted is True

        remaining = db.get_all_summaries()
        assert len(remaining) == 1
        assert remaining[0]["project_id"] == "projB"

        # Deleting non-existent project should return False
        deleted_again = db.delete_project_insights("projA")
        assert deleted_again is False