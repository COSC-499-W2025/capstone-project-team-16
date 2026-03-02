import unittest
import os
import sys
import tempfile
import shutil
import zipfile
import sqlite3

# Adjust path to import src
# Assuming this test file is in <project_root>/tests/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from file_parser import compute_file_hash, check_file_validity
import db

class TestDeduplication(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        
        # Initialize DB schema
        with sqlite3.connect(self.db_path) as conn:
            db.ensure_db_initialized(conn)

    def tearDown(self):
        # Cleanup temp files and DB
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                # Windows workaround: SQLite lock might linger
                import gc
                import time
                gc.collect()
                time.sleep(0.1)
                try:
                    os.remove(self.db_path)
                except PermissionError:
                    pass

    def create_dummy_file(self, filename, content=b"test content"):
        path = os.path.join(self.test_dir, filename)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def create_dummy_zip(self, zip_name, files):
        zip_path = os.path.join(self.test_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for fname, content in files.items():
                zf.writestr(fname, content)
        return zip_path

    def test_compute_file_hash_identical(self):
        """
        Test that identical files produce the same hash.
        
        SCENARIO: Two separate files are created with the exact same binary content.
        EXPECTED: compute_file_hash returns the same SHA256 string for both.
        """
        file1 = self.create_dummy_file("file1.txt", b"same content")
        file2 = self.create_dummy_file("file2.txt", b"same content")
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        self.assertEqual(hash1, hash2)
        self.assertIsNotNone(hash1)

    def test_compute_file_hash_different(self):
        """
        Test that different files produce different hashes.
        
        SCENARIO: Two files are created with different binary content.
        EXPECTED: compute_file_hash returns different SHA256 strings.
        """
        file1 = self.create_dummy_file("file1.txt", b"content A")
        file2 = self.create_dummy_file("file2.txt", b"content B")
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        self.assertNotEqual(hash1, hash2)

    def test_check_file_validity_returns_hash(self):
        """
        Test that check_file_validity returns the correct tuple (file_tree, zip_hash).
        
        SCENARIO: A valid ZIP file is processed by check_file_validity.
        EXPECTED: The function returns a tuple where the second element matches the manually computed hash of the ZIP file.
        """
        # Create a valid zip
        zip_path = self.create_dummy_zip("test.zip", {"a.txt": "content"})
        
        # Calculate expected hash manually
        expected_hash = compute_file_hash(zip_path)
        
        # Run function
        result = check_file_validity(zip_path)
        
        self.assertIsNotNone(result)
        file_tree, returned_hash = result
        
        self.assertEqual(returned_hash, expected_hash)
        self.assertTrue(len(file_tree) > 0)
        self.assertEqual(file_tree[0]['filename'].endswith('a.txt'), True)

    def test_db_scan_exists(self):
        """
        Test the scan_exists function in db.py.
        
        SCENARIO: Check existence of a hash before and after saving a scan.
        EXPECTED: Returns False initially, then True after save_full_scan is called.
        """
        test_hash = "abc123hash_unique"
        
        # Initially should not exist
        self.assertFalse(db.scan_exists(test_hash, db_path=self.db_path))
        
        # Save a scan with this hash
        dummy_results = {
            "project_summaries": [],
            "zip_hash": test_hash
        }
        
        db.save_full_scan(dummy_results, "basic", True, db_path=self.db_path)
        
        # Now should exist
        self.assertTrue(db.scan_exists(test_hash, db_path=self.db_path))

    def test_db_scan_exists_none(self):
        """
        Test that scan_exists returns False for None input.
        
        SCENARIO: scan_exists is called with None.
        EXPECTED: Returns False (graceful handling of missing hash).
        """
        self.assertFalse(db.scan_exists(None, db_path=self.db_path))

if __name__ == '__main__':
    unittest.main()
