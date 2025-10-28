import pytest
import zipfile
from unittest.mock import patch
from file_parser import (get_input_file_path)

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

