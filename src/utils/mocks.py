"""
Provides mock implementations of the application's service protocols.

These mocks are used for development and testing purposes to isolate components
and provide predictable behavior without relying on external systems like the
filesystem or a real user interface.
"""
from typing import Iterator
from datetime import datetime, timezone
from contracts import (
    Storage,
    ConsentGateway,
    ConsentResult,
    FileScanner,
    FileInfo,
    MetadataExtractor,
    FileMetadata,
    ExtractionResult,
    ExtractionFailure,
)


class MockPermissionManager(ConsentGateway):
    """A mock consent gateway that always grants permission automatically."""
    def get_user_consent(self) -> ConsentResult:
        return ConsentResult.GRANTED

class MockFileScanner(FileScanner):
    """A mock file scanner that returns a fixed list of dummy file objects."""
    def get_input_file_path(self) -> list[FileInfo] | None:
        return [
            FileInfo("test/main.py", 1024, datetime.now(timezone.utc), True),
            FileInfo("test/data.json", 500, datetime.now(timezone.utc), True),
            FileInfo("test/badfile.dll", 999, None, True), # Simulate a file that might fail processing
        ]

    def cleanup(self) -> None:
        """A mock cleanup method to satisfy the FileScanner protocol."""
        pass

class MockMetadataExtractor(MetadataExtractor):
    """A mock metadata extractor that provides canned extraction results."""
    def base_extraction(self, file_list: list[FileInfo]) -> ExtractionResult:
        succeeded = []
        for f in file_list:
            if f.file_path.endswith(".py"):
                succeeded.append(FileMetadata(
                    file_path=f.file_path,
                    size=f.size,
                    last_modified=f.last_modified,
                    extension=".py",
                    category="source_code",
                    is_file=f.is_file,
                    language="python"
                ))
            elif f.file_path.endswith(".json"):
                # Emulate real behavior: configuration files have 'undefined' language.
                succeeded.append(FileMetadata(
                    file_path=f.file_path,
                    size=f.size,
                    last_modified=f.last_modified,
                    extension=".json",
                    category="configuration",
                    is_file=f.is_file,
                    language="undefined"
                ))

        failed = [
            ExtractionFailure(file_path=f.file_path, reason="Unsupported file type")
            for f in file_list if not (f.file_path.endswith(".py") or f.file_path.endswith(".json"))
        ]
        return ExtractionResult(succeeded=succeeded, failed=failed)

class MockStorage(Storage):
    """
    A volatile, in-memory storage mock.

    This class simulates database operations but does not persist any data to disk,
    storing records in a simple list instead.
    """
    def __init__(self):
        self.store: list[FileMetadata] = []

    def initialize_database(self) -> None:
        print("[MockStorage] Database initialized (in-memory).")

    def save_extracted_data(self, extracted_data: list[FileMetadata]) -> None:
        self.store.extend(extracted_data)
        print(f"[MockStorage] Simulating save of {len(extracted_data)} records.")
        for record in extracted_data:
            print(f"  -> Stored: {record.file_path} ({record.category})")

    def read_all_data(self) -> Iterator[FileMetadata]:
        return iter(self.store)