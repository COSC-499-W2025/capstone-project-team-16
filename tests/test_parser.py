import os
import tempfile
import zipfile
import pytest
from unittest.mock import patch
from file_parser import get_input_file_path, check_file_validity

# ----------------------------------------------------------
# Helper to create a dummy zip file
# ----------------------------------------------------------
def create_dummy_zip(zip_path, files=None):
    files = files or {"file.txt": b"hello world"}
    with zipfile.ZipFile(zip_path, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)

# ----------------------------------------------------------
# Tests for get_input_file_path
# ----------------------------------------------------------
def test_valid_zip_selected_first_try(capsys):
    """
    SCENARIO: One valid zip exists in input folder
    EXPECTED: Function detects zip immediately and returns file tree
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_file = os.path.join(tmpdir, "project.zip")
        create_dummy_zip(zip_file)

        with patch("builtins.input", lambda _: "1"):
            result = get_input_file_path(input_dir=tmpdir)

        assert result is not None
        captured = capsys.readouterr()
        assert "Valid zip file detected" in captured.out

def test_no_zip_then_user_adds_one(capsys):
    """
    SCENARIO: Input folder initially empty
    EXPECTED: Function prompts, then detects newly added zip
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_file = os.path.join(tmpdir, "project.zip")
        # Patch input to create zip after first Enter press
        inputs = iter(["", "1"])
        def fake_input(prompt=""):
            if next(inputs) == "":
                create_dummy_zip(zip_file)
                return ""
            return "1"

        with patch("builtins.input", fake_input):
            result = get_input_file_path(input_dir=tmpdir)

        assert result is not None
        captured = capsys.readouterr()
        assert "No zip files found" in captured.out
        assert "Valid zip file detected" in captured.out

def test_cancel_selection(capsys):
    """
    SCENARIO: User cancels selection by entering 0
    EXPECTED: Returns None
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_file = os.path.join(tmpdir, "project.zip")
        create_dummy_zip(zip_file)

        with patch("builtins.input", lambda _: "0"):
            result = get_input_file_path(input_dir=tmpdir)

        assert result is None
        captured = capsys.readouterr()
        assert "Select a zip file" in captured.out

def test_invalid_number_then_valid(capsys):
    """
    SCENARIO: User enters number out of range first, then valid selection
    EXPECTED: Function loops and eventually returns correct file tree
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_file = os.path.join(tmpdir, "project.zip")
        create_dummy_zip(zip_file)

        inputs = iter(["99", "1"])
        with patch("builtins.input", lambda _: next(inputs)):
            result = get_input_file_path(input_dir=tmpdir)

        assert result is not None
        captured = capsys.readouterr()
        assert "Number out of range" in captured.out
        assert "Valid zip file detected" in captured.out

def test_empty_input_folder_returns_none(capsys):
    """
    SCENARIO: Input folder remains empty after prompting
    EXPECTED: Function returns None
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch input and os.listdir to simulate empty folder
        with patch("builtins.input", side_effect=["", ""]):
            with patch("os.listdir", return_value=[]):
                result = get_input_file_path(input_dir=tmpdir)

    # Function should return None
    assert result is None

    captured = capsys.readouterr()
    assert "No zip files found" in captured.out
    assert "Returning to home" in captured.out


# ----------------------------------------------------------
# Tests for check_file_validity
# ----------------------------------------------------------
def test_valid_zip_file():
    """
    SCENARIO: Valid zip provided
    EXPECTED: Returns file tree
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_file = os.path.join(tmpdir, "project.zip")
        create_dummy_zip(zip_file, {"a.txt": b"1", "b.txt": b"2"})

        file_tree = check_file_validity(zip_file)
        assert isinstance(file_tree, list)
        assert len(file_tree) == 2
        assert all("filename" in f for f in file_tree)

def test_nonexistent_file(capsys):
    """
    SCENARIO: File path does not exist
    EXPECTED: Returns None
    """
    file_tree = check_file_validity("/nonexistent/file.zip")
    assert file_tree is None
    captured = capsys.readouterr()
    assert "Path does not exist" in captured.out

def test_not_a_zip_file(capsys):
    """
    SCENARIO: File exists but is not a zip
    EXPECTED: Returns None
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_file = os.path.join(tmpdir, "file.txt")
        with open(fake_file, "w") as f:
            f.write("hello")
        file_tree = check_file_validity(fake_file)
        assert file_tree is None
        captured = capsys.readouterr()
        assert "not a zip file" in captured.out.lower()

def test_empty_zip_file(capsys):
    """
    SCENARIO: Zip file exists but contains no files
    EXPECTED: check_file_validity returns None and prints a message
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "empty.zip")
        
        # Create an actual empty zip file
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass  # no files added

        # Call the function
        file_tree = check_file_validity(zip_path)

        # ASSERT: should be None
        assert file_tree is None

        captured = capsys.readouterr()
        assert "Zip file is valid, but empty." in captured.out
