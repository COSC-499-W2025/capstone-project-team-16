import os
import zipfile
import tempfile


def get_input_file_path():
    """
    Prompts the user for a zip file path and returns the extracted file tree.
    """
    while True:
        print("Please provide the path to your zipped project folder: ")
        print("Example: C:/Users/YourName/Documents/project.zip")
        zip_path = input("File path: ")

        if not zip_path:
            print("No path was entered.")
            continue

        file_tree = check_file_validity(zip_path)
        if file_tree:
            print("Valid zip file detected.")
            return file_tree
        else:
            print("Invalid zip file detected. Please enter a valid zip file.")


def check_file_validity(zip_path):
    """
    Validates the given zip file and extracts it to a temporary directory if valid.

    Returns:
        list: file_tree (list of dicts) if valid, else None
    """
    # Fast path checks before doing any I/O-heavy work
    if not os.path.exists(zip_path):
        print("Path does not exist.")
        return None

    if not os.path.isfile(zip_path):
        print("File does not exist.")
        return None

    if not zip_path.lower().endswith(".zip"):
        print("The requested file is not a zip file.")
        return None

    try:
        # Open once and reuse for validation + file_tree
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # NOTE: testzip() is expensive for large archives because it
            # fully reads and decompresses each file. For performance,
            # we rely on extract failing if the archive is corrupted.
            # If you still want an explicit test, uncomment:
            #
            # bad = zip_ref.testzip()
            # if bad:
            #     print("Corrupted archive: bad entry at:", bad)
            #     return None

            infos = zip_ref.infolist()
            if not infos:
                print("Zip file is valid, but empty.")
                return None

            # Extract once, using the already-open zip_ref
            temp_dir = extract_zip_to_temp(zip_path, zip_ref=zip_ref)

            # Build file tree using the already-fetched infos
            file_tree = [
                {
                    "filename": os.path.join(temp_dir, info.filename),
                    "size": info.file_size,
                    "last_modified": info.date_time,
                }
                for info in infos
                # Skip directory entries to avoid useless records
                if not info.is_dir()
            ]

        return file_tree

    except zipfile.BadZipFile:
        print("Not a zip file or corrupted at central directory.")
        return None
    except zipfile.LargeZipFile:
        print("File uses ZIP64. Too large cannot handle.")
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
