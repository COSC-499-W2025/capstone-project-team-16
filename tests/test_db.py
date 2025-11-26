import pytest
import sqlite3
from unittest.mock import patch
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


def test_save_single_record_creates_table_and_defaults(db_path):
    """
    Single record should:
      - Auto-create table
      - Save given fields
      - Apply defaults for missing ones
    """
    data = [{"project": "TestProj", "score": 50}]

    with patch("db.DB_NAME", db_path):
        db.save_results(data)

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
        db.save_results(data)

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
        db.save_results(data)

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
        db.save_results([{"project": "First", "score": 1}])
        assert db.db_initialized is True

        db.save_results([{"project": "Second", "score": 2}])

    rows = _fetch_all(
        db_path,
        "SELECT project_name, score FROM project_summaries ORDER BY project_name"
    )
    assert len(rows) == 2
    result = {name: score for name, score in rows}
    assert result["First"] == 1
    assert result["Second"] == 2
