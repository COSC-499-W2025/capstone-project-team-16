import pytest
from unittest.mock import patch, MagicMock
from metadata_extractor import detailed_extraction

def test_detailed_extraction_valid_repo():
    """
    SCENARIO: Entry is a valid repository with info returned by analyze_repo_type
    EXPECTED: Entry is added to projects with correct metadata
    """
    extracted_data = [
        {
            "filename": "/path/to/repo/.git/",
            "extension": ".git",
            "isFile": False,
            "category": "repository"
        }
    ]

    mock_repo_info = {
        "is_valid": True,
        "repo_name": "repo",
        "repo_root": "/path/to/repo",
        "authors": ["author1@example.com"],
        "contributors": ["author1@example.com"],
        "branch_count": 1,
        "has_merges": False,
        "project_type": "individual",
        "duration_days": 10,
        "commit_frequency": 2
    }

    # Minimal advanced options
    advanced_options = {
        "framework_scan": False     # doesn’t matter for this test
    }

    with patch("metadata_extractor.analyze_repo_type", return_value=mock_repo_info):
        result = detailed_extraction(extracted_data, advanced_options)

    project = result["projects"][0]

    assert project["repo_name"] == "repo"
    assert project["repo_root"] == "/path/to/repo"
    assert project["authors"] == ["author1@example.com"]
    assert project["contributors"] == ["author1@example.com"]
    assert project["branch_count"] == 1
    assert project["has_merges"] is False
    assert project["project_type"] == "individual"
    assert project["duration_days"] == 10
    assert project["commit_frequency"] == 2



def test_detailed_extraction_non_repo(capsys):
    """
    SCENARIO: Entry is not a repository
    EXPECTED: Entry remains unchanged, no repo analysis is printed
    """
    extracted_data = [
        {
            "filename": "/path/to/file.txt",
            "extension": ".txt",
            "isFile": True,
            "category": "text"
        }
    ]

    advanced_options = {"framework_scan": False}

    detailed_extraction(extracted_data, advanced_options)

    # Entry should remain unchanged
    entry = extracted_data[0]
    assert entry["filename"] == "/path/to/file.txt"

    # No repo analysis should be printed
    captured = capsys.readouterr()
    assert "Repo analysis" not in captured.out
