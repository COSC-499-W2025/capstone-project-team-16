import json
import os
import logging
from contracts import (
    MetadataExtractor,
    FileInfo,
    FileMetadata,
    ExtractionResult,
    ExtractionFailure,
)

logger = logging.getLogger(__name__)


class MetadataExtractorImpl(MetadataExtractor):
    """
    An implementation of the MetadataExtractor protocol.

    This class loads filters from a JSON file to categorize files and identify
    their programming language based on file extensions and names.
    """

    def __init__(self, filters_path: str):
        """
        Initializes the MetadataExtractorImpl.

        Args:
            filters_path (str): The path to the JSON file containing filter definitions.
        """
        if not filters_path:
            raise ValueError("filters_path must be provided")
        self.filters_path = filters_path
        self.ext_to_category, self.ext_to_language = self._load_filters()

    def _load_filters(self) -> tuple[dict, dict]:
        """
        Loads and processes categorization filters from the JSON file.

        Raises:
            FileNotFoundError: If the filters file doesn't exist.
            ValueError: If the JSON is malformed or has an invalid structure.
            RuntimeError: For other unexpected errors during loading.
        """
        try:
            with open(self.filters_path, "r") as f:
                data = json.load(f)

            # --- Filter Validation ---
            if "categories" not in data:
                raise ValueError("Missing required 'categories' key in filters file.")
            if "languages" not in data:
                logger.warning("Missing 'languages' key in filters file. Language detection will be disabled.")

            ext_to_category = {}
            for category, items in data.get("categories", {}).items():
                if not isinstance(items, list):
                    raise ValueError(f"Category '{category}' must be a list, but found {type(items).__name__}.")
                for item in items:
                    if not isinstance(item, str):
                        raise ValueError(f"Filter items in category '{category}' must be strings, but found {type(item).__name__}.")
                    ext_to_category[item.lower()] = category

            lang_to_exts = data.get("languages", {})
            ext_to_language = {}
            for lang, exts in lang_to_exts.items():
                if not isinstance(exts, list):
                    raise ValueError(f"Language '{lang}' extensions must be a list, but found {type(exts).__name__}.")
                for ext in exts:
                    if not isinstance(ext, str):
                        raise ValueError(f"Extension for language '{lang}' must be a string, but found {type(ext).__name__}.")
                    ext_to_language[ext.lower()] = lang

            logger.info(f"Successfully loaded {len(ext_to_category)} category filters and {len(ext_to_language)} language filters.")
            return ext_to_category, ext_to_language

        except FileNotFoundError as e:
            logger.error(f"Filter file not found at path: {self.filters_path}")
            raise FileNotFoundError(f"Cannot find required filter file: {self.filters_path}.") from e
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON detected in {self.filters_path}: {e}")
            raise ValueError(
                f"Filter file {self.filters_path} contains invalid JSON. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
            ) from e
        
        except ValueError as e:
            # Log the validation error and re-raise it to fail fast.
            logger.error(f"Invalid filter file structure in {self.filters_path}: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error loading filters: {e}")
            raise RuntimeError(
                f"An unexpected error occurred while loading filters from {self.filters_path}."
            ) from e

    def base_extraction(self, file_list: list[FileInfo]) -> ExtractionResult:
        """
        Performs metadata extraction on a list of file information objects.

        Args:
            file_list (list[FileInfo]): A list of unprocessed file records.

        Returns:
            ExtractionResult: An object containing lists of succeeded and failed extractions.
        """
        succeeded = []
        failed = []

        for f in file_list:
            try:
                # Strip trailing slash before getting basename to handle directory paths from zips (e.g., ".git/").
                file_path_cleaned = f.file_path.rstrip('/')  # Handles directory entries
                filename = os.path.basename(file_path_cleaned)
                search_name = filename.lower()
                _, ext = os.path.splitext(filename)
                search_ext = ext.lower()

                # Determine category based on extension first, then the full filename.
                category = "uncategorized"
                if search_ext and search_ext in self.ext_to_category:
                    # Match by extension (e.g., ".py", ".json")
                    category = self.ext_to_category[search_ext]
                elif search_name in self.ext_to_category:
                    # Match by exact filename/dirname (e.g., "Dockerfile", ".git")
                    category = self.ext_to_category[search_name]
                
                # Detect language only for files categorized as code.
                language = "undefined"
                if f.is_file and category in ["source_code", "web_code"]:
                    language = self.ext_to_language.get(search_ext, "undefined")

                succeeded.append(
                    FileMetadata(
                        file_path=f.file_path,
                        size=f.size,
                        last_modified=f.last_modified,
                        extension=search_ext,
                        category=category,
                        is_file=f.is_file,
                        language=language,
                    )
                )
            except Exception as e:
                # Safely get file_path to prevent this handler from crashing if 'f' is malformed.
                file_path = getattr(f, 'file_path', 'unknown')
                logger.error(f"Failed to process file '{file_path}': {e}")
                failed.append(ExtractionFailure(file_path=file_path, reason=str(e)))

        return ExtractionResult(succeeded=succeeded, failed=failed)