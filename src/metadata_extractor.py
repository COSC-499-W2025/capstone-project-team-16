import zipfile
import os

def extract_zip(zip_path: str, extract_to: str) -> None:
    """Extract the zip file to a temporary directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def get_file_metadata(file_path: Path, root_dir: Path) -> dict:
    """Collect general file metadata."""
    stat = file_path.stat()
    return {
        "file_name": file_path.name,
        "relative_path": str(file_path.relative_to(root_dir)),
        "extension": file_path.suffix.lower(),
        "size_bytes": stat.st_size,
        "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }

def detect_project_metadata_files(file_path: Path) -> dict:
    """Identify and read repository metadata files (README, LICENSE, etc.)."""
    filename = file_path.name.lower()
    content = None

    # Only attempt to read small text-based files
    if file_path.suffix.lower() in [".md", ".txt", ".json", ".toml", ".cfg", ".yml", ".yaml", ".xml", ""]:
        try:
            content = file_path.read_text(errors="ignore")[:2000]   # only read first 2KB
        except Exception:
            pass

    # Return a dictionary marking which metadata files are found
    return {
        "is_git_folder": ".git" in file_path.parts,
        "gitignore": content if filename == ".gitignore" else None,
        "readme": content if filename in ["readme", "readme.md"] else None,
        "license": content if filename in ["license", "license.txt"] else None,
        "requirements": content if filename == "requirements.txt" else None,
        "package_json": content if filename == "package.json" else None,
        "setup_py": content if filename in ["setup.py", "setup.cfg"] else None,
    }

def detect_source_code_data(file_path: Path, content: str) -> dict:
    """Analyze source code data: language, lines, and structure."""
    ext = file_path.suffix.lower()
    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".java": "Java", ".cpp": "C++",
        ".c": "C", ".rs": "Rust", ".html": "HTML", ".css": "CSS", ".go": "Go",
    }

    language = lang_map.get(ext)
    loc = content.count("\n") if content else 0
    has_main = "main(" in content or "if __name__" in content

    return {
        "language": language,
        "lines_of_code": loc,
        "has_main_entry": has_main,
    }

def categorize_file(file_path: Path) -> str:
    """Roughly categorize files by type."""
    ext = file_path.suffix.lower()
    path_str = str(file_path).lower()

    if "test" in path_str or "/tests/" in path_str:
        return "test_file"
    if "docs" in path_str or ext in [".md", ".rst", ".txt"]:
        return "documentation"
    if ext == ".ipynb":
        return "notebook"
    if ext in [".png", ".jpg", ".jpeg", ".svg", ".gif"]:
        return "image"
    if ext in [".mp4", ".mov"]:
        return "video"
    if ext in [".mp3", ".wav"]:
        return "audio"
    if ext in [".csv", ".json", ".xlsx", ".xml", ".parquet"]:
        return "dataset"
    if ext in [".pkl", ".h5", ".pt", ".onnx"]:
        return "model"
    return "other"

def extract_project_metadata(zip_path: str) -> dict:
    """Extract and analyze metadata from the given project zip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        extract_zip(zip_path, tmpdir)
        root_dir = Path(tmpdir)

        all_files_metadata = []

        # Walk through every file recursively in the extracted project
        for file_path in root_dir.rglob("*"):
            if file_path.is_file():
                # Basic file-level info
                file_info = get_file_metadata(file_path, root_dir)
                category = categorize_file(file_path)
                # Only read text files if small (< 2 MB)
                content = ""
                # Only read text files if small (< 2 MB)
                if file_info["size_bytes"] < 2_000_000:
                    try:
                        content = file_path.read_text(errors="ignore")
                    except Exception:
                        pass

                # Gather repo metadata and code structure info
                project_meta = detect_project_metadata_files(file_path)
                code_meta = detect_source_code_data(file_path, content)

                # Merge all metadata for this file
                file_info.update({
                    "category": category,
                    "project_metadata": project_meta,
                    "code_metadata": code_meta,
                })

                all_files_metadata.append(file_info)

        # Return summary containing all files' metadata
        return {"file_count": len(all_files_metadata), "files": all_files_metadata}