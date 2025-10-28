import pytest
from unittest.mock import patch
from metadata_extractor import (check_file_validity,
    extract_project_metadata,
    get_file_metadata,
    categorize_file,
    detect_source_code_data)


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