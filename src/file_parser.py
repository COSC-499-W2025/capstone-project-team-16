import os
import zipfile
import tempfile

# Checks user input and passes it to a validity check. This will loop if not input is entered
# Prompts user for input and validates/extracts the zip file
# Checks user input and validates/extracts the zip file
# Returns only the file tree
def get_input_file_path():
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
            # Example: uncomment to inspect files
            # for f in file_tree:
            #     print(f["filename"], f["size"])
            return file_tree
        else:
            print("Invalid zip file detected. Please enter a valid zip file.")


def check_file_validity(zip_path):
    """
    Validates the given zip file and extracts it to a temporary directory if valid.

    Returns:
        list: file_tree (list of dicts) if valid, else None
    """
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
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            bad = zip_ref.testzip()
            if bad:
                print("Corrupted archive: bad entry at:", bad)
                return None

            if not zip_ref.infolist():
                print("Zip file is valid, but empty.")
                return None

        # Extract to a temporary directory
        temp_dir = extract_zip_to_temp(zip_path)

        # Build file tree with absolute paths inside temp directory
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_tree = [
                {
                    "filename": os.path.join(temp_dir, info.filename),
                    "size": info.file_size,
                    "last_modified": info.date_time
                }
                for info in zip_ref.infolist()
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


def extract_zip_to_temp(zip_path):
    """Extracts a zip file into a temporary directory and returns the path."""
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir