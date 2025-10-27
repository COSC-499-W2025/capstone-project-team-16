import pytest
from unittest.mock import patch
from file_parser import (get_input_file_path, check_file_validity,
    extract_project_metadata,
    get_file_metadata,
    categorize_file,
    detect_source_code_data)

# Helper Function to Create Test Zip Files
def make_test_zip(tmp_path, files):
    """
    Creates a temporary zip file with given file structure.
    `files` is a dict: { "path/in/zip.txt": "file contents" }
    """
    zip_path = tmp_path / "test_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    return zip_path



def test_valid_path_first_try(monkeypatch, capsys):
    """
        SCENARIO: User enters a valid zip path immediately
        EXPECTED: Function returns that exact path
        
        WHAT WE'RE TESTING:
        - Does the function accept valid input?
        - Does it return the correct path?
        - Does it exit (not loop forever)?
    """
    test_path = '/valid/path/project.zip'
    monkeypatch.setattr('builtins.input', lambda _: test_path)
    
    # Mock check_file_validity to return a list of file info dicts
    mock_file_tree = [
        {"filename": "file1.txt", "size": 1024, "date_time": (2024, 1, 1, 12, 0, 0)},
        {"filename": "file2.py", "size": 2048, "date_time": (2024, 1, 2, 13, 0, 0)}
    ]
    
    with patch('file_parser.check_file_validity', return_value=mock_file_tree):
        # ACT
        result = get_input_file_path()
        
        # ASSERT
        assert result == test_path
        
        # Verify files were printed
        captured = capsys.readouterr()
        assert "Valid zip file detected" in captured.out
        assert "file1.txt" in captured.out
        assert "1024" in captured.out
        assert "file2.py" in captured.out
        assert "2048" in captured.out





def test_empty_input_then_valid_path(monkeypatch, capsys):
    """
        SCENARIO: User presses Enter without typing, then enters valid path
        EXPECTED: Function loops back and asks again, then returns valid path
        
        WHAT WE'RE TESTING:
        - Does the function handle empty input?
        - Does it print an error message?
        - Does it loop and ask again?
        - Does it eventually accept valid input?
    """

    user_inputs = iter([
        '',                           # First attempt: just press Enter
        '/valid/path/project.zip'     # Second attempt: valid path
    ])
    
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    # Mock file tree for valid zip
    mock_file_tree = [
        {"filename": "readme.txt", "size": 512, "date_time": (2024, 1, 1, 12, 0, 0)}
    ]
    
    with patch('file_parser.check_file_validity', return_value=mock_file_tree):
        # ACT
        result = get_input_file_path()
        
        # ASSERT
        assert result == '/valid/path/project.zip'
        
        # Check messages
        captured = capsys.readouterr()
        assert "No path was entered." in captured.out
        assert "Valid zip file detected" in captured.out






def test_invalid_path_then_valid_path(monkeypatch, capsys):
    """
        SCENARIO: User enters invalid path and then a valid one
        EXPECTED: Function loops back and asks again, then returns valid path
        
        WHAT WE'RE TESTING:
        - Does the function handle empty input?
        - Does it print an error message?
        - Does it loop and ask again?
        - Does it eventually accept valid input?
    """

    user_inputs = iter([
        '/invalid/path.zip',      # First attempt: will return None (invalid)
        '/valid/path.zip'         # Second attempt: will return list (valid)
    ])
    
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    # Mock file tree for valid zip
    mock_file_tree = [
        {"filename": "main.py", "size": 2048, "date_time": (2024, 1, 1, 12, 0, 0)}
    ]
    
    # Mock validation: None for invalid, list for valid
    with patch('file_parser.check_file_validity', side_effect=[None, mock_file_tree]):
        # ACT
        result = get_input_file_path()
        
        # ASSERT
        assert result == '/valid/path.zip'
        
        # Verify both messages appeared
        captured = capsys.readouterr()
        assert "Invalid zip file detected" in captured.out  # From first attempt
        assert "Valid zip file detected" in captured.out    # From second attempt





def test_multiple_invalid_path_then_valid_path(monkeypatch, capsys):
    """
        SCENARIO: User enters multiple invalid paths and then a valid one
        EXPECTED: Function loops back and asks again until a valid path is entered then returns valid path
        
        WHAT WE'RE TESTING:
        - Does the function persist through multiple failures?
        - Does it eventually accept valid input?
        - Does it handle a mix of empty and invalid inputs?
    """

    # ARRANGE - User tries 4 times before success
    user_inputs = iter([
        '',                          # Attempt 1: Empty (doesn't call check_file_validity)
        '/bad/path.txt',            # Attempt 2: Invalid (returns None)
        '/nonexistent.zip',         # Attempt 3: Invalid (returns None)
        '/finally/valid.zip'        # Attempt 4: Valid (returns list)
    ])
    
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    # Mock file tree for valid zip
    mock_file_tree = [
        {"filename": "success.txt", "size": 100, "date_time": (2024, 1, 1, 12, 0, 0)}
    ]
    
    # Mock validation: None, None, then list
    # Note: Empty string (attempt 1) doesn't call check_file_validity
    with patch('file_parser.check_file_validity', side_effect=[None, None, mock_file_tree]):
        # ACT
        result = get_input_file_path()
        
        # ASSERT
        assert result == '/finally/valid.zip'
        
        # Verify all messages appeared
        captured = capsys.readouterr()
        assert "No path was entered." in captured.out
        assert captured.out.count("Invalid zip file detected") == 2  # Two invalid attempts
        assert "Valid zip file detected" in captured.out

def test_file_tree_assignment_and_printing(monkeypatch, capsys):
    """
    SCENARIO: Valid zip with multiple files
    EXPECTED: All files are printed with their sizes
    
    WHAT WE'RE TESTING:
    - Does the walrus operator correctly capture the file tree?
    - Are all files in the list printed?
    - Are filenames and sizes displayed correctly?
    
    This tests the walrus operator: if (file_tree := check_file_validity(zip_path)):
    """
    # ARRANGE
    monkeypatch.setattr('builtins.input', lambda _: '/test/archive.zip')
    
    # Mock file tree with multiple files
    mock_file_tree = [
        {"filename": "docs/readme.md", "size": 1024, "date_time": (2024, 1, 1, 12, 0, 0)},
        {"filename": "src/main.py", "size": 2048, "date_time": (2024, 1, 2, 13, 0, 0)},
        {"filename": "tests/test.py", "size": 512, "date_time": (2024, 1, 3, 14, 0, 0)}
    ]
    
    with patch('file_parser.check_file_validity', return_value=mock_file_tree):
        # ACT
        result = get_input_file_path()
        
        # ASSERT
        assert result == '/test/archive.zip'
        
        captured = capsys.readouterr()
        
        # Verify all files were printed
        assert "docs/readme.md" in captured.out
        assert "1024" in captured.out
        assert "src/main.py" in captured.out
        assert "2048" in captured.out
        assert "tests/test.py" in captured.out
        assert "512" in captured.out


def test_empty_zip_file(monkeypatch, capsys):
    """
    SCENARIO: Valid zip file but contains no files
    EXPECTED: Function prints message and loops back for new input
    
    WHAT WE'RE TESTING:
    - Does the function handle an empty list (valid zip with no files)?
    - Does it still return the path?
    
    Edge case: Empty but valid zip
    """
    user_inputs = iter([
        '/empty/archive.zip',
        '/valid/archive.zip'       # Second attempt: valid zip with files
    ])
    
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    # Mock: First call returns empty list, second returns files
    valid_file_tree = [
        {"filename": "file.txt", "size": 100, "date_time": (2024, 1, 1, 12, 0, 0)}
    ]
    
    with patch('file_parser.check_file_validity', side_effect=[None, valid_file_tree]):
        # ACT
        result = get_input_file_path()
        
        # ASSERT
        assert result == '/valid/archive.zip'
        
        captured = capsys.readouterr()
        assert "Invalid zip file detected." in captured.out
        assert "Valid zip file detected" in captured.out

def test_check_file_validity_valid_zip(tmp_path):
    """Should correctly validate a valid zip file."""
    zip_path = make_test_zip(tmp_path, {"README.md": "# Hello\nThis is a test."})
    result = check_file_validity(str(zip_path))

    # Ensure result is a non-empty list of dictionaries
    assert isinstance(result, list)
    assert len(result) == 1
    assert "filename" in result[0]


def test_check_file_validity_corrupted_zip(tmp_path):
    """Should detect and reject a corrupted zip file."""
    zip_path = tmp_path / "corrupted.zip"
    zip_path.write_bytes(b"This is not a valid zip archive")
    result = check_file_validity(str(zip_path))
    assert result is None

def test_extract_project_metadata_reads_readme(tmp_path):
    """Extractor should find README.md and return metadata summary."""
    files = {
        "README.md": "# Example Project\n",
        "main.py": "print('Hello')\nif __name__ == '__main__': main()",
        "docs/info.txt": "documentation",
    }
    zip_path = make_test_zip(tmp_path, files)
    metadata = extract_project_metadata(str(zip_path))

    # Should detect 3 files
    assert metadata["file_count"] == 3

    # Check that README was classified correctly
    readme = next((f for f in metadata["files"] if f["file_name"] == "README.md"), None)
    assert readme is not None
    assert "readme" in readme["project_metadata"]
    assert readme["category"] == "documentation"

def test_detect_source_code_data_detects_language():
    """Detects Python from extension and counts lines."""
    code = "def foo():\n    pass\nif __name__ == '__main__':\n    foo()\n"
    dummy_file = Path("example.py")
    result = detect_source_code_data(dummy_file, code)

    assert result["language"] == "Python"
    assert result["lines_of_code"] > 0
    assert result["has_main_entry"] is True

def test_categorize_file_assigns_types(tmp_path):
    """Ensure file categorization covers various types correctly."""
    examples = {
        "script.py": "other",
        "docs/guide.md": "documentation",
        "tests/test_app.py": "test_file",
        "data/sample.csv": "dataset",
        "image/logo.png": "image",
        "notebook.ipynb": "notebook",
    }

    for name, expected_category in examples.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("dummy")
        assert categorize_file(path) == expected_category

def test_get_file_metadata_fields(tmp_path):
    """Ensure basic file metadata includes all expected fields."""
    file_path = tmp_path / "demo.txt"
    file_path.write_text("hello world")
    root_dir = tmp_path
    info = get_file_metadata(file_path, root_dir)

    # Check for expected keys
    for key in ["file_name", "relative_path", "extension", "size_bytes"]:
        assert key in info

    assert info["file_name"] == "demo.txt"
    assert info["extension"] == ".txt"
    assert info["size_bytes"] > 0

def test_full_metadata_json_output(tmp_path):
    """Full integration test: ensure extractor produces valid JSON output."""
    files = {
        "README.md": "test project",
        "src/app.py": "print('hi')",
        "tests/test_basic.py": "def test_x(): pass",
        "data/data.csv": "a,b,c\n1,2,3",
    }

    zip_path = make_test_zip(tmp_path, files)
    metadata = extract_project_metadata(str(zip_path))

    # Check expected structure
    assert isinstance(metadata, dict)
    assert "file_count" in metadata
    assert "files" in metadata
    assert all(isinstance(f, dict) for f in metadata["files"])

    # Optionally write to JSON to ensure serializable
    output_path = tmp_path / "out.json"
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    assert output_path.exists()
    assert output_path.stat().st_size > 0