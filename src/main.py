"""
Main entry point for the application.
This file is responsible for wiring up the application dependencies and
running the orchestrator.
"""
import logging
import os


"""
Current problems (as summarized by gemini). Most are related to the fact that this needs to use mock data

1. Critical Data Loss in StorageManager
The save_extracted_data method is fundamentally destructive.

The Flaw: cursor.execute("DELETE FROM files") is called every time data is saved.

The Consequence: This application cannot maintain historical data. Each scan wipes the entire database and replaces it with the new snapshot. If you scan one directory today and a different one tomorrow, the results from today are erased. This design is highly problematic for a tool that implies building a scope or repository of information.

The Fix: You must implement an upsert (update or insert) strategy. Use INSERT ... ON CONFLICT(filename) DO UPDATE SET ... to update records for files that have changed and insert new ones. The DELETE operation is incorrect for this domain.

2. Incomplete Orchestrator Design
The Orchestrator fails to orchestrate the full process defined by your contracts.

The Flaw: The Orchestrator only knows about MetadataExtractor and Storage. It is completely ignorant of the AnalysisEngine and Exporter protocols defined in contracts.py.

The Consequence: The Orchestrator.run method's job is incomplete. It just dumps data to the database. The main function's try...except block even catches AnalysisError and ExportError, but it's impossible for the Orchestrator to raise them.

The Fix: The Orchestrator's __init__ method should also accept analysis_engine: AnalysisEngine and exporter: Exporter. Its run method should execute the full, logical pipeline:

extraction_result = self.metadata_extractor.base_extraction(...)

analysis_result = self.analysis_engine.analyze(extraction_result.succeeded)

self.storage.save_extracted_data(extraction_result.succeeded)

self.storage.save_analysis_results(analysis_result) (This implies the Storage protocol also needs to be expanded).

self.exporter.export(analysis_result)

3. Inefficient Data Flow
The implied data flow is [In-Memory List] -> [Database] -> [In-Memory List] -> [Analysis]. This is redundant.

The Flaw: The Orchestrator saves the extracted data, and the (hypothetical) AnalysisEngine would then have to immediately read it back using storage.read_all_data().

The Consequence: You are performing a pointless database round-trip. The data (extraction_result.succeeded) is already in memory.

The Fix: As described in point #2, the Orchestrator should pass the in-memory extraction_result.succeeded list directly to the AnalysisEngine before, or during, the save operation.

4. Contract-Implementation Mismatch
Your Storage protocol in contracts.py is lying.

The Flaw: The Storage protocol defines read_all_data(self) -> list[FileMetadata]: ....

The Implementation: Your StorageManager.read_all_data method correctly and wisely uses yield to create a generator, saving memory. Its actual return type is Iterator[FileMetadata].

The Consequence: The implementation does not match the contract it supposedly fulfills. The contract promises to load everything into a list, which is a bad design for a potentially large dataset. The implementation is superior to the contract.

The Fix: Change the protocol in contracts.py to match the better implementation: def read_all_data(self) -> Iterator[FileMetadata]: ... (requires from typing import Iterator).

5. Misleading Error Handling
The main.py error handling is disconnected from reality.

The Flaw: main.py catches (FileScannerError, ExtractionError, StorageError, AnalysisError, ExportError).

The Consequence: The AnalysisError and ExportError exceptions are dead code. Nothing in the try block can possibly raise them because the Orchestrator does not use the components that would raise them. This gives a false sense of an application's completeness.

The Fix: Remove AnalysisError and ExportError from the except tuple until those components are actually wired into the execution path.






"""


# --- Actual Imports (commented out for mock implementation) ---
# from .file_parser import FileParser
# from .permission_manager import PermissionManager
# from .metadata_extractor import MetadataExtractor
# -------------------------------------------------------------

# The mocks are temporarily defined here for context
from datetime import datetime, timezone
from .contracts import (
    ConsentGateway, ConsentResult, FileScanner, FileInfo, MetadataExtractor, FileMetadata,
    ExtractionResult
)

class MockPermissionManager(ConsentGateway):
    def get_user_consent(self) -> ConsentResult: return ConsentResult.GRANTED

class MockFileParser(FileScanner):
    def get_input_file_path(self) -> list[FileInfo] | None:
        # Correctly generate a timezone-aware UTC datetime.
        return [FileInfo(filename="src/mock_file.py", size=1024, last_modified=datetime.now(timezone.utc), is_file=True)]

class MockMetadataExtractor(MetadataExtractor):
    def base_extraction(self, file_list: list[FileInfo]) -> ExtractionResult:
        f = file_list[0]
        return ExtractionResult(succeeded=[FileMetadata(filename=f.filename, size=f.size, last_modified=f.last_modified, extension=".py", category="source_code", is_file=True)], failed=[])

from .storage_manager import StorageManager
from .orchestrator import Orchestrator
from .contracts import (
    ConsentResult,
    FileScannerError,
    ExtractionError,
    StorageError,
    AnalysisError, ExportError # For future use
)

# Read configuration from environment variables with semi random defaults.
DB_PATH = os.getenv("SKILLSCOPE_DB_PATH", "skill_scope.db")

# CLI entry
def main() -> None:
    # Initializes components, handles user interaction, and runs the orchestrator.
    # Configure logging to show timestamp, level, and message. Logging needs to be integrated separately later
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("~~~~~~~~~~~~~~~~~~~~~~~")

    # Instantiate components with direct I/O for the CLI
    # --- Actual Implementation (commented out) ---
    # permission_manager = PermissionManager()
    # file_scanner = FileParser()
    permission_manager = MockPermissionManager()
    file_scanner = MockFileParser()
    storage = StorageManager(db_path=DB_PATH)

    try:
        # 1. Handle user-facing interactions first
        consent = permission_manager.get_user_consent()
        if consent != ConsentResult.GRANTED:
            # Handles DENIED and CANCELLED
            return # Exit gracefully

        # 2. Initialize database once at startup. This is an explicit setup step, currently it wipes clean on every run
        storage.initialize_database()

        # 3. Get file list from the user
        file_list = file_scanner.get_input_file_path()
        if not file_list:
            print("Scan aborted: No valid file list was provided.")
            return

        # 4. Instantiate the core logic and run it with the prepared data
        orchestrator = Orchestrator(
            # --- Actual Implementation (commented out) ---
            # metadata_extractor=MetadataExtractor(),
            metadata_extractor=MockMetadataExtractor(),
            storage=storage,
        )
        summary = orchestrator.run(file_list=file_list)
        print("\n--- Scan Summary ---")
        print(f"Initial files scanned: {summary.scanned_files}")
        print(f"Files processed and saved: {summary.processed_files}")

    except (FileScannerError, ExtractionError, StorageError, AnalysisError, ExportError) as e:
        logging.error("A known error occurred during the scan: %s", e)
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user. Exiting.")
    except Exception as e:
        # For unexpected errors, log the full traceback for debugging (Will be tweaked with actual logging class plugged into something later)
        logging.critical("An unexpected error occurred.", exc_info=True)
        print(f"\nAn unexpected critical error occurred. Please check the logs.")

if __name__ == "__main__":
    main()
