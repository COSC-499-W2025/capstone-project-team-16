import pytest
from unittest.mock import patch, MagicMock
from metadata_extractor import detailed_extraction

def test_detailed_extraction_valid_repo(capsys):
    """
    SCENARIO: Entry is a valid repository with info returned by analyze_repo_type
    EXPECTED: Entry is updated with repo info and prints success message
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
        "branch_count": 1,
        "has_merges": False,
        "project_type": "individual"
    }

    with patch("metadata_extractor.analyze_repo_type", return_value=mock_repo_info):
        detailed_extraction(extracted_data)

    entry = extracted_data[0]
    assert entry["repo_name"] == "repo"
    assert entry["repo_root"] == "/path/to/repo"
    assert entry["authors"] == ["author1@example.com"]
    assert entry["branch_count"] == 1
    assert entry["has_merges"] is False
    assert entry["project_type"] == "individual"

    captured = capsys.readouterr()
    assert "Repo analysis succeeded:" in captured.out
    assert "Name: repo" in captured.out

def test_detailed_extraction_invalid_repo(capsys):
    """
    SCENARIO: Entry is a repository, but analyze_repo_type fails (returns None)
    EXPECTED: Entry remains unchanged and prints skipping message
    """
    extracted_data = [
        {
            "filename": "/path/to/badrepo/.git/",
            "extension": ".git",
            "isFile": False,
            "category": "repository"
        }
    ]

    with patch("metadata_extractor.analyze_repo_type", return_value=None):
        detailed_extraction(extracted_data)

    entry = extracted_data[0]
    assert "repo_name" not in entry
    assert "repo_root" not in entry

    captured = capsys.readouterr()
    assert "Skipping invalid or failed repo" in captured.out

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

    detailed_extraction(extracted_data)

    entry = extracted_data[0]
    assert entry["filename"] == "/path/to/file.txt"
    captured = capsys.readouterr()
    assert "Repo analysis" not in captured.out