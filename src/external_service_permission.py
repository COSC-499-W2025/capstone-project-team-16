# external_service_permission.py

def ask_user_permission():
    
    # This is to ask user for permission before using an external service.
    # Will returns True if user gives permission, False otherwise.
   
    print("This action requires using an external service.")
    print("Some data may be sent outside your local machine.")

    # keep asking until user enters 'y' or 'n'
    
    while True:
        choice = input("Do you consent to using the external service? (y/n): ").strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
    

def run_external_service():
    
    # placeholder for now. need to add external service call(added but need to check). need to replace with API or LLM call.

    print("External service is running")

    # need to test this vvvv

"""
# Get API key (need to change to our environment)

    api_key = os.getenv("EXTERNAL_API_KEY")
    if not api_key:
        print("No API key found.")
        return

    # URL of the external API
    api_url = "https://api..../..." #need to change address

    # Data we want to send to the API
    payload = {
        "input": "Content to analyze.",
        "options": {
            "task": "skill_extraction",
            "language": "en"
        }
    }

    # Headers for authentication and format
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Send request
    print("Sending data to external service...")
    response = requests.post(api_url, json=payload, headers=headers)

    # Check if it worked
    if response.status_code == 200:  #200 means pass.
        data = response.json()
        print("Got response from external service!")
        print("Analysis Result:", data.get("analysis", "No analysis found"))
    else:
        print(Request failed. Status code: {response.status_code}")


"""

def run_local_fallback():
    
    # if user doesn't give permission, run this. like a local analysis method like scanning files without sending anything outside.
  
  
    print("External service denied. Running local analysis instead...")

    # Pick a folder to analyze (need to change this later)
    
    folder_path = "./test_folder"  # or let user input a path (need to change too)

    # Check if folder exists
    
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' not found.")
        return

    # Count how many files are inside
    
    file_count = 0
    for root, dirs, files in os.walk(folder_path):
        file_count += len(files)

    # Print the simple result
    print(f"Local analysis complete.")
    print(f"Total number of files found: {file_count}")
    

def main():

    # main part
  
    user_permission = ask_user_permission()

    if user_permission:
        run_external_service()
    else:
        run_local_fallback()

