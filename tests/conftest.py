import pytest
import tempfile
import os
import sys
import zipfile
import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import contextlib
from components.storage import StorageManager

# Add src directory to the path to allow for absolute imports from src.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from contracts import FileMetadata

@pytest.fixture(scope="session")
def src_root():
    """Returns the absolute path to the src directory."""
    return Path(__file__).parent.parent / "src"

@pytest.fixture(scope="session")
def real_filter_file(src_root):
    """Returns the path to the real extractor_filters.json file."""
    return src_root / "data" / "extractor_filters.json"

@pytest.fixture
def temp_dir(tmp_path):
    """Provides a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def mock_env(monkeypatch, temp_dir):
    """Provides isolated environment variables for the duration of a test."""
    # Store original environment variables to restore them later.
    originals = {
        "SKILLSCOPE_DB_PATH": os.environ.get("SKILLSCOPE_DB_PATH"),
        "SKILLSCOPE_MODE": os.environ.get("SKILLSCOPE_MODE")
    }
    
    # Set test values
    monkeypatch.setenv("SKILLSCOPE_DB_PATH", str(temp_dir / "test.db"))
    monkeypatch.setenv("SKILLSCOPE_MODE", "DEV")
    
    yield
    
    # Restore the original environment variables after the test.
    for key, value in originals.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

@pytest.fixture
def valid_zip_file(temp_dir):
    """Creates a valid test zip file with a diverse set of content."""
    zip_path = temp_dir / "valid_project.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Source files
        zf.writestr("src/main.py", b"def hello(): pass")
        zf.writestr("src/utils.py", b"import os")
        zf.writestr("tests/test_main.py", b"assert True")
        
        # Web files
        zf.writestr("web/index.html", b"<html></html>")
        zf.writestr("web/style.css", b"body { color: red; }")
        
        # Config files
        zf.writestr("config.json", b'{"version": "1.0"}')
        zf.writestr("pyproject.toml", b"[tool.poetry]")
        zf.writestr(".gitignore", b"*.pyc\n__pycache__/")
        
        # Documentation
        zf.writestr("README.md", b"# Project")
        zf.writestr("docs/api.rst", b"API Documentation")
        
        # Build scripts
        zf.writestr("Makefile", b"all: test\n\ntest:\n\tpytest")
        zf.writestr("Dockerfile", b"FROM python:3.9")
        
        # Notebooks
        zf.writestr("analysis.ipynb", b'{"cells": []}')
        
        # Assets
        zf.writestr("logo.png", b"fake_image_data")
        
        # Directories
        zf.writestr("data/", b"")
        zf.writestr("src/__pycache__/", b"")
        
        # Files with special names
        zf.writestr("file with spaces.py", b"# spaces")
        zf.writestr("测试.py", b"# unicode")
        zf.writestr("a" * 200 + ".txt", b"# long name")
        
        # File with no extension
        zf.writestr("LICENSE", b"MIT License")
        
        # Binary file
        zf.writestr("binary.dll", b"\x00\x01\x02\x03")
    
    return str(zip_path)

@pytest.fixture
def malicious_zip_slip(temp_dir):
    """Creates a zip file containing various Zip Slip attack vectors."""
    zip_path = temp_dir / "attack.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Classic traversal
        zf.writestr("../../../etc/passwd", b"root:x:0:0:")
        zf.writestr("../../../windows/system32/cmd.exe", b"malware")
        
        # Absolute paths
        zf.writestr("/etc/hosts", b"127.0.0.1 evil.com")
        zf.writestr("C:/Windows/System32/calc.exe", b"fake")
        
        # Encoded traversal
        zf.writestr("%2e%2e/%2e%2e/etc/shadow", b"data")
        zf.writestr("%252e%252e/etc/crontab", b"malicious")
        
        # Double dots
        zf.writestr("a/b/../../etc/passwd", b"root")
        
        # Mixed slashes
        zf.writestr("..\\../..\\../etc/passwd", b"windows_slash")
        
        # Empty filename
        zf.writestr("", b"empty")
        
        # Current directory trick
        zf.writestr("./../../../etc/passwd", b"root")
        
        # Normalized path escape
        zf.writestr("foo/../bar/../../etc/passwd", b"root")
        
        # Unicode homoglyphs (if supported)
        try:
            zf.writestr("\u002e\u002e/\u002e\u002e/etc/passwd", b"unicode")
        except:
            pass
    
    return str(zip_path)

@pytest.fixture
def corrupted_zip_file(temp_dir):
    """Creates a corrupted (invalid) zip file."""
    zip_path = temp_dir / "corrupted.zip"
    zip_path.write_bytes(b"This is not a valid zip file")
    return str(zip_path)

@pytest.fixture
def empty_zip_file(temp_dir):
    """Creates an empty zip file with no entries."""
    zip_path = temp_dir / "empty.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        pass
    return str(zip_path)

@pytest.fixture
def zip_with_bad_timestamps(temp_dir):
    """Creates a zip file containing entries with invalid timestamps."""
    zip_path = temp_dir / "bad_time.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Create a ZipInfo with invalid date
        info = zipfile.ZipInfo("file.txt")
        info.date_time = (2023, 13, 45, 25, 61, 61)  # Invalid month, day, minute, second
        zf.writestr(info, b"content")
        
        # Another with year overflow
        info2 = zipfile.ZipInfo("file2.txt")
        info2.date_time = (99999, 1, 1, 0, 0, 0)  # Year too large
        zf.writestr(info2, b"content2")
    
    return str(zip_path)

@pytest.fixture
def malformed_filters(temp_dir):
    """Creates a dictionary of various malformed filter files."""
    filters = {}
    
    # Missing categories
    path = temp_dir / "missing_categories.json"
    path.write_text(json.dumps({"languages": {}}))
    filters["missing_categories"] = str(path)
    
    # Invalid JSON
    path = temp_dir / "invalid_json.json"
    path.write_text("{invalid json")
    filters["invalid_json"] = str(path)
    
    # Non-list categories
    path = temp_dir / "non_list.json"
    path.write_text(json.dumps({"categories": {"code": "not_a_list"}}))
    filters["non_list"] = str(path)
    
    # Non-string items
    path = temp_dir / "non_string.json"
    path.write_text(json.dumps({"categories": {"code": [123]}}))
    filters["non_string"] = str(path)
    
    # Valid for comparison
    path = temp_dir / "valid.json"
    path.write_text(json.dumps({
        "categories": {"code": [".py"]},
        "languages": {"python": [".py"]}
    }))
    filters["valid"] = str(path)
    
    return filters

@pytest.fixture
def sample_file_metadata():
    """Generates a list of diverse FileMetadata objects for testing."""
    return [
        # Normal file
        FileMetadata("src/main.py", 1024, datetime.now(timezone.utc), ".py", "source_code", True, "python"),
        
        # File with no extension
        FileMetadata("LICENSE", 2048, datetime.now(timezone.utc), "", "uncategorized", True, "undefined"),
        
        # Directory
        FileMetadata("src/", 0, None, "", "repository", False, "undefined"),
        
        # Unicode filename
        FileMetadata("测试.py", 512, datetime.now(timezone.utc), ".py", "source_code", True, "python"),
        
        # Very large file
        FileMetadata("data/big.csv", 2**30, datetime.now(timezone.utc), ".csv", "datasets", True, "undefined"),
        
        # Null timestamp
        FileMetadata("build/temp.tmp", 0, None, ".tmp", "uncategorized", True, "undefined"),
        
        # SQL injection attempt
        FileMetadata("'; DROP TABLE files;--.py", 100, None, ".py", "source_code", True, "python"),
        
        # Path traversal in filename
        FileMetadata("../../../etc/passwd", 100, None, "", "uncategorized", True, "undefined"),
        
        # Long filename
        FileMetadata("a" * 255 + ".py", 100, None, ".py", "source_code", True, "python"),
    ]

@pytest.fixture(autouse=True)
def reset_logging():
    """Saves and restores the logging state for each test to ensure isolation."""
    import logging
    original_handlers = logging.root.handlers[:]
    original_level = logging.root.level
    
    yield
    
    logging.root.handlers = original_handlers
    logging.root.level = original_level

class TestStorageManager(StorageManager):
    """A test-specific storage manager that uses a shared in-memory connection."""
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        super().__init__(db_path=":memory:")

    @contextlib.contextmanager
    def get_db_connection(self):
        yield self._connection

@pytest.fixture
def memory_storage():
    """
    Provides a StorageManager using a single, shared in-memory database connection.

    This fixture ensures that data persists between different operations within the same test function.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    storage = TestStorageManager(conn)
    storage.initialize_database()
    yield storage
    conn.close()

@pytest.fixture
def sample_zip(valid_zip_file):
    """Alias for valid_zip_file to match test expectations."""
    return valid_zip_file
    conn.close()