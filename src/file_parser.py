import os
import shutil
import tempfile
import zipfile
import hashlib



# --------------------------------------------------------
# Directories (absolute paths for Docker/local consistency)
# --------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_DIR = os.path.join(PROJECT_ROOT, "input")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Ensure folders exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _center_text(text):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def _print_banner(title, line_char="~", min_width=23):
    line_width = max(len(title), min_width)
    line = line_char * line_width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))

def compute_file_hash(filepath):
    """Computes SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def get_input_file_path(input_dir=INPUT_DIR):
    """
    Lists ZIP files in input_dir and lets the user select one.
    Prompts user to add files if none exist.
    Returns extracted file tree or None.
    """
    while True:
        zip_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".zip")]

        if not zip_files:
            print(_center_text(f"No zip files found in '{input_dir}'."))
            print(_center_text("Drop your zipped project(s) in the 'input' folder at the project root and press Enter to continue..."))
            input()
            zip_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".zip")]
            if not zip_files:
                print(_center_text("Still no zip files found. Returning to home."))
                return None
        
        print(_center_text("Checking for duplicates..."))
        # Deduplicate files based on content hash
        unique_zips = []
        seen_hashes = set()
        
        for f in zip_files:
            full_path = os.path.join(input_dir, f)
            f_hash = compute_file_hash(full_path)
            
            if f_hash and f_hash in seen_hashes:
                continue
            if f_hash:
                seen_hashes.add(f_hash)
            unique_zips.append(f)
        zip_files = unique_zips

        _print_banner("Select a zip file")
        for i, f in enumerate(zip_files, start=1):
            print(_center_text(f"{i}. {f}"))

        prompt = f"Choose an option (1-{len(zip_files)} or 0 to cancel): "
        choice = input(_center_text(prompt)).strip()
        if not choice.isdigit():
            print(_center_text("Invalid input. Enter a number."))
            continue

        idx = int(choice)
        if idx == 0:
            return None
        if 1 <= idx <= len(zip_files):
            zip_path = os.path.join(input_dir, zip_files[idx - 1])
            result = check_file_validity(zip_path)
            if result:
                print(_center_text("Valid zip file detected."))
                return result
            else:
                print(_center_text("Invalid zip file. Try again."))
        else:
            print(_center_text("Number out of range."))


def check_file_validity(zip_path):
    """
    Validates the given zip file and extracts it to a temporary directory if valid.

    Returns:
        tuple: (file_tree, zip_hash) if valid, else None
    """
    # Fast path checks before doing any I/O-heavy work
    if not os.path.exists(zip_path):
        print(_center_text("Path does not exist."))
        return None

    if not os.path.isfile(zip_path):
        print(_center_text("File does not exist."))
        return None

    if not zip_path.lower().endswith(".zip"):
        print(_center_text("The requested file is not a zip file."))
        return None

    # Compute hash of the ZIP file itself for deduplication
    zip_hash = compute_file_hash(zip_path)

    try:
        # Open once and reuse for validation + file_tree
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:


            infos = zip_ref.infolist()
            if not infos:
                print(_center_text("Zip file is valid, but empty."))
                return None

            # Extract once, using the already-open zip_ref
            temp_dir = extract_zip_to_temp(zip_path, zip_ref=zip_ref)

            # Build file tree with directories included
            file_tree = []

            for info in infos:
                full_path = os.path.join(temp_dir, info.filename)
                is_file = not info.is_dir()

                file_tree.append({
                    "filename": full_path,
                    "size": info.file_size,
                    "last_modified": info.date_time,
                    "isFile": is_file
                })

        return file_tree, zip_hash

    except zipfile.BadZipFile:
        print(_center_text("Not a zip file or corrupted at central directory."))
        return None
    except zipfile.LargeZipFile:
        print(_center_text("File uses ZIP64. Too large cannot handle."))
        return None
    except Exception as e:
        print("Error:", e)
        return None


def extract_zip_to_temp(zip_path, zip_ref=None):
    """
    Extracts a zip file into a temporary directory and returns the path.

    For performance, if an already-open ZipFile object is provided via
    zip_ref, it will be used instead of reopening the archive.
    """
    temp_dir = tempfile.mkdtemp()

    if zip_ref is not None:
        # Use the existing open handle (no extra open or central directory read)
        zip_ref.extractall(temp_dir)
    else:
        # Backward-compatible usage if called elsewhere with only zip_path
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_dir)

    return temp_dir
