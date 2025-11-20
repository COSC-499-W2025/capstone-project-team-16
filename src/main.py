### This will act as our orchestrator for coordinating scan tasks

from __future__ import annotations
from permission_manager import get_user_consent
from file_parser import get_input_file_path
from metadata_extractor import base_extraction, detailed_extraction
from alternative_analysis import analyze_projects
from dataclasses import dataclass, field
from typing import Protocol

print("Welcome to Skill Scope!")
print("~~~~~~~~~~~~~~~~~~~~~~~")


if (get_user_consent()):
    file_list = get_input_file_path()
else:
    exit()

if file_list:
    #call metadata extractor and pass file_path
    #should get a list of files with accompanying metadata.
    scraped_data = base_extraction(file_list)

    advanced_data = detailed_extraction(scraped_data)
    
    #for analysis part
    analyze_projects(scraped_data)



"""
Orchestrator Template

This file only defines:
- Minimal contracts
- A thin Orchestrator with a single run() method
- A stub main() for a proposed wiring location

No actual logic, data types not finalized, etc.
"""



# Minimal data contract
@dataclass
class ScanSummary:
    scanned_files: int = 0
    notes: list[str] = field(default_factory=list)

# Minimal service contracts
class ConsentGateway(Protocol):
    def request_consent(self) -> bool: ...

class FileScanner(Protocol):
    def scan(self) -> int: ...  

class MetadataExtractor(Protocol):
    def extract(self) -> None: ...

class AnalysisEngine(Protocol):
    def analyze(self) -> None: ...

class Exporter(Protocol):
    def export(self) -> None: ...

class Storage(Protocol):
    def save(self) -> None: ...

# Orchestrator skeleton
class Orchestrator:
    """Make implementations for each dependency, implement run() when ready.
    Until then, it returns a blank summary.
    """

    def __init__(
        self,
        *,
        consent_gateway: ConsentGateway | None = None,
        file_scanner: FileScanner | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        analysis_engine: AnalysisEngine | None = None,
        exporter: Exporter | None = None,
        storage: Storage | None = None,
    ) -> None:
        self.consent_gateway = consent_gateway
        self.file_scanner = file_scanner
        self.metadata_extractor = metadata_extractor
        self.analysis_engine = analysis_engine
        self.exporter = exporter
        self.storage = storage

    def run(self) -> ScanSummary:
        """
        High-level flow (to be implemented):

        1) consent = consent_gateway.request_consent()
        2) inventory_count = file_scanner.scan()
        3) metadata_extractor.extract()
        4) analysis_engine.analyze()
        5) exporter.export()
        6) storage.save()
        7) return ScanSummary(scanned_files=inventory_count, notes=[...])

        For now, returns an empty summary as a placeholder.
        """
        # TODO: implement the flow above once components exist
        return ScanSummary()

# CLI entry
def main() -> None:
    # TODO: Wire real components like:
    # orchestrator = Orchestrator(
    #     consent_gateway=MyConsentGateway(),
    #     file_scanner=MyFileScanner(),
    #     metadata_extractor=MyMetadataExtractor(),
    #     analysis_engine=MyAnalysisEngine(),
    #     exporter=MyExporter(),
    #     storage=MyStorage(),
    # )
    # summary = orchestrator.run()
    # print(summary)
    pass

if __name__ == "__main__":
    main()
