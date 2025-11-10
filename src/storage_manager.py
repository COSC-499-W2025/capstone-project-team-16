"""
This module handles all database interactions for Skill Scope, including
initializing the database and saving extracted file metadata.
"""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from src.contracts import FileMetadata, StorageError, Storage

logger = logging.getLogger(__name__)

class StorageManager:
    """Handles all database interactions for Skill Scope."""

    def __init__(self, db_path: str = "skill_scope.db"):
        """
        Initializes the StorageManager with a path to the database.
        Args:
            db_path: Path to the SQLite database file or a URI for in-memory DBs.
        """
        self.db_path = db_path

    @contextmanager
    def get_db_connection(self):
        """Provides a managed database connection."""
        conn = None
        try:
            # Use uri=True if the path is a URI, necessary for shared in-memory DBs.
            use_uri = self.db_path.startswith("file:")
            conn = sqlite3.connect(self.db_path, uri=use_uri, timeout=5)
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise StorageError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close()

    def initialize_database(self):
        """Creates the database tables if they don't already exist."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_timestamp TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    size INTEGER NOT NULL DEFAULT 0,
                    last_modified TEXT,
                    extension TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'uncategorized',
                    is_file INTEGER NOT NULL DEFAULT 0
                )
            """)

    def save_extracted_data(self, extracted_data: list[FileMetadata]):
        """Saves a list of extracted file data to the database."""
        scan_time = datetime.now().isoformat()
        
        insert_query = """
            INSERT INTO files (scan_timestamp, filename, size, last_modified, extension, category, is_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        records_to_insert = []
        for item in extracted_data:
            record = (
                scan_time,
                item.filename,
                item.size,
                item.last_modified.isoformat() if item.last_modified else None,
                item.extension,
                item.category,
                int(item.is_file)
            )
            records_to_insert.append(record)

        if not records_to_insert:
            logger.info("No valid records were provided to save.")
            return

        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(insert_query, records_to_insert)
            logger.info("Successfully saved %d records to the database.", len(records_to_insert))
