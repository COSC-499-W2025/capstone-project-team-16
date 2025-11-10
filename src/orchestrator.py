"""
The Orchestrator class that coordinates the application's core workflow.
"""
from __future__ import annotations
import logging
from src.contracts import (
    ScanSummary,
    MetadataExtractor,
    Storage,
    AnalysisEngine,
    Exporter,
)

logger = logging.getLogger(__name__)

class Orchestrator:
    """Coordinates the application's workflow by calling various services."""

    def __init__(
        self,
        *,
        metadata_extractor: MetadataExtractor,
        storage: Storage,
        analysis_engine: AnalysisEngine | None = None,
        exporter: Exporter | None = None,
    ) -> None:
        self.metadata_extractor = metadata_extractor
        self.storage = storage
        self.analysis_engine = analysis_engine
        self.exporter = exporter

    def run(self, file_list: list) -> ScanSummary:
        """
        Executes the core workflow: extraction, storage, and analysis.
        This method is non-interactive and expects all inputs to be provided.
        """
        # 1. Extract metadata from the raw file list
        extracted_data = self.metadata_extractor.base_extraction(file_list)

        # 2. Save the structured data
        if extracted_data:
            self.storage.save_extracted_data(extracted_data)
            summary_note = "Scan completed and data saved to database."
        else:
            logger.info("No data was extracted to save to the database.")
            summary_note = "Scan completed, but no data was extracted to save."

        # 3. Optional analysis and export steps
        if self.analysis_engine:
            # Pass data explicitly to the next step in the pipeline
            analysis_results = self.analysis_engine.analyze(extracted_data)
            # In a real scenario, these results would be used.
        
        if self.exporter:
            self.exporter.export(extracted_data)
            
        summary = ScanSummary(scanned_files=len(file_list))
        summary.notes.append(summary_note)
        return summary