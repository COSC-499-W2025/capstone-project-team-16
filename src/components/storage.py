"""
Manages all database interactions for the application.

This module is responsible for initializing the database schema, handling
connections, and persisting extracted file metadata.
"""
import logging
import sqlite3
from contextlib import contextmanager
from typing import Iterator
from datetime import datetime, timezone
from contracts import StorageError, Storage, FileMetadata

logger = logging.getLogger(__name__)


class StorageManager(Storage):
    """Handles all database interactions using SQLite."""

    def __init__(self, db_path: str = "skill_scope.db"):
        """
        Initializes the StorageManager with a path to the database.

        Args:
            db_path (str): Path to the SQLite database file. Can also be a URI
                           for special configurations like in-memory databases.
        """
        self.db_path = db_path

    @contextmanager
    def get_db_connection(self):
        """
        Provides a managed database connection with transactional integrity.

        This context manager ensures that the connection is properly opened,
        and that transactions are committed on success or rolled back on
        error. The connection is always closed upon exit.

        Yields:
            sqlite3.Connection: The active database connection.

        Raises:
            StorageError: If a database operation fails.
        """
        conn = None
        try:
            # Determine if the db_path is a URI or a special in-memory identifier
            # to allow sqlite3.connect to interpret it correctly.
            use_uri = self.db_path == ":memory:" or self.db_path.startswith("file:")
            conn = sqlite3.connect(self.db_path, uri=use_uri, timeout=5)
            yield conn  # Yield the connection to the 'with' block
            conn.commit()  # Commit changes if no exceptions occurred
        except sqlite3.Error as e:
            if conn:
                conn.rollback()  # Rollback changes on any database error
            raise StorageError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close()  # Always close the connection

    def initialize_database(self):
        """
        Creates the database tables if they do not already exist.

        This method also implements a basic schema versioning system using
        SQLite's `PRAGMA user_version`.
        """
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            current_version = cursor.execute("PRAGMA user_version").fetchone()[0]
            
            # If the version is less than 3, the database is either new or outdated.
            # This check allows for future schema migrations (e.g., using ALTER TABLE).
            if current_version < 3:
                logger.info("Database version is %d, initializing/upgrading schema to version 3.", current_version)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id INTEGER PRIMARY KEY AUTOINCREMENT,      -- Unique ID for each file record
                    scan_timestamp TEXT NOT NULL,                   -- Scan time in ISO 8601 format (UTC)
                    file_path TEXT NOT NULL,                        -- Full path of the file within the project
                    size INTEGER NOT NULL,                          -- File size in bytes
                    last_modified TEXT,                             -- File modification time in ISO 8601 format (UTC)
                    extension TEXT NOT NULL,                        -- File extension (e.g., '.py')
                    category TEXT NOT NULL DEFAULT 'uncategorized', -- Assigned category (e.g., 'source_code')
                    is_file INTEGER NOT NULL,                       -- Boolean stored as 0 for False, 1 for True
                    language TEXT NOT NULL DEFAULT 'undefined'      -- Programming language, if applicable
                )
                """)
                # Add an index on file_path for faster sorting and lookups.
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path)")

                # Update the schema version to 3.
                cursor.execute("PRAGMA user_version = 3")
                
    def save_extracted_data(self, extracted_data: list[FileMetadata]):
        """
        Saves a list of extracted file metadata to the database.

        This implementation first clears all previous scan data before inserting
        the new records in batches to conserve memory.
        #TODO: Future versions should implement an UPDATE/INSERT logic instead of a destructive DELETE.

        Args:
            extracted_data (list[FileMetadata]): The list of metadata to save.
        """
        if not extracted_data:
            logger.info("No data to save.")
            return
        
        insert_query = """
            INSERT INTO files (scan_timestamp, file_path, size, last_modified, extension, category, is_file, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Clear previous scan data to ensure a fresh start.
            cursor.execute("DELETE FROM files")

            # Record the current scan time in UTC ISO 8601 format.
            scan_time = datetime.now(timezone.utc).isoformat()
            batch_size = 1000  # Define batch size for memory-efficient insertion
            total_saved = 0

            for i in range(0, len(extracted_data), batch_size):
                batch = extracted_data[i:i + batch_size]
                records_to_insert = []
                # Prepare records for batch insertion.
                for item in batch:
                    records_to_insert.append((
                        scan_time,
                        item.file_path,
                        item.size,
                        # Convert datetime object to ISO 8601 string for storage
                        item.last_modified.isoformat() if item.last_modified else None,
                        item.extension,
                        item.category,
                        int(item.is_file),  # Convert boolean to integer (0 or 1)
                        item.language
                    ))
                
                # Execute batch insert for the current batch of records.
                cursor.executemany(insert_query, records_to_insert)
                total_saved += len(records_to_insert)
                logger.info("Saved batch of %d records.", len(records_to_insert))

            logger.info("Successfully saved a total of %d records to the database.", total_saved)

    def read_all_data(self) -> Iterator[FileMetadata]:
        """
        Streams all file metadata records from the database.

        This method uses a generator to yield records one by one, which prevents
        loading the entire dataset into memory and improves scalability.

        Yields:
            FileMetadata: An object representing a single file's metadata.
        """
        with self.get_db_connection() as conn:
            # Configure row_factory to return dict-like rows for access by column name.
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files ORDER BY file_path")

            while True:
                row = cursor.fetchone()
                if row is None:
                    break  # Exit loop when no more rows are available
                
                last_modified = None
                if row["last_modified"]:
                    try:
                        last_modified = datetime.fromisoformat(row["last_modified"])
                    except ValueError:
                        # Log a warning if a date string is malformed and cannot be parsed.
                        logger.warning("Could not parse malformed date string '%s' for file '%s'.", row["last_modified"], row["file_path"])

                # Yield a FileMetadata object, allowing the caller to process data incrementally.
                yield FileMetadata(
                    file_path=row["file_path"],
                    size=row["size"],
                    last_modified=last_modified,
                    extension=row["extension"],
                    category=row["category"],
                    is_file=bool(row["is_file"]),  # Convert integer back to boolean
                    language=row["language"]
                )
