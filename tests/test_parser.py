import pytest
from unittest.mock import patch
from file_parser import get_input_file_path


def test_valid_path_first_try(monkeypatch, capsys):
    test_path = '/valid/path/project.zip'
    monkeypatch.setattr('builtins.input', lambda _: test_path)

    mock_file_tree = [
        {"filename": "file1.txt", "size": 1024, "last_modified": (2024, 1, 1, 12, 0, 0)},
        {"filename": "file2.py", "size": 2048, "last_modified": (2024, 1, 2, 13, 0, 0)},
    ]

    with patch('file_parser.check_file_validity', return_value=mock_file_tree):
        result = get_input_file_path()

    # ASSERT
    assert result == mock_file_tree

    captured = capsys.readouterr()
    assert "Valid zip file detected" in captured.out


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

    user_inputs = iter(['', '/valid/path/project.zip'])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))

    mock_file_tree = [
        {"filename": "readme.txt", "size": 512, "last_modified": (2024, 1, 1, 12, 0, 0)}
    ]

    with patch('file_parser.check_file_validity', return_value=mock_file_tree):
        result = get_input_file_path()
        assert result == mock_file_tree

        captured = capsys.readouterr()
        assert "No path was entered." in captured.out
        assert "Valid zip file detected" in captured.out


def test_invalid_path_then_valid_path(monkeypatch, capsys):
    """
    SCENARIO: User enters invalid path and then a valid one
    EXPECTED: Function loops back and asks again, then returns valid path

    WHAT WE'RE TESTING:
    - Does the function handle invalid input?
    - Does it print an error message?
    - Does it loop and ask again?
    - Does it eventually accept valid input?
    """

    user_inputs = iter(['/invalid/path.zip', '/valid/path.zip'])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))

    mock_file_tree = [
        {"filename": "main.py", "size": 2048, "last_modified": (2024, 1, 1, 12, 0, 0)}
    ]

    with patch('file_parser.check_file_validity', side_effect=[None, mock_file_tree]):
        result = get_input_file_path()
        assert result == mock_file_tree

        captured = capsys.readouterr()
        assert "Invalid zip file detected" in captured.out
        assert "Valid zip file detected" in captured.out


def test_multiple_invalid_path_then_valid_path(monkeypatch, capsys):
    """
    SCENARIO: User enters multiple invalid paths and then a valid one
    EXPECTED: Function loops back and asks again until a valid path is entered,
              then returns valid path

    WHAT WE'RE TESTING:
    - Does the function persist through multiple failures?
    - Does it eventually accept valid input?
    - Does it handle a mix of empty and invalid inputs?
    """

    # ARRANGE - User tries 4 times before success
    user_inputs = iter(['', '/bad/path.txt', '/nonexistent.zip', '/finally/valid.zip'])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))

    mock_file_tree = [
        {"filename": "success.txt", "size": 100, "last_modified": (2024, 1, 1, 12, 0, 0)}
    ]

    with patch('file_parser.check_file_validity', side_effect=[None, None, mock_file_tree]):
        result = get_input_file_path()
        assert result == mock_file_tree

        captured = capsys.readouterr()
        assert "No path was entered." in captured.out
        assert captured.out.count("Invalid zip file detected") == 2
        assert "Valid zip file detected" in captured.out


def test_file_tree_assignment(monkeypatch, capsys):
    """
    SCENARIO: Valid zip with multiple files
    EXPECTED: File tree returned from get_input_file_path matches the value
              from check_file_validity.

    WHAT WE'RE TESTING:
    - Does get_input_file_path correctly return the file tree provided by
      check_file_validity?
    """
    monkeypatch.setattr('builtins.input', lambda _: '/test/archive.zip')

    mock_file_tree = [
        {"filename": "docs/readme.md", "size": 1024, "last_modified": (2024, 1, 1, 12, 0, 0)},
        {"filename": "src/main.py", "size": 2048, "last_modified": (2024, 1, 2, 13, 0, 0)},
        {"filename": "tests/test.py", "size": 512, "last_modified": (2024, 1, 3, 14, 0, 0)},
    ]

    with patch('file_parser.check_file_validity', return_value=mock_file_tree):
        result = get_input_file_path()
        assert result == mock_file_tree

        captured = capsys.readouterr()
        assert "Valid zip file detected" in captured.out


def test_empty_zip_file(monkeypatch, capsys):
    """
    SCENARIO: check_file_validity reports an "empty" or invalid zip on first call,
              then a valid one on second call.
    EXPECTED: Function prints invalid message, loops, then returns the valid file tree.

    WHAT WE'RE TESTING:
    - Does the function handle a failed validation (e.g., empty zip)?
    - Does it loop and accept a subsequent valid zip?
    """

    user_inputs = iter(['/empty/archive.zip', '/valid/archive.zip'])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))

    valid_file_tree = [
        {"filename": "file.txt", "size": 100, "last_modified": (2024, 1, 1, 12, 0, 0)}
    ]

    # First call: invalid/empty (None). Second: valid file tree.
    with patch('file_parser.check_file_validity', side_effect=[None, valid_file_tree]):
        result = get_input_file_path()
        assert result == valid_file_tree

        captured = capsys.readouterr()
        assert "Invalid zip file detected" in captured.out
        assert "Valid zip file detected" in captured.out
