import sys
from contracts import ConsentGateway, ConsentResult


class ConsolePermissionManager(ConsentGateway):
    """
    An implementation of ConsentGateway that prompts the user via the CLI.
    """
    def get_user_consent(self) -> ConsentResult:
        """
        Prompts the user for consent and returns the corresponding result.

        This method will loop indefinitely until the user provides a valid
        response ('Y' or 'N') or cancels the operation (e.g., via Ctrl+C).

        Returns:
            ConsentResult: The outcome of the consent request.
        """
        while True:
            try:                
                response = input("Before proceeding, do you give consent to Skill Scope to access and view your personal data? (Y/N): ").strip().upper()
                
                if response == "Y":
                    print("Consent granted.")
                    return ConsentResult.GRANTED
                elif response == "N":
                    print("Consent denied.")
                    return ConsentResult.DENIED
                else:
                    print("Invalid input. Please enter 'Y' or 'N'.")
            except (KeyboardInterrupt, EOFError):
                # Handle cases where the user cancels the input prompt.
                print("\nInput cancelled.")
                return ConsentResult.CANCELLED