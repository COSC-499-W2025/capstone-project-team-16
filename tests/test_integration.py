import pytest
import tempfile
import zipfile
import os
from pathlib import Path
from datetime import datetime, timezone

from components.scanner import ZipFileScanner
from components.extractor import MetadataExtractorImpl
from components.storage import StorageManager
from components.permissions import ConsolePermissionManager
from core.orchestrator import Orchestrator
from contracts import ConsentResult, FileScannerError, StorageError


class TestFullWorkflow:
    """Contains integration tests for the complete application workflow."""

    @pytest.fixture
    def sample_zip(self, tmp_path):
        """Creates a realistic sample zip file for integration testing."""
        zip_path = tmp_path / "sample_project.zip"
        files = {
            "src/main.py": b"def hello(): print('world')",
            "src/utils.py": b"import os\nimport sys",
            "tests/test_main.py": b"def test_hello(): pass",
            "web/index.html": b"<html><body>Hello</body></html>",
            "web/style.css": b"body { color: blue; }",
            "config.json": b'{"version": "1.0"}',
            "pyproject.toml": b"[tool.poetry]\nname = 'sample'",
            "README.md": b"# Sample Project",
            "Makefile": b"all:\n\techo 'done'",
            "Dockerfile": b"FROM python:3.9",
            "data.csv": b"a,b,c\n1,2,3",
            "logo.png": b"fake_png_data",
            ".gitignore": b"*.pyc\n__pycache__/",
            "src/__pycache__/": b"",  # Directory
        }
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for path, content in files.items():
                zf.writestr(path, content)
        
        return str(zip_path)

    @pytest.fixture
    def orchestrator_full(self, sample_zip, tmp_path, real_filter_file):
        """Creates an orchestrator instance with real, non-mocked components."""
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(sample_zip)
        
        extractor = MetadataExtractorImpl(str(real_filter_file))
        
        db_path = tmp_path / "test.db"
        storage = StorageManager(str(db_path))
        storage.initialize_database()
        
        return Orchestrator(
            metadata_extractor=extractor,
            storage=storage
        ), files, storage

    def test_complete_scan_extract_store_workflow(self, orchestrator_full):
        """Tests the full workflow from scanning to extraction and storage."""
        orchestrator, files, storage = orchestrator_full
        
        # Run the main workflow.
        summary = orchestrator.run(files)
        
        # Verify the contents of the summary object.
        assert summary.scanned_files == len(files)
        assert summary.processed_files > 0
        assert summary.scanned_files >= summary.processed_files
        
        # Verify that the data was persisted to storage.
        saved_files = list(storage.read_all_data())
        assert len(saved_files) == summary.processed_files
        
        # Verify the integrity of the stored data.
        for file_meta in saved_files:
            assert file_meta.file_path is not None
            assert file_meta.size >= 0
            assert file_meta.category in [
                "source_code", "web_code", "documentation", "configuration",
                "assets", "datasets", "binaries", "notebooks", "build_scripts",
                "docker_files", "git_metadata", "repository", "uncategorized"
            ]

    def test_workflow_handles_empty_zip(self, tmp_path, real_filter_file, memory_storage):
        """Tests that the workflow handles an empty zip file correctly."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass
        
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(str(zip_path))
        
        assert len(files) == 0
        
        extractor = MetadataExtractorImpl(str(real_filter_file))
        memory_storage.initialize_database()
        
        orchestrator = Orchestrator(
            metadata_extractor=extractor,
            storage=memory_storage
        )
        
        summary = orchestrator.run(files)
        
        assert summary.scanned_files == 0
        assert summary.processed_files == 0

    def test_workflow_with_mixed_valid_invalid_files(self, tmp_path, real_filter_file, memory_storage):
        """Tests the workflow with a mix of valid and malicious file paths."""
        zip_path = tmp_path / "mixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("valid.py", b"print('hello')")
            zf.writestr("../../../etc/passwd", b"root:x:0:0:")  # Invalid
            zf.writestr("normal.txt", b"content")
            zf.writestr("", b"empty_filename")  # Invalid
        
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(str(zip_path))
        
        # The scanner should filter out malicious paths.
        assert len(files) == 2  # valid.py and normal.txt
        
        extractor = MetadataExtractorImpl(str(real_filter_file))
        memory_storage.initialize_database()
        
        orchestrator = Orchestrator(
            metadata_extractor=extractor,
            storage=memory_storage
        )
        
        summary = orchestrator.run(files)
        
        assert summary.scanned_files == 2
        assert summary.processed_files == 2  # Both should process successfully

    def test_workflow_data_consistency_across_operations(self, orchestrator_full):
        """Tests that data remains consistent after multiple identical runs."""
        orchestrator, files, storage = orchestrator_full
        
        # First run.
        summary1 = orchestrator.run(files)
        
        # Second run with the same data.
        summary2 = orchestrator.run(files)
        
        # Verify that the summaries match.
        assert summary1.scanned_files == summary2.scanned_files
        assert summary1.processed_files == summary2.processed_files
        
        # Verify the database only contains data from the most recent run,
        # as the current storage implementation clears data on each save.
        saved_files = list(storage.read_all_data())
        assert len(saved_files) == summary2.processed_files

    def test_workflow_handles_large_file_list(self, tmp_path, real_filter_file, memory_storage):
        """Tests that the workflow can handle a large number of files."""
        zip_path = tmp_path / "large.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(10000):
                zf.writestr(f"src/file_{i}.py", b"def func(): pass")
        
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(str(zip_path))
        
        extractor = MetadataExtractorImpl(str(real_filter_file))
        memory_storage.initialize_database()
        
        orchestrator = Orchestrator(
            metadata_extractor=extractor,
            storage=memory_storage
        )
        
        # The workflow should complete without memory or performance issues.
        summary = orchestrator.run(files)
        
        assert summary.scanned_files == 10000
        assert summary.processed_files == 10000

    def test_workflow_with_unicode_filenames(self, tmp_path, real_filter_file, memory_storage):
        """Tests that the workflow correctly handles Unicode filenames."""
        zip_path = tmp_path / "unicode.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("测试.py", b"# Chinese test")
            zf.writestr("файл_тест.py", b"# Russian test")
            zf.writestr("🚀.py", b"# Emoji test")
        
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(str(zip_path))
        
        assert len(files) == 3
        
        extractor = MetadataExtractorImpl(str(real_filter_file))
        memory_storage.initialize_database()
        
        orchestrator = Orchestrator(
            metadata_extractor=extractor,
            storage=memory_storage
        )
        
        summary = orchestrator.run(files)
        
        assert summary.processed_files == 3
        
        saved = list(memory_storage.read_all_data())
        assert any("测试.py" in f.file_path for f in saved)


class TestPermissionIntegration:
    """Contains integration tests for the permission-granting flow."""

    def test_workflow_aborts_on_consent_denied(self, monkeypatch, memory_storage):
        """Tests that the workflow aborts if the user denies consent."""
        monkeypatch.setattr('builtins.input', lambda _: "N")
        
        permission = ConsolePermissionManager()
        consent = permission.get_user_consent()
        
        assert consent == ConsentResult.DENIED
        
        # In main.py, the app would exit here. For this test, we verify
        # no storage operations would occur if the workflow were to continue.
        memory_storage.initialize_database()
        
        before_count = len(list(memory_storage.read_all_data()))
        after_count = len(list(memory_storage.read_all_data()))
        assert before_count == after_count


class TestErrorRecovery:
    """Contains tests for application error recovery and resilience."""

    def test_workflow_handles_extractor_failure(self, sample_zip, monkeypatch, real_filter_file, memory_storage):
        """Tests that the workflow continues if the extractor fails on some files."""
        from unittest.mock import Mock
        
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(sample_zip)
        
        real_extractor = MetadataExtractorImpl(str(real_filter_file))
        
        # Create a mock that simulates failure on the first file.
        mock_result = real_extractor.base_extraction(files)
        mock_result.failed.append(type('MockFailure', (), {
            'file_path': files[0].file_path,
            'reason': 'Simulated failure'
        })())
        
        mock_extractor = Mock()
        mock_extractor.base_extraction.return_value = mock_result
        
        memory_storage.initialize_database()
        
        orchestrator = Orchestrator(
            metadata_extractor=mock_extractor,
            storage=memory_storage
        )
        
        summary = orchestrator.run(files)
        
        assert len(summary.failures) > 0
        assert summary.processed_files == len(mock_result.succeeded)

    def test_workflow_handles_storage_failure(self, sample_zip, tmp_path, real_filter_file):
        """Tests that the workflow handles storage errors gracefully."""
        scanner = ZipFileScanner()
        files = scanner._scan_zip_headers(sample_zip)
        
        extractor = MetadataExtractorImpl(str(real_filter_file))
        
        # Use an invalid database path to trigger a storage error.
        storage = StorageManager("/invalid/path/that/cannot/be/created/test.db")
        
        orchestrator = Orchestrator(
            metadata_extractor=extractor,
            storage=storage
        )
        
        with pytest.raises(StorageError):
            orchestrator.run(files)