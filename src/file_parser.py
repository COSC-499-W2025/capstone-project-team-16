import os
import zipfile

def get_input_file_path():

    while True:
        print("Please provide the path to your zipped project folder: ")
        print("Example: C:/Users/YourName/Documents/project.zip")
        zip_path = input("File path: ")

        if not zip_path:
            print("No path was entered.")
        elif zip_path:
            # Validate path and folder before moving on
            if check_file_validity(zip_path):
                print("Valid zip file detected.")
                return True


#TODO: add errors to log file 
def check_file_validity(zip_path):

    if os.path.exists(zip_path):
        if os.path.isfile(zip_path):
            if zip_path.lower().endswith(".zip"):
                
                try:
                  with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                      bad = zip_ref.testzip()
                      if bad is None:
                          return True
                      else:
                          print("Corrupted archive: bad entry at: ", bad)
                          return False
                except zipfile.BadZipFile:
                    print("Not a zip file or corrupted at central directory.")
                    return False
                except zipfile.LargeZipFile:
                    print("File uses ZIP64. Cannot handle.")
                    return False
                except Exception as e:
                    print("Error: ", e)
                    return False
            else:
                print("The requested file is not a zip file")
                return False

        else:
            print("File does not exist.")
            return False
                    
    else:
        print("Path does not exist")
        return False
