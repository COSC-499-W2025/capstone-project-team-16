"""
Defines the centralized contracts for the application.

This file defines the shared data structures (DTOs), service protocols,
and custom exceptions that form the application's core architectural contracts.
All implementation modules should depend on this file instead of on each
other to maintain a clean, decoupled architecture.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto 
from typing import Protocol, TypeVar, Iterator

# --- Custom Exceptions ---

class FileScannerError(Exception):
    """Represents an error during the file scanning phase."""
    pass

class ExtractionError(Exception):
    """Represents an error during the metadata extraction phase."""
    pass

class StorageError(Exception):
    """Represents an error during a database or storage operation."""
    pass

class AnalysisError(Exception):
    """Represents an error during the data analysis phase."""
    pass

class ExportError(Exception):
    """Represents an error during the data export phase."""
    pass

# --- Data Transfer Objects (DTOs) ---

@dataclass(frozen=True)
class FileInfo:
    """A raw, unprocessed file record produced by the scanner."""
    file_path: str
    size: int
    last_modified: datetime | None
    is_file: bool

@dataclass(frozen=True)
class FileMetadata:
    """A fully processed and categorized file record."""
    file_path: str
    size: int
    last_modified: datetime | None
    extension: str
    category: str
    is_file: bool
    language: str = "undefined"  # The identified programming language, if any.

@dataclass(frozen=True)
class ExtractionFailure:
    """Represents a failure to process a single file during extraction."""
    file_path: str
    reason: str

@dataclass(frozen=True)
class ExtractionResult:
    """The result of a metadata extraction operation."""
    succeeded: list[FileMetadata]
    failed: list[ExtractionFailure]

@dataclass(frozen=True)
class ScanSummary:
    """A summary of a completed scan and extraction operation."""
    scan_id: str
    scanned_files: int = 0
    processed_files: int = 0
    failures: list[ExtractionFailure] = field(default_factory=list)

# --- Enums ---

class ConsentResult(Enum):
    """Represents the possible outcomes of a user consent request."""
    GRANTED = auto()
    DENIED = auto()
    CANCELLED = auto()

# --- Service Protocols ---

class ConsentGateway(Protocol):
    """A protocol for components that handle user consent."""
    def get_user_consent(self) -> ConsentResult: ...

class FileScanner(Protocol):
    """A protocol for components that scan and list project files."""
    def get_input_file_path(self) -> list[FileInfo] | None: ...
    def cleanup(self) -> None: ...

class MetadataExtractor(Protocol):
    """A protocol for components that extract metadata from files."""
    def base_extraction(self, file_list: list[FileInfo]) -> ExtractionResult: ...

# A generic TypeVar to represent the result of an analysis.
# This provides better type safety than using 'Any'.
#TODO: This will be refined in a future implementation.
AnalysisResult = TypeVar("AnalysisResult")

class Storage(Protocol):
    """A protocol for components that handle data persistence."""
    def initialize_database(self) -> None: ...
    def save_extracted_data(self, extracted_data: list[FileMetadata]) -> None: ...
    def read_all_data(self) -> Iterator[FileMetadata]: ...

class AnalysisEngine(Protocol):
    """A protocol for components that analyze extracted metadata."""
    def analyze(self, extracted_data: list[FileMetadata]) -> AnalysisResult: ...

class Exporter(Protocol):
    """A protocol for components that export analysis results."""
    def export(self, analysis_results: AnalysisResult) -> None: ...