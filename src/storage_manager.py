# This module handles all database interactions, including
# initializing the database and saving extracted file metadata.
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .contracts import StorageError, Storage, FileMetadata

logger = logging.getLogger(__name__)


class StorageManager(Storage):
    # Handles all database interactions

    def __init__(self, db_path: str = "skill_scope.db"):
        # Initializes the StorageManager with a path to the database.
        # Args:
        #     db_path: Path to the SQLite database file or a URI for in-memory DBs. Will determine later which is better
        self.db_path = db_path

    @contextmanager
    def get_db_connection(self):
        # Provides a managed database connection.
        # This context manager ensures the connection is properly opened,
        # transactions are committed or rolled back, and the connection is closed.
        conn = None
        try:
            # Determine if the db_path is a URI or a special in-memory identifier.
            # This allows sqlite3.connect to interpret the path correctly in both cases
            use_uri = self.db_path == ":memory:" or self.db_path.startswith("file:")
            conn = sqlite3.connect(self.db_path, uri=use_uri, timeout=5)
            yield conn # Yield the connection to the 'with' block
            conn.commit() # Commit changes if no exceptions occurred within the 'with' block
        except sqlite3.Error as e:
            if conn:
                conn.rollback() # Rollback changes on database error
            raise StorageError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close() # Always close the connection, regardless of success or failure

    def initialize_database(self):
        # Creates the database tables if they don't already exist.
        # This method also handles basic schema versioning.
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            # Check the current schema version stored in PRAGMA user_version.
            current_version = cursor.execute("PRAGMA user_version").fetchone()[0]

            # If the database version is less than 1, apply the initial schema.
            # This allows for future schema migrations (e.g., ALTER TABLE statements).
            if current_version < 1:
                logger.info("Database version is %d, initializing schema to version 1.", current_version)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_timestamp TEXT NOT NULL, # Stores scan time in ISO 8601 format (UTC)
                    filename TEXT NOT NULL,
                    size INTEGER NOT NULL DEFAULT 0,
                    last_modified TEXT, # Stores file modification time in ISO 8601 format (UTC)
                    extension TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'uncategorized',
                    is_file INTEGER NOT NULL DEFAULT 0 # Boolean stored as 0 for False, 1 for True
                )
            """)
                # Update the schema version to 1.
                cursor.execute("PRAGMA user_version = 1")
                
    def save_extracted_data(self, extracted_data: list[FileMetadata]):
        # Clears previous scan data and saves a new list of extracted file metadata
        # to the database in batches to conserve memory.
        # Note: For this version, previous data is cleared. Future versions will implement UPDATE / INSERT.
        if not extracted_data:
            logger.info("No data to save.")
            return
        
        insert_query = """
            INSERT INTO files (scan_timestamp, filename, size, last_modified, extension, category, is_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            # Clear the entire 'files' table to prevent data duplication from previous scans (obviously temporary)
            logger.info("Clearing previous scan data from 'files' table.")
            cursor.execute("DELETE FROM files")

            # Record the current scan time in UTC ISO 8601 format.
            scan_time = datetime.now(timezone.utc).isoformat()
            batch_size = 1000 # Define batch size for memory efficiency during insertion
            total_saved = 0

            # Iterate through the extracted_data list in defined batches.
            for i in range(0, len(extracted_data), batch_size):
                batch = extracted_data[i:i + batch_size]
                records_to_insert = []
                # Prepare records for batch insertion.
                for item in batch:
                    records_to_insert.append((
                        scan_time,
                        item.filename,
                        item.size,
                        # Convert datetime object to ISO 8601 string for storage.
                        item.last_modified.isoformat() if item.last_modified else None,
                        item.extension,
                        item.category,
                        int(item.is_file) # Convert boolean to integer (0 or 1) for database storage
                    ))
                
                # Execute batch insert for the current batch of records.
                cursor.executemany(insert_query, records_to_insert)
                total_saved += len(records_to_insert)
                logger.info("Saved batch of %d records.", len(records_to_insert))

            logger.info("Successfully saved a total of %d records to the database.", total_saved)

    def read_all_data(self) -> iter[FileMetadata]:
        # Streams all file metadata records from the database using a generator.
        # This prevents loading the entire dataset into memory at once, improving scalability.
        with self.get_db_connection() as conn:
            # Configure row_factory to return rows as dict-like objects, allowing access by column name.
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files ORDER BY filename")

            # Iterate over results using fetchone() to stream data row by row.
            while True:
                row = cursor.fetchone()
                if row is None:
                    break # No more rows to fetch, exit loop
                
                last_modified = None
                if row["last_modified"]:
                    try:
                        # Convert ISO 8601 string back to a datetime object.
                        last_modified = datetime.fromisoformat(row["last_modified"])
                    except ValueError:
                        # Log a warning if a date string is malformed
                        logger.warning("Could not parse malformed date string '%s' for file '%s'.", row["last_modified"], row["filename"])

                # Yield a FileMetadata object for each row, allowing the caller to process data incrementally.
                yield FileMetadata(
                    filename=row["filename"],
                    size=row["size"],
                    last_modified=last_modified,
                    extension=row["extension"],
                    category=row["category"],
                    is_file=bool(row["is_file"]) # Convert integer (0 or 1) back to boolean
                )
