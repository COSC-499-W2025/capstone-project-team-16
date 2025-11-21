"""
Coordinates the core application workflow.

This module defines the Orchestrator class, which is responsible for managing the sequence of operations like extraction and storage.
"""

import logging
import uuid
from contracts import (
    ScanSummary,
    MetadataExtractor,
    Storage,
    FileInfo,
    ExtractionFailure,
    ExtractionResult,
)
 
logger = logging.getLogger(__name__)

class Orchestrator:
    """Coordinates the application's workflow by calling various services."""

    def __init__(
        self,
        *,
        metadata_extractor: MetadataExtractor,
        storage: Storage,
    ) -> None:
        """
        Initializes the Orchestrator.

        Args:
            metadata_extractor (MetadataExtractor): The component for extracting metadata.
            storage (Storage): The component for persisting data.
        """
        self.metadata_extractor = metadata_extractor
        self.storage = storage
 
    def run(self, scanned_files: list[FileInfo]) -> ScanSummary:
        """
        Executes the core workflow: extraction and storage.

        This method is non-interactive and expects all inputs to be provided.

        Args:
            scanned_files (list[FileInfo]): A list of raw file information from the scanner.

        Returns:
            ScanSummary: A summary of the completed operation.
        """
        # 1. Extract metadata from the raw file list.
        extraction_result: ExtractionResult = self.metadata_extractor.base_extraction(scanned_files)
 
        # Log any failures that occurred during the extraction process.
        if extraction_result.failed:
            logger.warning("Extraction failed for %d files:", len(extraction_result.failed))
            for failure in extraction_result.failed:
                logger.warning("  - %s: %s", failure.file_path, failure.reason)

        # 2. Save the structured data to the database.
        self.storage.save_extracted_data(extraction_result.succeeded)
            
        # 3. Create a summary of the operation.
        scan_id = str(uuid.uuid4())
        summary = ScanSummary(
            scan_id=scan_id,
            scanned_files=len(scanned_files),
            processed_files=len(extraction_result.succeeded),
            failures=extraction_result.failed,
        )
        logger.info("Orchestration complete. Succeeded: %d, Failed: %d.", len(extraction_result.succeeded), len(extraction_result.failed))
        return summary