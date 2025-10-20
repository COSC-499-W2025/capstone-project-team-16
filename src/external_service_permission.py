# external_service_permission.py

def ask_user_permission():
    
    # This is to ask user for permission before using an external service.
    # Will returns True if user gives permission, False otherwise.
   
    print("This action requires using an external service.")
    print("Some data may be sent outside your local machine.")
    choice = input("Do you consent to using the external service? (y/n): ").strip().lower()
    return choice == 'y'

def run_external_service():
    
    # placeholder for now. need to add external service call

    print("External service is running")

def run_local_fallback():
    
    # if user doesn't give permission, run this. like a local analysis method like scanning files without sending anything outside.
    # for now just a placeholder
  
    print("External service denied. Running local analysis instead...")

def main():

    # main part
  
    user_permission = ask_user_permission()

    if user_permission:
        run_external_service()
    else:
        run_local_fallback()

