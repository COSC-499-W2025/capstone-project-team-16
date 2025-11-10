"""
Centralized contracts for the application.

This file defines the shared data structures (DTOs), service protocols,
and custom exceptions that form the application's core architectural contracts.
All implementation modules should depend on this file, not on each other.

"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Protocol, Any, TypeVar

# --- Custom Exceptions ---

class FileScannerError(Exception):
    """Custom exception for file scanning failures."""
    pass

class ExtractionError(Exception):
    """Custom exception for metadata extraction failures."""
    pass

class StorageError(Exception):
    """Custom exception for database-related failures."""
    pass

class AnalysisError(Exception):
    """Custom exception for analysis failures."""
    pass

class ExportError(Exception):
    """Custom exception for export failures."""
    pass

# --- Data Transfer Objects (DTOs) ---

@dataclass(frozen=True)
class FileInfo:
    # A raw, unprocessed file record from the scanner
    filename: str
    size: int
    last_modified: datetime | None
    is_file: bool

@dataclass(frozen=True)
class FileMetadata:
    # A fully processed and categorized file record
    filename: str
    size: int
    last_modified: datetime | None
    extension: str
    category: str
    is_file: bool

@dataclass(frozen=True)
class ExtractionFailure:
    # Represents a failure to process a single file
    file_info: FileInfo
    reason: str

@dataclass(frozen=True)
class ExtractionResult:
    # The result of a metadata extraction operation, including successes and failures
    succeeded: list[FileMetadata]
    failed: list[ExtractionFailure]

@dataclass(frozen=True)
class ScanSummary:
    # A summary of a completed scan operation
    scanned_files: int = 0
    processed_files: int = 0
    notes: list[str] = field(default_factory=list)

# --- Enums ---

class ConsentResult(Enum):
    # Represents the possible outcomes of a consent request
    GRANTED = auto()
    DENIED = auto()
    CANCELLED = auto()

# --- Service Protocols ---

class ConsentGateway(Protocol):
    def get_user_consent(self) -> ConsentResult: ...

class FileScanner(Protocol):
    def get_input_file_path(self) -> list[FileInfo] | None: ...

class MetadataExtractor(Protocol):
    def base_extraction(self, file_list: list[FileInfo]) -> ExtractionResult: ...

# A generic TypeVar to represent the result of an analysis.
# This is safer than using 'Any'. This will be changed later
AnalysisResult = TypeVar("AnalysisResult")

class Storage(Protocol):
    def save_extracted_data(self, extracted_data: list[FileMetadata]) -> None: ...
    def read_all_data(self) -> list[FileMetadata]: ...

class AnalysisEngine(Protocol):
    def analyze(self, extracted_data: list[FileMetadata]) -> AnalysisResult: ...

class Exporter(Protocol):
    def export(self, analysis_results: AnalysisResult) -> None: ...