import os
import zipfile
import posixpath
import logging
from datetime import datetime, timezone
from contracts import FileScanner, FileInfo, FileScannerError

logger = logging.getLogger(__name__)


class ZipFileScanner(FileScanner):
    """
    Scans zip file headers in-memory without extracting contents to disk.

    This implementation reduces I/O overhead and avoids creating temporary files
    by reading file metadata directly from the zip archive's central directory.
    """

    def __init__(self):
        """Initializes the ZipFileScanner."""
        pass  # No temporary directory or state is needed for this implementation.

    def get_input_file_path(self) -> list[FileInfo] | None:
        """
        Prompts the user for a zip file path and initiates the scan.

        This method repeatedly prompts the user until a valid file path is provided
        or the user cancels by entering a blank line.

        Returns:
            list[FileInfo] | None: A list of file information on success, or None if cancelled.
        """
        while True:
            print("\nPlease provide the path to your zipped project folder:")
            print("(Leave blank to cancel)")
            zip_path = input("File path: ").strip()
            
            if not zip_path:
                print("Operation cancelled.")
                return None

            try:
                return self._scan_zip_headers(zip_path)
            except FileScannerError as e:
                logger.error(f"Scan failed: {e}")
                print(f"Error: {e}")

    def _scan_zip_headers(self, zip_path: str) -> list[FileInfo]:
        """
        Validates and scans the headers of a zip file in-memory.

        This method reads the metadata for each item in the zip archive without
        extracting the files. It includes security checks to prevent Zip Slip
        vulnerabilities.

        Args:
            zip_path (str): The path to the zip file to be scanned.

        Returns:
            list[FileInfo]: A list of objects containing metadata for each file.
        """
        if not os.path.isfile(zip_path) or not str(zip_path).lower().endswith(".zip"):
             raise FileScannerError("Invalid zip file path.")

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_tree = []
                for info in zip_ref.infolist():
                    # --- Security Check ---
                    # Validate file path to prevent Zip Slip vulnerabilities.
                    if self._is_malicious_path(info.filename):
                        logger.warning(f"Blocked potential Zip Slip attack: Malicious path '{info.filename}' detected in zip file.")
                        continue

                    # Handle timestamp conversion with robust error handling.
                    try:
                        # The ZIP specification stores local time. Assume it's from the system's
                        # local timezone, then convert to UTC for standardization.
                        last_mod_naive = datetime(*info.date_time)
                        last_mod_local = last_mod_naive.astimezone()  # Apply local timezone
                        last_mod_aware = last_mod_local.astimezone(timezone.utc)  # Convert to UTC
                    except (TypeError, ValueError):
                        # A file entry might be a directory or have a malformed timestamp.
                        last_mod_aware = None
                        logger.warning(f"Could not parse timestamp for '{info.filename}', using None.")
                    
                    file_tree.append(FileInfo(
                        file_path=info.filename,  # The virtual path inside the zip
                        size=info.file_size,  # Will be 0 for directories
                        last_modified=last_mod_aware,
                        is_file=not info.is_dir() # Set flag correctly
                    ))
                return file_tree

        except zipfile.BadZipFile:
            raise FileScannerError("File is corrupted or not a zip.")
        except Exception as e:
            raise FileScannerError(f"Scan error: {e}")

    def _is_malicious_path(self, filename: str) -> bool:
        """
        Validates a path to protect against Zip Slip attacks.

        This method uses `posixpath` for cross-platform consistency when analyzing
        paths inside the zip file.

        Args:
            filename (str): The internal path of a file within the zip archive.

        Returns:
            bool: True if the path is considered malicious, otherwise False.
        """
        if not filename:
            logger.warning("Blocked empty filename in zip.")
            return True

        # Block absolute paths (works cross-platform for both '/' and 'C:/' style paths)
        if posixpath.isabs(filename):
            return True

        # Normalize the path to collapse segments like 'a/b/../c' into 'a/c'.
        normalized = posixpath.normpath(filename)

        # After normalization, any path starting with '..' attempts to traverse upwards.
        if normalized.startswith('..'):
            return True

        # Check for encoded traversal attempts that might bypass basic checks.
        # e.g., %2e is '.', %252e is a double-encoded '.'
        dangerous_patterns = ['%2e', '%252e']
        lowered = filename.lower()
        return any(pattern in lowered for pattern in dangerous_patterns)

    def cleanup(self):
        """Performs cleanup operations. No-op for this implementation."""
        pass  # No action is needed as no temporary files or resources are created.