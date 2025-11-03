import json
import os
from unittest.mock import patch, mock_open
from metadata_extractor import load_filters, base_extraction


# ---------- load_filters TESTS ----------

def test_load_filters_returns_dict(tmp_path):
    """SCENARIO: Valid JSON file provided
       EXPECTED: Returns dictionary mapping extensions to categories"""
    json_data = {
        "categories": {
            "source_code": [".py", ".js"],
            "documentation": [".txt"]
        }
    }
    test_file = tmp_path / "extractor_filters.json"
    test_file.write_text(json.dumps(json_data))

    result = load_filters(path=str(test_file))
    assert result == {
        ".py": "source_code",
        ".js": "source_code",
        ".txt": "documentation"
    }


def test_load_filters_handles_missing_file(tmp_path, capsys):
    """SCENARIO: JSON file does not exist
       EXPECTED: Prints warning and returns empty dict"""
    result = load_filters(path=str(tmp_path / "nonexistent.json"))
    captured = capsys.readouterr()
    assert result == {}
    assert "Filter file not found" in captured.out


def test_load_filters_invalid_json(tmp_path, capsys):
    """SCENARIO: JSON file is corrupted
       EXPECTED: Prints warning and returns empty dict"""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ invalid json")
    result = load_filters(path=str(bad_json))
    captured = capsys.readouterr()
    assert result == {}
    assert "Error decoding JSON" in captured.out


def test_load_filters_unexpected_error(monkeypatch, capsys):
    """SCENARIO: Unexpected error (e.g., permission error)
       EXPECTED: Prints warning and returns empty dict"""
    def mock_open(*args, **kwargs):
        raise PermissionError("No permission")
    
    monkeypatch.setattr("builtins.open", mock_open)
    result = load_filters(path="extractor_filters.json")
    captured = capsys.readouterr()
    assert result == {}
    assert "Unexpected error loading filters" in captured.out

# ---------- base_extraction TESTS ----------

@patch("metadata_extractor.load_filters")
def test_base_extraction_categorizes_files(mock_load_filters):
    """SCENARIO: Files are correctly categorized using filter map
       EXPECTED: Returns extracted data list with correct categories"""
    mock_load_filters.return_value = {
        ".py": "source_code",
        ".txt": "documentation"
    }

    file_list = [
        {"filename": "script.py", "size": 100, "last_modified": (2025, 1, 1, 12, 0, 0)},
        {"filename": "readme.txt", "size": 200, "last_modified": (2025, 1, 2, 12, 0, 0)}
    ]

    result = base_extraction(file_list)
    assert len(result) == 2
    assert result[0]["category"] == "source_code"
    assert result[0]["isFile"] is True
    assert result[1]["category"] == "documentation"


@patch("metadata_extractor.load_filters")
def test_base_extraction_handles_folders(mock_load_filters):
    """SCENARIO: Folder is detected
       EXPECTED: isFile is False and category is uncategorized (or matching folder)"""
    mock_load_filters.return_value = {"myfolder": "repository"}

    file_list = [
        {"filename": "myfolder/", "size": 0, "last_modified": (2025, 1, 1, 12, 0, 0)}
    ]

    result = base_extraction(file_list)
    assert result[0]["isFile"] is False
    assert result[0]["category"] in ["repository", "uncategorized"]


@patch("metadata_extractor.load_filters")
def test_base_extraction_uncategorized(mock_load_filters):
    """SCENARIO: Unknown extension
       EXPECTED: Category set to 'uncategorized'"""
    mock_load_filters.return_value = {".py": "source_code"}

    file_list = [
        {"filename": "unknown.xyz", "size": 123, "last_modified": (2025, 1, 1, 12, 0, 0)}
    ]

    result = base_extraction(file_list)
    assert result[0]["category"] == "uncategorized"
    assert result[0]["isFile"] is True


@patch("metadata_extractor.load_filters", return_value=None)
def test_base_extraction_no_filters(mock_load_filters):
    """SCENARIO: load_filters returns None
       EXPECTED: Prints error message instead of crashing"""
    file_list = [{"filename": "test.py", "size": 10, "last_modified": (2025, 1, 1, 0, 0, 0)}]

    # No exception should occur even if filters are None
    base_extraction(file_list)
