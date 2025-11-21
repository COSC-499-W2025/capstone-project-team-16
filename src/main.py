"""
Brief summary of module purpose.

This module serves as the main entry point for the SkillScope application.
It is responsible for initializing and wiring up all dependencies, handling
user consent, and orchestrating the primary workflow.
"""
from __future__ import annotations
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contracts import (
    ConsentResult,
    FileScannerError,
    ExtractionError,
    StorageError,
)
from utils.logging_config import setup_logging
from core.orchestrator import Orchestrator
from contracts import ConsentGateway, FileScanner, MetadataExtractor, Storage

# --- Configuration ---
DB_PATH = os.getenv("SKILLSCOPE_DB_PATH", "skill_scope.db")
FILTER_PATH = os.getenv(
    "SKILLSCOPE_FILTER_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "extractor_filters.json")
)

logger = logging.getLogger(__name__)


def main(
    permission_manager: ConsentGateway | None = None,
    file_scanner: FileScanner | None = None,
    metadata_extractor: MetadataExtractor | None = None,
    storage: Storage | None = None,
) -> None:
    """
    Runs the main application workflow.

    This function orchestrates the entire process, from dependency injection
    and user consent to file scanning, extraction, and summarization. It accepts
    optional dependencies to facilitate testing.

    Args:
        permission_manager (ConsentGateway | None): The consent management component.
        file_scanner (FileScanner | None): The file scanning component.
        metadata_extractor (MetadataExtractor | None): The metadata extraction component.
        storage (Storage | None): The data storage component.
    """
    scanner_instance = file_scanner
    try:
        setup_logging()

        print("~~~~~~~~~~~~~~~~~~~~~~~\nSkillScope Skeleton Runner\n~~~~~~~~~~~~~~~~~~~~~~~")

        # --- Dependency Injection ---
        # If components are not passed in (i.e., running in production), create them.
        if permission_manager is None:  # Production mode initialization
            RUN_MODE = os.getenv("SKILLSCOPE_MODE", "PROD").upper()
            if RUN_MODE == "PROD":
                logger.info("Running in PROD mode. Loading real implementations.")
                from components.scanner import ZipFileScanner
                from components.extractor import MetadataExtractorImpl
                from components.permissions import ConsolePermissionManager
                from components.storage import StorageManager
                
                permission_manager = ConsolePermissionManager()
                scanner_instance = ZipFileScanner()
                metadata_extractor = MetadataExtractorImpl(filters_path=FILTER_PATH)
                storage = StorageManager(db_path=DB_PATH)
                logger.info("Check 'skill_scope.db' for persisted data.")
            else:
                print("Running in DEV mode")  # For tests
                logger.info("Running in DEV mode. Loading mock implementations.")  # For logs
                logger.info("Running in DEV mode. Loading mock implementations.")
                from utils.mocks import MockPermissionManager, MockFileScanner, MockMetadataExtractor, MockStorage
                
                permission_manager = MockPermissionManager()
                scanner_instance = MockFileScanner()
                metadata_extractor = MockMetadataExtractor()
                storage = MockStorage()

        permission_manager: "ConsentGateway"
        metadata_extractor: "MetadataExtractor"
        storage: "Storage"

        # --- Main Workflow ---

        # 1. Handle user-facing interactions first.
        assert permission_manager is not None
        consent = permission_manager.get_user_consent()
        if consent != ConsentResult.GRANTED:
            # This block handles both DENIED and CANCELLED results, exiting gracefully.
            print("Consent denied. Exiting.")
            return 

        # 2. Initialize database
        assert storage is not None
        storage.initialize_database()

        # 3. Get file list from the user.
        assert scanner_instance is not None
        scanned_files = scanner_instance.get_input_file_path()
        if not scanned_files:
            print("No files found.")
            return

        # 4. Instantiate the core logic and run it with the prepared data.
        orchestrator = Orchestrator(
            metadata_extractor=metadata_extractor,
            storage=storage,
        )
        summary = orchestrator.run(scanned_files=scanned_files)

        # 5. Continue implementation (analysis)
        #TODO: Implement the analysis stage using the extracted data.
        print("\n--- Scan Summary ---")
        print(f"Scan ID:         {summary.scan_id}")
        print(f"Files Scanned:   {summary.scanned_files}")
        print(f"Files Processed: {summary.processed_files}")

        if summary.failures:
            print(f"Failures:        {len(summary.failures)}")
            for failure in summary.failures:
                print(f"  - {failure.file_path}: {failure.reason}")

    except (ValueError, FileNotFoundError) as e:
        # Catches configuration errors, e.g., from MetadataExtractorImpl initialization.
        logger.critical(f"Configuration error: {e}", exc_info=True)
        print(f"\n❌ Configuration Error: {e}")
        print("Please check your filter file and application setup, then try again.")
    except RuntimeError as e:
        # Catches unexpected errors during setup, such as filter loading.
        logger.critical(f"A critical runtime error occurred during setup: {e}", exc_info=True)
        print(f"\n❌ Critical Error: {e}")
    except (
        FileScannerError, ExtractionError, StorageError
    ) as e:
        # Catches custom application-specific errors during the workflow.
        logger.error(f"Operation failed: {e}", exc_info=True)
        print(f"\n❌ Operation Failed: {e}")
    except (KeyboardInterrupt, EOFError):
        # Gracefully handle user cancellation.
        print("\nOperation cancelled by user. Exiting.")
    except Exception as e:
        logging.critical("An unexpected error occurred.", exc_info=True)
        print(f"\nAn unexpected critical error occurred. Please check the logs for details.")
    finally:
        # Ensure cleanup is always called if the scanner was initialized.
        if scanner_instance:
            scanner_instance.cleanup()

if __name__ == "__main__":
    main()
