import os
import zipfile


# Checks user input and passes it to a validity check. This will loop if not input is entered
def get_input_file_path():

    while True:
        print("Please provide the path to your zipped project folder: ")
        print("Example: C:/Users/YourName/Documents/project.zip")
        zip_path = input("File path: ")

        if not zip_path:
            print("No path was entered.")
        elif zip_path:
            # Validate path and folder before moving on
            if (file_tree := check_file_validity(zip_path)):
                print("Valid zip file detected.")
                for f in file_tree:
                    print(f["filename"], f["size"])
                return zip_path
            else: print("Invalid zip file detected. Please enter a valid zip file.")


#TODO: add errors to log file 
"""
Validates the following in order:

1. Path exists
2. File exists
3. Ends in .zip
4. Corrupted file / ZIP64 / Other Errors
5. Empty zip file

For every file checked in the zip, a list of dictionary entries is made, summarizing the contents. 

"""
def check_file_validity(zip_path):

    if os.path.exists(zip_path):
        if os.path.isfile(zip_path):
            if zip_path.lower().endswith(".zip"):
                
                try:
                  with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                      bad = zip_ref.testzip()
                      if bad:
                          print("Corrupted archive: bad entry at: ", bad)
                          return None
                      else:
                        file_tree = [
                            {
                                # May need to add more information for extraction
                                "filename": info.filename,
                                "size": info.file_size,
                                "last_modified": info.date_time
                            }
                            for info in zip_ref.infolist()
                        ]
                        if not file_tree:
                            print("Zip file is valid, but empty.")
                            return None


                        return file_tree



                except zipfile.BadZipFile:
                    print("Not a zip file or corrupted at central directory.")
                    return None
                except zipfile.LargeZipFile:
                    print("File uses ZIP64. Too large cannot handle.")
                    return None
                except Exception as e:
                    print("Error: ", e)
                    return None
            else:
                print("The requested file is not a zip file")
                return None

        else:
            print("File does not exist.")
            return None
                    
    else:
        print("Path does not exist")
        return None

