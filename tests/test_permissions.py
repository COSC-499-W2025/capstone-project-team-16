import pytest
from components.permissions import ConsolePermissionManager
from contracts import ConsentResult
import sys
from io import StringIO


class TestConsolePermissionManager:
    """Contains tests for the ConsolePermissionManager's consent handling."""

    def test_get_user_consent_granted(self, monkeypatch):
        """Tests that a 'Y' input returns a GRANTED result."""
        manager = ConsolePermissionManager()
        monkeypatch.setattr('builtins.input', lambda _: "Y")
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.GRANTED

    def test_get_user_consent_denied(self, monkeypatch):
        """Tests that an 'N' input returns a DENIED result."""
        manager = ConsolePermissionManager()
        monkeypatch.setattr('builtins.input', lambda _: "N")
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.DENIED

    def test_get_user_consent_retry_on_invalid_input(self, monkeypatch, capsys):
        """Tests that invalid input prompts the user to retry until a valid input is given."""
        manager = ConsolePermissionManager()
        inputs = iter(["invalid", "maybe", "Y"])
        
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.GRANTED
        captured = capsys.readouterr()
        assert "Invalid input. Please enter 'Y' or 'N'." in captured.out
        # Verify the error is shown twice for the two invalid inputs.
        assert captured.out.count("Invalid input") == 2

    def test_get_user_consent_handles_keyboard_interrupt(self, monkeypatch, capsys):
        """Tests that a KeyboardInterrupt returns a CANCELLED result."""
        manager = ConsolePermissionManager()
        
        def mock_input(_):
            raise KeyboardInterrupt()
        
        monkeypatch.setattr('builtins.input', mock_input)
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.CANCELLED
        captured = capsys.readouterr()
        assert "Input cancelled" in captured.out

    def test_get_user_consent_handles_eof_error(self, monkeypatch, capsys):
        """Tests that an EOFError returns a CANCELLED result."""
        manager = ConsolePermissionManager()
        
        def mock_input(_):
            raise EOFError()
        
        monkeypatch.setattr('builtins.input', mock_input)
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.CANCELLED
        captured = capsys.readouterr()
        assert "Input cancelled" in captured.out

    def test_get_user_consent_case_insensitive(self, monkeypatch):
        """Tests that user input is handled in a case-insensitive manner."""
        manager = ConsolePermissionManager()
        
        for input_val in ["y", "Y", "n", "N"]:
            monkeypatch.setattr('builtins.input', lambda _: input_val)
            result = manager.get_user_consent()
            
            if input_val.lower() == "y":
                assert result == ConsentResult.GRANTED
            else:
                assert result == ConsentResult.DENIED

    def test_get_user_consent_strips_whitespace(self, monkeypatch):
        """Tests that input with leading/trailing whitespace is handled correctly."""
        manager = ConsolePermissionManager()
        monkeypatch.setattr('builtins.input', lambda _: "  Y  \n")
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.GRANTED

    def test_get_user_consent_empty_string_retries(self, monkeypatch, capsys):
        """Tests that an empty input string is treated as invalid and retried."""
        manager = ConsolePermissionManager()
        inputs = iter(["", "Y"])
        
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        result = manager.get_user_consent()
        
        assert result == ConsentResult.GRANTED
        captured = capsys.readouterr()
        assert "Invalid input" in captured.out  # Verify an error was shown