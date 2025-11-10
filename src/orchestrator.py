# The Orchestrator class that coordinates the application's core workflow.

import logging
from src.contracts import (
    ScanSummary,
    MetadataExtractor,
    Storage,
    FileInfo,
    ExtractionResult,
)

logger = logging.getLogger(__name__)

class Orchestrator:
    # Coordinates the application's workflow by calling various services

    def __init__(
        self,
        *,
        metadata_extractor: MetadataExtractor,
        storage: Storage,
    ) -> None:
        self.metadata_extractor = metadata_extractor
        self.storage = storage

    def run(self, file_list: list[FileInfo]) -> ScanSummary:
        # Executes the core workflow: extraction and storage. This method is non-interactive and expects all inputs to be provided.

        # 1. Extract metadata from the raw file list
        extraction_result: ExtractionResult = self.metadata_extractor.base_extraction(file_list)

        # Log any failures during extraction.
        if extraction_result.failed:
            logger.warning("Extraction failed for %d files:", len(extraction_result.failed))
            for failure in extraction_result.failed:
                logger.warning("  - %s: %s", failure.file_info.filename, failure.reason)

        # 2. Save the structured data
        self.storage.save_extracted_data(extraction_result.succeeded)
            
        # 3. Create a summary of the operation.
        summary = ScanSummary(
            scanned_files=len(file_list),
            processed_files=len(extraction_result.succeeded)
        )
        logger.info("Orchestration complete. Succeeded: %d, Failed: %d.", len(extraction_result.succeeded), len(extraction_result.failed))
        return summary