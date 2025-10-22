import pytest
from unittest.mock import patch
from file_parser import get_input_file_path


def test_valid_path_first_try(monkeypatch):
    """
        SCENARIO: User enters a valid zip path immediately
        EXPECTED: Function returns that exact path
        
        WHAT WE'RE TESTING:
        - Does the function accept valid input?
        - Does it return the correct path?
        - Does it exit (not loop forever)?
    """
    monkeypatch.setattr('builtins.input', lambda _: '/valid/path.zip')

    with patch('file_parser.check_file_validity', return_value=True):

        result = get_input_file_path()

        assert result == '/valid/path.zip'

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
        '', # Press Enter first
        '/valid/path.zip' # Valid path right after
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))

    with patch('file_parser.check_file_validity', return_value=True):

        result = get_input_file_path()

        assert result == '/valid/path.zip'

        captured = capsys.readouterr()
        assert "No path was entered." in captured.out

def test_invalid_path_then_valid_path(monkeypatch, capsys):
    """
        SCENARIO: User enters invalid path and then a true one
        EXPECTED: Function loops back and asks again, then returns valid path
        
        WHAT WE'RE TESTING:
        - Does the function handle empty input?
        - Does it print an error message?
        - Does it loop and ask again?
        - Does it eventually accept valid input?
    """

    user_inputs = iter([
        '/invalid/path.zip', # Press Enter first
        '/valid/path.zip' # Valid path right after
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))

    with patch('file_parser.check_file_validity', side_effect=[False, True]):

        result = get_input_file_path()

        assert result == '/valid/path.zip'

        captured = capsys.readouterr()
        assert "Invalid zip file detected" in captured.out

