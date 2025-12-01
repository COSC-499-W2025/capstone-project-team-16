import json
import sqlite3
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
    data = [{"project": "TestProj", "score": 50}]
    db.save_results(data, user_consent=True, analysis_mode="advanced", db_path=db_path)

    tables = _fetch_all(
        db_path,
        "SELECT name FROM sqlite_master WHERE type='table' AND name='project_summaries';"
    )
    assert tables == [("project_summaries",)]

    rows = _fetch_all(
        db_path,
        """
        SELECT
            project_name, score, total_files, duration_days,
            code_files, test_files, doc_files, design_files,
            languages, frameworks, skills, is_collaborative
        FROM project_summaries
        """
    )
    assert len(rows) == 1
    (
        project_name, score, total_files, duration_days,
        code_files, test_files, doc_files, design_files,
        languages, frameworks, skills, is_collaborative
    ) = rows[0]

    assert project_name == "TestProj"
    assert score == 50
    assert total_files == duration_days == code_files == test_files == doc_files == design_files == 0
    assert languages == frameworks == skills == ""
    assert is_collaborative == "No"


def test_missing_keys_use_defaults(db_path):
    data = [{"project": "Incomplete", "total_files": 5}]
    db.save_results(data, user_consent=False, analysis_mode="basic", db_path=db_path)

    rows = _fetch_all(
        db_path,
        "SELECT project_name, total_files, duration_days, score FROM project_summaries"
    )
    assert len(rows) == 1
    project_name, total_files, duration_days, score = rows[0]
    assert project_name == "Incomplete"
    assert total_files == 5
    assert duration_days == 0
    assert score == 0


def test_multiple_records_persist_correctly(db_path):
    data = [
        {"project": "ProjA", "score": 10, "total_files": 1},
        {"project": "ProjB", "score": 20, "total_files": 2},
        {"project": "ProjC", "score": 30, "total_files": 3},
    ]
    db.save_results(data, user_consent=True, analysis_mode="basic", db_path=db_path)

    rows = _fetch_all(
        db_path,
        "SELECT project_name, score, total_files FROM project_summaries ORDER BY project_name"
    )
    assert len(rows) == 3
    result = {name: (score, total_files) for name, score, total_files in rows}
    assert result["ProjA"] == (10, 1)
    assert result["ProjB"] == (20, 2)
    assert result["ProjC"] == (30, 3)


def test_user_consent_and_analysis_mode_persist(db_path):
    data = [{"project": "ConsentProj", "score": 42}]
    db.save_results(data, user_consent=True, analysis_mode="advanced", db_path=db_path)

    rows = _fetch_all(
        db_path,
        "SELECT project_name, user_consent, analysis_mode FROM project_summaries"
    )
    project_name, consent, mode = rows[0]
    assert project_name == "ConsentProj"
    assert consent == "Yes"
    assert mode == "advanced"


# ----------------------------------------------------------------------
# Generic helper tests
# ----------------------------------------------------------------------

def test_get_all_and_get_by_id_helpers(db_path):
    data = [{"project": "ProjA", "score": 10}, {"project": "ProjB", "score": 20}]
    db.save_results(data, user_consent=True, analysis_mode="basic", db_path=db_path)

    summaries = db.get_all_summaries(db_path=db_path)
    assert len(summaries) == 2

    proj_a_id = next(s["id"] for s in summaries if s["project_name"] == "ProjA")
    proj_a = db.get_summary_by_id(proj_a_id, db_path=db_path)
    assert proj_a["project_name"] == "ProjA"
    assert proj_a["score"] == 10
    assert proj_a["user_consent"] == "Yes"
    assert proj_a["analysis_mode"] == "basic"


def test_update_summary_helper(db_path):
    data = [{"project": "ToUpdate", "score": 50}]
    db.save_results(data, user_consent=False, analysis_mode="basic", db_path=db_path)
    summary_id = db.get_all_summaries(db_path=db_path)[0]["id"]

    updated = db.update_summary(summary_id, {"score": 99, "analysis_mode": "advanced"}, db_path=db_path)
    assert updated
    refreshed = db.get_summary_by_id(summary_id, db_path=db_path)
    assert refreshed["score"] == 99
    assert refreshed["analysis_mode"] == "advanced"
    assert refreshed["project_name"] == "ToUpdate"


def test_delete_summary_helper(db_path):
    data = [{"project": "ToDelete", "score": 1}]
    db.save_results(data, user_consent=True, analysis_mode="basic", db_path=db_path)
    summary_id = db.get_all_summaries(db_path=db_path)[0]["id"]

    deleted = db.delete_summary(summary_id, db_path=db_path)
    assert deleted
    assert db.get_all_summaries(db_path=db_path) == []


def test_search_by_project_name_helper(db_path):
    data = [
        {"project": "API Server", "score": 10},
        {"project": "Frontend UI", "score": 20},
        {"project": "Another API Tool", "score": 30},
    ]
    db.save_results(data, user_consent=True, analysis_mode="advanced", db_path=db_path)

    results = db.search_by_project_name("API", db_path=db_path)
    names = {r["project_name"] for r in results}
    assert names == {"API Server", "Another API Tool"}


# ----------------------------------------------------------------------
# Requirement-specific helpers
# ----------------------------------------------------------------------

def test_store_project_insights_inserts_full_row(db_path):
    project = {"project": "InsightsProj", "score": 88, "total_files": 12, "languages": "Python"}
    user_id = "user-123"
    project_id = "proj-abc"
    file_tree = {"root": ["main.py", "README.md"]}
    resume_bullets = ["Built analysis pipeline", "Improved performance by 20%"]

    db.store_project_insights(
        project=project,
        user_id=user_id,
        project_id=project_id,
        user_consent=True,
        analysis_mode="advanced",
        file_tree=file_tree,
        resume_bullets=resume_bullets,
        db_path=db_path,
    )

    rows = _fetch_all(db_path, "SELECT project_name, user_id, project_id, analysis_data, file_tree, resume_bullets, user_consent, analysis_mode, score FROM project_summaries")
    (
        project_name, uid, pid, analysis_data_str,
        file_tree_str, resume_bullets_str, consent, mode, score
    ) = rows[0]

    assert project_name == "InsightsProj"
    assert uid == user_id
    assert pid == project_id
    assert consent == "Yes"
    assert mode == "advanced"
    assert score == 88
    assert json.loads(analysis_data_str)["project"] == "InsightsProj"
    assert json.loads(file_tree_str) == file_tree
    assert json.loads(resume_bullets_str) == resume_bullets


def test_list_project_summaries_filters_by_user(db_path):
    db.save_results([{"project": "User1Proj1", "score": 10}, {"project": "User1Proj2", "score": 20}],
                    user_consent=True, analysis_mode="basic", user_id="user1", project_id="proj-u1-1", db_path=db_path)
    db.save_results([{"project": "User2Proj1", "score": 30}],
                    user_consent=True, analysis_mode="advanced", user_id="user2", project_id="proj-u2-1", db_path=db_path)

    all_summaries = db.list_project_summaries(db_path=db_path)
    assert len(all_summaries) == 3

    user1_summaries = db.list_project_summaries(user_id="user1", db_path=db_path)
    assert {s["project_name"] for s in user1_summaries} == {"User1Proj1", "User1Proj2"}

    user2_summaries = db.list_project_summaries(user_id="user2", db_path=db_path)
    assert user2_summaries[0]["project_name"] == "User2Proj1"


def test_get_resume_bullets_returns_structured_items(db_path):
    db.store_project_insights({"project": "ProjA", "score": 10}, "user1", "projA", True, "basic", {}, ["A bullet 1", "A bullet 2"], db_path=db_path)
    db.store_project_insights({"project": "ProjB", "score": 20}, "user1", "projB", True, "advanced", {}, ["B bullet 1"], db_path=db_path)

    bullets = db.get_resume_bullets(user_id="user1", db_path=db_path)
    assert len(bullets) == 3
    proj_ids = {b["project_id"] for b in bullets}
    assert proj_ids == {"projA", "projB"}


def test_delete_project_insights_by_project_id(db_path):
    db.store_project_insights({"project": "ProjA", "score": 10}, "user1", "projA", True, "basic", {}, ["A bullet"], db_path=db_path)
    db.store_project_insights({"project": "ProjB", "score": 20}, "user1", "projB", True, "advanced", {}, ["B bullet"], db_path=db_path)

    deleted = db.delete_project_insights("projA", db_path=db_path)
    assert deleted is True

    remaining = db.get_all_summaries(db_path=db_path)
    assert len(remaining) == 1
    assert remaining[0]["project_id"] == "projB"

    deleted_again = db.delete_project_insights("projA", db_path=db_path)
    assert deleted_again is False
