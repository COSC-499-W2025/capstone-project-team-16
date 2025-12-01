import pytest
import json
import os
from unittest.mock import patch, mock_open
from metadata_extractor import load_filters, base_extraction


# ---------- load_filters TESTS ----------

def test_load_filters_returns_dict(tmp_path):
    """SCENARIO: Valid JSON file provided
       EXPECTED: Returns extension→category AND extension→language dicts"""
    
    json_data = {
        "categories": {
            "source_code": [".py", ".js"],
            "documentation": [".txt"]
        },
        "languages": {
            ".py": "Python",
            ".js": "JavaScript",
            ".txt": "Text"
        }
    }

    test_file = tmp_path / "extractor_filters.json"
    test_file.write_text(json.dumps(json_data))

    # Load filter dictionary
    filters = load_filters(filename=str(test_file))
    extensions = filters["extensions"]
    languages = filters["languages"]

    # Check extension→category mapping
    assert extensions == {
        ".py": "source_code",
        ".js": "source_code",
        ".txt": "documentation"
    }

    # Check extension→language mapping
    assert languages == {
        ".py": "Python",
        ".js": "JavaScript",
        ".txt": "Text"
    }


def test_load_filters_handles_missing_file(tmp_path, capsys):
    """SCENARIO: JSON file does not exist
       EXPECTED: Prints warning and returns empty dicts"""
    
    filters = load_filters(filename=str(tmp_path / "nonexistent.json"))
    extensions = filters.get("extensions", {})
    languages = filters.get("languages", {})
    
    captured = capsys.readouterr()
    
    # Both dictionaries should be empty
    assert extensions == {}
    assert languages == {}
    
    # Warning message should appear
    assert "Filter file not found" in captured.out


def test_load_filters_invalid_json(tmp_path, capsys):
    """SCENARIO: JSON file is corrupted
       EXPECTED: Prints warning and returns empty dicts"""
    
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ invalid json")
    
    filters = load_filters(filename=str(bad_json))
    extensions = filters.get("extensions", {})
    languages = filters.get("languages", {})
    
    captured = capsys.readouterr()
    
    # Both dictionaries should be empty
    assert extensions == {}
    assert languages == {}
    
    # Warning message should appear
    assert "Error decoding JSON" in captured.out


def test_load_filters_unexpected_error(monkeypatch, capsys):
    """SCENARIO: Unexpected error (e.g., permission error)
       EXPECTED: Prints warning and returns empty dicts"""
    
    def mock_open(*args, **kwargs):
        raise PermissionError("No permission")
    
    monkeypatch.setattr("builtins.open", mock_open)
    
    filters = load_filters(filename="extractor_filters.json")
    extensions = filters.get("extensions", {})
    languages = filters.get("languages", {})
    
    captured = capsys.readouterr()
    
    # Both dictionaries should be empty
    assert extensions == {}
    assert languages == {}
    
    # Warning message should appear
    assert "Unexpected error loading filters" in captured.out


# ---------- base_extraction TESTS ----------

@patch("metadata_extractor.load_filters")
def test_base_extraction_categorizes_files(mock_load_filters):
    """SCENARIO: Files are correctly categorized using filter map
       EXPECTED: Returns extracted data list with correct categories and languages"""
    
    mock_load_filters.return_value = {
        "extensions": {
            ".py": "source_code",
            ".txt": "documentation"
        },
        "languages": {
            ".py": "Python",
            ".txt": "undefined"
        },
        "frameworks": {}   # needed because your function accesses this key
    }

    file_list = [
        {"filename": "script.py", "size": 100, "last_modified": (2025, 1, 1, 12, 0, 0), "isFile": True},
        {"filename": "readme.txt", "size": 200, "last_modified": (2025, 1, 2, 12, 0, 0), "isFile": True}
    ]

    result = base_extraction(file_list, mock_load_filters.return_value)
    
    assert len(result) == 2

    # Check first file
    assert result[0]["category"] == "source_code"
    assert result[0]["isFile"] is True
    assert result[0]["language"] == "Python"

    # Check second file
    assert result[1]["category"] == "documentation"
    assert result[1]["isFile"] is True
    assert result[1]["language"] == ""





@patch("metadata_extractor.load_filters")
def test_base_extraction_handles_folders(mock_load_filters):
    """SCENARIO: Folder is detected
       EXPECTED: isFile is False and category is uncategorized (or matching folder)"""
    
    mock_load_filters.return_value = {
        "extensions": {"myfolder": "repository"},
        "languages": {}
    }

    file_list = [
        {
            "filename": "myfolder/",
            "size": 0,
            "last_modified": (2025, 1, 1, 12, 0, 0),
            "isFile": False   # REQUIRED
        }
    ]

    result = base_extraction(file_list, mock_load_filters.return_value)

    assert result[0]["isFile"] is False
    assert result[0]["category"] in ["repository", "uncategorized"]
    assert result[0]["language"] == ""



@patch("metadata_extractor.load_filters")
def test_base_extraction_uncategorized(mock_load_filters):
    """SCENARIO: Unknown extension
       EXPECTED: Category set to 'uncategorized' and language empty"""
    
    mock_load_filters.return_value = {
        "extensions": {".py": "source_code"},
        "languages": {".py": "Python"}
    }

    file_list = [
        {"filename": "unknown.xyz", "size": 123, "last_modified": (2025, 1, 1, 12, 0, 0), "isFile": True}
    ]

    result = base_extraction(file_list, mock_load_filters.return_value)

    assert result[0]["category"] == "uncategorized"
    assert result[0]["isFile"] is True
    assert result[0]["language"] == ""  # unknown extensions → empty string




@patch("metadata_extractor.load_filters", return_value={"extensions": {}, "languages": {}})
def test_base_extraction_no_filters(mock_load_filters, capsys):
    """SCENARIO: load_filters returns empty dicts
       EXPECTED: Prints error message instead of crashing"""
    
    file_list = [{"filename": "test.py", "size": 10, "last_modified": (2025, 1, 1, 0, 0, 0)}]

    # Call base_extraction
    result = base_extraction(file_list, mock_load_filters.return_value)

    # Capture printed output
    captured = capsys.readouterr()
    assert "Unable to load filters" in captured.out

    # Since filters are empty, no files should be extracted
    assert result == []

