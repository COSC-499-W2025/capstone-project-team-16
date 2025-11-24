import pytest
import sqlite3
import os
from unittest.mock import patch
import database_manager

@pytest.fixture
def mock_db_path(tmp_path):
    # pytest creates a temp folder 'tmp_path' that is deleted after tests
    db_file = tmp_path / "test_metrics.db"
    return str(db_file)

def test_auto_init_and_save(mock_db_path):
    """
    SCENARIO: First run, no table exists.
    EXPECTED: save_scan_results automatically creates the table and saves data.
    """
    # Patch the DB_NAME so we don't overwrite real skillscope.db
    with patch("database_manager.DB_NAME", str(mock_db_path)):
        
        # ARRANGE: Dummy data
        data = [{"project": "TestProj", "score": 50}]
        
        # ACT: Call save directly 
        database_manager.save_scan_results(data)
        
        # ASSERT: Check if table and data exist
        conn = sqlite3.connect(str(mock_db_path))
        cursor = conn.cursor()
        
        # Check table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_summaries';")
        assert cursor.fetchone() is not None
        
        # Check data
        cursor.execute("SELECT project_name, score FROM project_summaries")
        row = cursor.fetchone()
        assert row[0] == "TestProj"
        assert row[1] == 50
        
        conn.close()

def test_stability_missing_keys(mock_db_path):
    """
    SCENARIO: Input data is missing keys (e.g., upstream code returns incomplete data).
    EXPECTED: Database saves default values (0 or None) instead of crashing.
    """
    with patch("database_manager.DB_NAME", str(mock_db_path)):
        # DATA MISSING 'score' and 'duration_days'
        broken_data = [
            {"project": "BrokenProject", "total_files": 50} 
        ]
        
        # Should NOT raise KeyError
        database_manager.save_scan_results(broken_data)
        
        # Verify defaults were saved
        conn = sqlite3.connect(str(mock_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT project_name, score, duration_days FROM project_summaries")
        row = cursor.fetchone()
        
        assert row[0] == "BrokenProject"
        assert row[1] == 0  # Default integer
        assert row[2] == 0  # Default integer
        conn.close()

def test_data_fidelity_raw_input(mock_db_path):
    """
    SCENARIO: Upstream logic passes raw or unformatted strings (e.g. drive letters).
    EXPECTED: Database records exact input without attempting correction or validation.
    """
    with patch("database_manager.DB_NAME", str(mock_db_path)):
        buggy_data = [
            {"project": "C:", "score": 9000, "total_files": 100}
        ]
        
        database_manager.save_scan_results(buggy_data)
        
        conn = sqlite3.connect(str(mock_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT project_name FROM project_summaries")
        result = cursor.fetchone()[0]
        
        # Assert that the raw input is preserved
        assert result == "C:"
        conn.close()

def test_performance_atomic_transaction(mock_db_path):
    """
    SCENARIO: Saving multiple records.
    EXPECTED: All records are saved in one transaction.
    """
    with patch("database_manager.DB_NAME", str(mock_db_path)):
        bulk_data = [
            {"project": "ProjA", "score": 10},
            {"project": "ProjB", "score": 20},
            {"project": "ProjC", "score": 30}
        ]
        
        database_manager.save_scan_results(bulk_data)
        
        conn = sqlite3.connect(str(mock_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM project_summaries")
        count = cursor.fetchone()[0]
        
        assert count == 3
        conn.close()