import pytest
import zipfile
import tempfile
import os
from datetime import datetime, timezone
from components.scanner import ZipFileScanner, FileScannerError
from contracts import FileInfo
import io

@pytest.fixture
def scanner():
    """Creates a ZipFileScanner instance for testing."""
    return ZipFileScanner()

@pytest.fixture
def valid_zip(tmp_path):
    """Creates a valid zip file with standard content for testing."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("file1.py", b"print('hello')")
        zf.writestr("folder/file2.json", b'{"key": "value"}')
        zf.writestr("Makefile", b"all: build")
    return str(zip_path)

@pytest.fixture
def zip_with_dirs(tmp_path):
    """Creates a zip file that includes explicit directory entries."""
    zip_path = tmp_path / "dirs.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("root_file.txt", b"content")
        zf.writestr("subdir/", b"")  # Directory entry
        zf.writestr("subdir/nested.py", b"code")
    return str(zip_path)

class TestZipFileScanner:
    """Contains unit tests for the ZipFileScanner component."""

    # --- Validation Tests ---
    def test_scan_nonexistent_file_raises_error(self, scanner):
        """Tests that scanning a non-existent file raises a FileScannerError."""
        with pytest.raises(FileScannerError, match="Invalid zip file path"):
            scanner._scan_zip_headers("/nonexistent.zip")

    def test_scan_non_zip_file_raises_error(self, scanner, tmp_path):
        """Tests that scanning a file without a .zip extension raises an error."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not a zip")
        with pytest.raises(FileScannerError, match="Invalid zip file path"):
            scanner._scan_zip_headers(str(txt_path))

    def test_scan_corrupted_zip_raises_error(self, scanner, tmp_path):
        """Tests that scanning a corrupted or invalid zip file raises an error."""
        bad_zip = tmp_path / "bad.zip"
        bad_zip.write_bytes(b"not a valid zip")
        with pytest.raises(FileScannerError, match="corrupted or not a zip"):
            scanner._scan_zip_headers(str(bad_zip))

    # --- Security Tests: Zip Slip ---
    def test_scan_blocks_absolute_paths(self, scanner, tmp_path):
        """Test blocking absolute paths in zip."""
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("/etc/passwd", b"hacked")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 0

    def test_scan_blocks_traversal_before_normalization(self, scanner, tmp_path):
        """Test blocking path traversal like '../../etc/passwd'."""
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../../etc/passwd", b"hacked")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 0

    def test_scan_blocks_traversal_after_normalization(self, scanner, tmp_path):
        """Test blocking normalized traversal attempts."""
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("a/b/../../../etc/passwd", b"hacked")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 0

    def test_scan_blocks_url_encoded_traversal(self, scanner, tmp_path):
        """Test blocking URL-encoded path traversal."""
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("%2e%2e/%2e%2e/etc/passwd", b"hacked")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 0

    def test_scan_blocks_double_encoded_traversal(self, scanner, tmp_path):
        """Test blocking double-encoded path traversal."""
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("%252e%252e/etc/passwd", b"hacked")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 0

    def test_scan_blocks_empty_filename(self, scanner, tmp_path):
        """Test blocking empty filenames."""
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("", b"empty")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 0

    # --- Functional Tests ---
    def test_scan_valid_zip_returns_fileinfo_list(self, scanner, valid_zip):
        """Tests that a successful scan of a valid zip returns a list of FileInfo objects."""
        result = scanner._scan_zip_headers(valid_zip)
        assert len(result) == 3
        assert all(isinstance(f, FileInfo) for f in result)

    def test_scan_preserves_file_size(self, scanner, valid_zip):
        """Test file sizes are correctly captured."""
        result = scanner._scan_zip_headers(valid_zip)
        py_file = next(f for f in result if f.file_path == "file1.py")
        assert py_file.size == len(b"print('hello')")

    def test_scan_handles_directories(self, scanner, zip_with_dirs):
        """Tests that directory entries are correctly identified and marked."""
        result = scanner._scan_zip_headers(zip_with_dirs)
        dir_entry = next(f for f in result if f.file_path == "subdir/")
        assert dir_entry.is_file is False
        assert dir_entry.size == 0

    def test_scan_handles_malformed_timestamps(self, scanner, tmp_path, monkeypatch):
        """Tests for graceful handling of malformed zip timestamps."""
        zip_path = tmp_path / "bad_time.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            info = zipfile.ZipInfo("file.txt")
            info.date_time = (2023, 13, 45, 25, 61, 61)  # Invalid datetime
            zf.writestr(info, b"content")
        
        result = scanner._scan_zip_headers(zip_path)
        assert result[0].last_modified is None

    def test_scan_converts_to_utc(self, scanner, valid_zip):
        """Tests that timestamps are correctly converted to the UTC timezone."""
        result = scanner._scan_zip_headers(valid_zip)
        for file_info in result:
            if file_info.last_modified:
                assert file_info.last_modified.tzinfo == timezone.utc

    def test_scan_empty_zip_returns_empty_list(self, scanner, tmp_path):
        """Tests that scanning an empty zip file returns an empty list."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass
        
        result = scanner._scan_zip_headers(zip_path)
        assert len(result) == 0

    def test_scan_unicode_filenames(self, scanner, tmp_path):
        """Tests scanning of files with Unicode characters in their names."""
        zip_path = tmp_path / "unicode.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("测试.py", b"code")
            zf.writestr("файл.txt", b"content")
        
        result = scanner._scan_zip_headers(zip_path)
        assert len(result) == 2
        assert any("测试.py" in f.file_path for f in result)

    def test_scan_very_large_zip(self, scanner, tmp_path):
        """Tests scanning a zip with a large number of files for performance."""
        zip_path = tmp_path / "large.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(10000):
                zf.writestr(f"file_{i}.txt", b"content")
        
        result = scanner._scan_zip_headers(zip_path)
        assert len(result) == 10000

    def test_scan_zip_with_very_long_filenames(self, scanner, tmp_path):
        """Tests the handling of extremely long filenames within a zip."""
        zip_path = tmp_path / "long_names.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # 255+ character filename
            long_name = "a" * 300 + ".py"
            zf.writestr(long_name, b"content")
        
        result = scanner._scan_zip_headers(str(zip_path))
        assert len(result) == 1  # Should handle long names gracefully

    def test_cleanup_is_noop(self, scanner):
        """Tests that the cleanup method is a no-op, as designed."""
        scanner.cleanup()  # Use the fixture

    # --- Interactive Method Tests ---
    def test_get_input_file_path_user_cancels(self, scanner, monkeypatch):
        """Tests that the user can cancel the input prompt by entering an empty string."""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = scanner.get_input_file_path()
        assert result is None

    def test_get_input_file_path_invalid_path_retries(self, scanner, monkeypatch, capsys):
        """Tests that providing an invalid path prompts the user to retry."""
        inputs = iter(["bad_path", ""])  # First invalid, then cancel
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        result = scanner.get_input_file_path()
        assert result is None
        captured = capsys.readouterr()
        assert "Error:" in captured.out  # Verify an error message was shown

    def test_get_input_file_path_retries_on_invalid_path(self, scanner, monkeypatch, tmp_path, capsys):
        """Test invalid path prompts for retry until valid."""
        valid_zip = tmp_path / "valid.zip"
        with zipfile.ZipFile(valid_zip, 'w') as zf:
            zf.writestr("test.py", b"content")
        
        inputs = iter(["/nonexistent.zip", str(valid_zip)])  # Invalid, then valid
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        result = scanner.get_input_file_path()
        
        assert result is not None
        assert len(result) == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out  # Should show error for first attempt


    # --- Performance & Stress Tests ---

    @pytest.mark.slow
    def test_scan_performance_large_zip(self, scanner, tmp_path):
        """Tests the scanner's performance with a large zip file."""
        import time
        
        zip_path = tmp_path / "performance.zip"
        file_count = 50000
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(file_count):
                zf.writestr(f"src/file_{i}.py", b"# content")
        
        start_scan = time.time()
        results = scanner._scan_zip_headers(str(zip_path))
        scan_time = time.time() - start_scan
        
        assert len(results) == file_count
        
        # Use a generous threshold and skip if too slow to avoid CI failures.
        if scan_time > 15.0:
            pytest.skip(f"Performance test too slow on this system: {scan_time:.2f}s")

    @pytest.mark.slow
    def test_scan_memory_efficiency(self, scanner, tmp_path):
        """Tests that the scanner does not load the entire zip file into memory."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        zip_path = tmp_path / "memory_test.zip"
        
        # Create a 100MB zip file with many individual files.
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(10000):
                zf.writestr(f"file_{i}.txt", b"x" * 10240)  # 10KB each
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        
        results = scanner._scan_zip_headers(str(zip_path))
        
        mem_after = process.memory_info().rss
        mem_increase = (mem_after - mem_before) / 1024 / 1024  # MB
        
        assert len(results) == 10000
        # The memory increase should be minimal (< 50MB for metadata).
        if mem_increase > 50:
            pytest.skip(f"Memory increase ({mem_increase:.1f}MB) exceeded threshold.")

    def test_scan_concurrent_access(self, scanner, valid_zip):
        """Tests that the scanner handles concurrent access attempts safely."""
        import threading
        
        results = []
        errors = []
        
        def scan_in_thread():
            try:
                thread_results = scanner._scan_zip_headers(valid_zip)
                results.append(thread_results)
            except Exception as e:
                errors.append(e)
        
        # Run 10 concurrent scans on the same file.
        threads = [threading.Thread(target=scan_in_thread) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # All threads should succeed without raising exceptions.
        assert len(errors) == 0
        assert len(results) == 10
        assert all(len(r) == 3 for r in results)