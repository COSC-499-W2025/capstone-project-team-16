"""
Main entry point for the Skill Scope application.
This file is responsible for wiring up the application dependencies and
running the orchestrator.
"""
import logging
import os
from file_parser import FileParser
from storage_manager import StorageManager
from permission_manager import PermissionManager
from metadata_extractor import MetadataExtractor
from orchestrator import Orchestrator
from src.contracts import ConsentResult, FileScannerError, ExtractionError, StorageError

# Read configuration from environment variables with sensible defaults.
DB_PATH = os.getenv("SKILLSCOPE_DB_PATH", "skill_scope.db")

# CLI entry
def main() -> None:
    """Initializes components, handles user interaction, and runs the orchestrator."""
    print("Welcome to Skill Scope!")
    print("~~~~~~~~~~~~~~~~~~~~~~~")

    # Instantiate components with direct I/O for the CLI
    permission_manager = PermissionManager()
    file_scanner = FileParser()
    storage = StorageManager(db_path=DB_PATH)

    try:
        # 1. Handle user-facing interactions first
        consent = permission_manager.get_user_consent()
        if consent != ConsentResult.GRANTED:
            # Handles DENIED and CANCELLED
            return # Exit gracefully

        # 2. Initialize database once at startup
        storage.initialize_database()

        # 3. Get file list from the user
        file_list = file_scanner.get_input_file_path()
        if not file_list:
            print("Scan aborted: No valid file list was provided.")
            return

        # 4. Instantiate the core logic and run it with the prepared data
    orchestrator = Orchestrator(
        metadata_extractor=MetadataExtractor(),
        storage=storage,
    )
        summary = orchestrator.run(file_list=file_list)
        print("\n--- Scan Summary ---")
        print(summary)

    except (FileScannerError, ExtractionError, StorageError) as e:
        print(f"\nA critical error occurred: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user. Exiting.")
    except Exception as e:
        logging.exception("An unexpected critical error occurred.")
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
