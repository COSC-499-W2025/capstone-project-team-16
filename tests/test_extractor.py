import pytest
import json
import tempfile
import os
from datetime import datetime, timezone
from components.extractor import MetadataExtractorImpl
from contracts import FileInfo, FileMetadata, ExtractionFailure
import logging

@pytest.fixture
def valid_filter_json(tmp_path):
    """Creates a valid filters JSON file for testing."""
    filter_data = {
        "categories": {
            "source_code": [".py", "Makefile"],
            "docs": [".md"]
        },
        "languages": {
            "python": [".py"]
        }
    }
    path = tmp_path / "filters.json"
    path.write_text(json.dumps(filter_data))
    return str(path)

@pytest.fixture
def extractor(valid_filter_json):
    """Creates an extractor instance with a valid filters file."""
    return MetadataExtractorImpl(valid_filter_json)

class TestMetadataExtractorImpl:
    """Contains unit tests for the MetadataExtractorImpl component."""

    # --- Initialization Tests ---
    def test_init_with_valid_filters(self, valid_filter_json):
        """Tests for successful initialization with a valid filters file."""
        extractor = MetadataExtractorImpl(valid_filter_json)
        assert extractor.filters_path == valid_filter_json
        assert ".py" in extractor.ext_to_category
        assert ".py" in extractor.ext_to_language

    def test_init_missing_path_raises_error(self):
        """Tests that initialization with an empty path raises a ValueError."""
        with pytest.raises(ValueError, match="filters_path must be provided"):
            MetadataExtractorImpl("")

    def test_init_nonexistent_file_raises_error(self):
        """Tests that initialization with a non-existent file raises a FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            MetadataExtractorImpl("/nonexistent/filters.json")

    def test_init_malformed_json_raises_error(self, tmp_path):
        """Tests that initialization with a malformed JSON file raises a ValueError."""
        path = tmp_path / "bad.json"
        path.write_text("{invalid json")
        with pytest.raises(ValueError):
            MetadataExtractorImpl(str(path))

    def test_init_missing_categories_key_raises_error(self, tmp_path):
        """Tests that a filter file missing the 'categories' key raises a ValueError."""
        path = tmp_path / "no_categories.json"
        path.write_text(json.dumps({"languages": {}}))
        with pytest.raises(ValueError, match="Missing required 'categories'"):
            MetadataExtractorImpl(str(path))

    def test_init_malformed_category_items_raises_error(self, tmp_path):
        """Tests that categories with non-list values raise a ValueError."""
        path = tmp_path / "bad_cat.json"
        path.write_text(json.dumps({"categories": {"source_code": "not_a_list"}}))
        with pytest.raises(ValueError, match="must be a list"):
            MetadataExtractorImpl(str(path))

    def test_init_malformed_filter_items_raises_error(self, tmp_path):
        """Tests that filter items that are not strings raise a ValueError."""
        path = tmp_path / "bad_items.json"
        path.write_text(json.dumps({"categories": {"source_code": [123]}}))
        with pytest.raises(ValueError, match="must be strings"):
            MetadataExtractorImpl(str(path))

    def test_init_duplicate_extensions_overwrites(self, tmp_path):
        """Tests that later categories overwrite earlier ones for duplicate extensions."""
        path = tmp_path / "dup.json"
        path.write_text(json.dumps({
            "categories": {
                "first": [".py"],
                "second": [".py"]
            }
        }))
        extractor = MetadataExtractorImpl(str(path))
        assert extractor.ext_to_category[".py"] == "second"

    # --- Extraction Tests ---
    def test_base_extraction_categorizes_by_extension(self, extractor):
        """Tests categorization based on a file's extension."""
        files = [FileInfo("test.py", 100, datetime.now(timezone.utc), True)]
        result = extractor.base_extraction(files)
        
        assert len(result.succeeded) == 1
        metadata = result.succeeded[0]
        assert metadata.category == "source_code"
        assert metadata.language == "python"
        assert metadata.extension == ".py"

    def test_base_extraction_categorizes_by_filename(self, extractor):
        """Tests categorization based on an exact filename match (e.g., Makefile)."""
        files = [FileInfo("Makefile", 100, datetime.now(timezone.utc), True)]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].category == "source_code"  # As defined in the fixture

    def test_base_extraction_uncategorized_unknown_extension(self, extractor):
        """Tests that files with unknown extensions are marked as 'uncategorized'."""
        files = [FileInfo("unknown.xyz", 100, datetime.now(timezone.utc), True)]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].category == "uncategorized"

    def test_base_extraction_undefined_language_for_non_code(self, extractor):
        """Tests that non-code files are assigned an 'undefined' language."""
        files = [FileInfo("doc.md", 100, datetime.now(timezone.utc), True)]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].language == "undefined"

    def test_base_extraction_directory_handling(self, extractor):
        """Tests that directory entries are handled correctly during extraction."""
        files = [FileInfo(".git/", 0, None, False)]
        result = extractor.base_extraction(files)
        assert len(result.succeeded) == 1, "Should process one directory entry."
        assert result.succeeded[0].is_file is False, "is_file flag should be False for directories."
        assert result.succeeded[0].category == "uncategorized", "Category should be 'uncategorized' based on the test fixture's filters."

    def test_base_extraction_strip_trailing_slash(self, extractor):
        """Tests the removal of trailing slashes for directory matching."""
        files = [FileInfo(".git///", 0, None, False)]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].category == "uncategorized", "Category should be 'uncategorized' after stripping slashes."

    def test_base_extraction_case_insensitive_matching(self, extractor):
        """Tests that extension and filename matching is case-insensitive."""
        files = [
            FileInfo("test.PY", 100, datetime.now(timezone.utc), True),
            FileInfo("MAKEFILE", 100, datetime.now(timezone.utc), True)
        ]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].category == "source_code"
        assert result.succeeded[1].category == "source_code"

    def test_base_extraction_handles_malformed_fileinfo_gracefully(self, extractor):
        """Tests for robust error handling when a FileInfo object is malformed."""
        # Create a mock object missing attributes
        class BadFileInfo:
            pass
        
        result = extractor.base_extraction([BadFileInfo()])  # type: ignore
        assert len(result.failed) == 1
        assert result.failed[0].file_path == 'unknown'

    def test_base_extraction_empty_list(self, extractor):
        """Tests that extraction with an empty file list returns an empty result."""
        result = extractor.base_extraction([])
        assert len(result.succeeded) == 0
        assert len(result.failed) == 0

    def test_base_extraction_preserves_timestamp_none(self, extractor):
        """Tests that None timestamps from FileInfo are preserved in FileMetadata."""
        files = [FileInfo("test.py", 100, None, True)]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].last_modified is None

    # --- Performance & Edge Cases ---
    def test_base_extraction_large_batch(self, extractor):
        """Tests extraction performance with a large list of files."""
        files = [
            FileInfo(f"file_{i}.py", 100, datetime.now(timezone.utc), True)
            for i in range(10000)
        ]
        result = extractor.base_extraction(files)
        assert len(result.succeeded) == 10000

    def test_base_extraction_unicode_filenames(self, extractor):
        """Tests the handling of Unicode filenames during extraction."""
        files = [FileInfo("测试.py", 100, datetime.now(timezone.utc), True)]
        result = extractor.base_extraction(files)
        assert result.succeeded[0].file_path == "测试.py"

    def test_missing_languages_key_warning_logged(self, caplog, tmp_path):
        """Test warning is logged when 'languages' key is missing."""
        path = tmp_path / "no_lang.json"
        path.write_text(json.dumps({"categories": {}}))
        
        with caplog.at_level(logging.WARNING):
            MetadataExtractorImpl(str(path))
            assert "Missing 'languages' key" in caplog.text

    def test_base_extraction_categorizes_directory_by_name(self, real_filter_file):
        """Tests that directories like '.git' are categorized correctly by name."""
        extractor = MetadataExtractorImpl(str(real_filter_file))
        files = [FileInfo(".git/", 0, None, False)]
        
        result = extractor.base_extraction(files)
        
        assert result.succeeded[0].category == "repository"  # As defined in the real filters file
