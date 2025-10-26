import pytest
from unittest.mock import patch, MagicMock, mock_open
import zipfile
from file_parser import check_file_validity


def test_path_does_not_exist(capsys):
    """
    SCENARIO: User provides a path that doesn't exist
    EXPECTED: Returns None and prints error message
    
    WHAT WE'RE TESTING:
    - First validation check (os.path.exists)
    - Returns None for non-existent paths
    - Prints appropriate error message
    """
    # ARRANGE
    fake_path = '/nonexistent/path/file.zip'
    
    # Mock os.path.exists to return False
    with patch('os.path.exists', return_value=False):
        # ACT
        result = check_file_validity(fake_path)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "Path does not exist" in captured.out

def test_path_exists_but_not_a_file(capsys):
    """
    SCENARIO: User provides a path to a directory, not a file
    EXPECTED: Returns None and prints error message
    
    WHAT WE'RE TESTING:
    - Second validation check (os.path.isfile)
    - Distinguishes between directories and files
    """
    # ARRANGE
    directory_path = '/some/directory'
    
    # Mock: path exists but is not a file
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=False):
        # ACT
        result = check_file_validity(directory_path)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "File does not exist" in captured.out

def test_file_not_zip_extension(capsys):
    """
    SCENARIO: User provides a file that doesn't end in .zip
    EXPECTED: Returns None and prints error message
    
    WHAT WE'RE TESTING:
    - Third validation check (ends with .zip)
    - Extension validation
    """
    # ARRANGE
    text_file = '/path/to/file.txt'
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True):
        # ACT
        result = check_file_validity(text_file)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "The requested file is not a zip file" in captured.out

def test_zip_extension_case_insensitive(capsys):
    """
    SCENARIO: File ends in .ZIP, .Zip, etc. (uppercase/mixed case)
    EXPECTED: Should be accepted (case insensitive)
    
    WHAT WE'RE TESTING:
    - Extension check is case insensitive (.lower())
    """
    # ARRANGE
    uppercase_zip = '/path/to/FILE.ZIP'
    
    # Mock a valid zip file
    mock_zip = MagicMock()
    mock_zip.__enter__.return_value.testzip.return_value = None
    mock_zip.__enter__.return_value.infolist.return_value = [
        MagicMock(filename="test.txt", file_size=100, date_time=(2024, 1, 1, 12, 0, 0))
    ]
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', return_value=mock_zip):
        # ACT
        result = check_file_validity(uppercase_zip)
        
        # ASSERT
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1

def test_valid_zip_with_files(capsys):
    """
    SCENARIO: Valid zip file containing multiple files
    EXPECTED: Returns list of dictionaries with file info
    
    WHAT WE'RE TESTING:
    - Happy path - everything works
    - Returns correct structure (list of dicts)
    - Each dict has filename, size, date_time
    """
    # ARRANGE
    valid_zip = '/path/to/valid.zip'
    
    # Create mock ZipFile
    mock_zip = MagicMock()
    mock_zip.__enter__.return_value.testzip.return_value = None  # No corruption
    
    # Mock file info objects
    mock_file1 = MagicMock()
    mock_file1.filename = "readme.txt"
    mock_file1.file_size = 1024
    mock_file1.date_time = (2024, 1, 1, 12, 0, 0)
    
    mock_file2 = MagicMock()
    mock_file2.filename = "src/main.py"
    mock_file2.file_size = 2048
    mock_file2.date_time = (2024, 1, 2, 13, 30, 0)
    
    mock_zip.__enter__.return_value.infolist.return_value = [mock_file1, mock_file2]
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', return_value=mock_zip):
        # ACT
        result = check_file_validity(valid_zip)
        
        # ASSERT
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Check first file
        assert result[0]["filename"] == "readme.txt"
        assert result[0]["size"] == 1024
        assert result[0]["date_time"] == (2024, 1, 1, 12, 0, 0)
        
        # Check second file
        assert result[1]["filename"] == "src/main.py"
        assert result[1]["size"] == 2048
        assert result[1]["date_time"] == (2024, 1, 2, 13, 30, 0)

def test_corrupted_zip_file(capsys):
    """
    SCENARIO: Zip file has corruption detected by testzip()
    EXPECTED: Returns None and prints corruption message
    
    WHAT WE'RE TESTING:
    - Corruption detection (testzip returns filename of bad entry)
    - Proper error message with bad file name
    """
    # ARRANGE
    corrupt_zip = '/path/to/corrupt.zip'
    
    mock_zip = MagicMock()
    mock_zip.__enter__.return_value.testzip.return_value = "corrupted_file.txt"
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', return_value=mock_zip):
        # ACT
        result = check_file_validity(corrupt_zip)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "Corrupted archive" in captured.out
        assert "corrupted_file.txt" in captured.out

def test_empty_zip_file(capsys):
    """
    SCENARIO: Valid zip but contains no files
    EXPECTED: Returns None and prints empty message
    
    WHAT WE'RE TESTING:
    - Empty file list handling
    - Appropriate message for empty zips
    """
    # ARRANGE
    empty_zip = '/path/to/empty.zip'
    
    mock_zip = MagicMock()
    mock_zip.__enter__.return_value.testzip.return_value = None
    mock_zip.__enter__.return_value.infolist.return_value = []  # Empty list
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', return_value=mock_zip):
        # ACT
        result = check_file_validity(empty_zip)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "Zip file is valid, but empty" in captured.out

def test_bad_zip_file_exception(capsys):
    """
    SCENARIO: File has .zip extension but isn't actually a zip file
    EXPECTED: Returns None and prints error message
    
    WHAT WE'RE TESTING:
    - BadZipFile exception handling
    - Appropriate error message
    """
    # ARRANGE
    fake_zip = '/path/to/fake.zip'
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile):
        # ACT
        result = check_file_validity(fake_zip)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "Not a zip file or corrupted" in captured.out

def test_large_zip_file_exception(capsys):
    """
    SCENARIO: Zip file uses ZIP64 format (very large files)
    EXPECTED: Returns None and prints error message
    
    WHAT WE'RE TESTING:
    - LargeZipFile exception handling
    - ZIP64 detection
    """
    # ARRANGE
    large_zip = '/path/to/huge.zip'
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', side_effect=zipfile.LargeZipFile):
        # ACT
        result = check_file_validity(large_zip)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "ZIP64" in captured.out
        assert "Too large" in captured.out

def test_generic_exception(capsys):
    """
    SCENARIO: Unexpected error occurs
    EXPECTED: Returns None and prints error message with details
    
    WHAT WE'RE TESTING:
    - Catch-all exception handler
    - Error details are printed
    """
    # ARRANGE
    problem_zip = '/path/to/problem.zip'
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('zipfile.ZipFile', side_effect=Exception("Unexpected error occurred")):
        # ACT
        result = check_file_validity(problem_zip)
        
        # ASSERT
        assert result is None
        
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Unexpected error occurred" in captured.out