import pytest
import sys
import os
from io import StringIO
from unittest.mock import patch, Mock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import main
from contracts import ConsentResult, FileScannerError, FileInfo, ExtractionResult


class TestMainEntryPoint:
    """Contains tests for the main application entry point."""

    @pytest.fixture
    def mock_dependencies(self, monkeypatch, tmp_path):
        """Creates a dictionary of mock components to be injected into main."""
        mock_permission = Mock()
        mock_permission.get_user_consent.return_value = ConsentResult.GRANTED

        mock_scanner = Mock()
        mock_scanner.get_input_file_path.return_value = [FileInfo("test.py", 100, None, True)]
        mock_scanner.cleanup = Mock()

        mock_extractor = Mock()
        mock_extractor.base_extraction.return_value = ExtractionResult(succeeded=[], failed=[])

        mock_storage = Mock()
        mock_storage.initialize_database = Mock()
        mock_storage.save_extracted_data = Mock()

        return {
            'permission': mock_permission,
            'scanner': mock_scanner,
            'extractor': mock_extractor,
            'storage': mock_storage
        }

    def test_main_successful_workflow(self, mock_dependencies, capsys):
        """Tests that the main function completes a successful workflow."""
        main(
            permission_manager=mock_dependencies['permission'],
            file_scanner=mock_dependencies['scanner'],
            metadata_extractor=mock_dependencies['extractor'],
            storage=mock_dependencies['storage']
        )
        
        # Verify that all primary components were called as expected.
        mock_dependencies['permission'].get_user_consent.assert_called_once()
        mock_dependencies['storage'].initialize_database.assert_called_once()
        mock_dependencies['scanner'].get_input_file_path.assert_called_once()
        mock_dependencies['extractor'].base_extraction.assert_called_once()
        mock_dependencies['storage'].save_extracted_data.assert_called_once()
        mock_dependencies['scanner'].cleanup.assert_called_once()

    def test_main_exits_on_consent_denied(self, mock_dependencies, capsys):
        """Tests that the main function exits when user consent is denied."""
        mock_dependencies['permission'].get_user_consent.return_value = ConsentResult.DENIED
        
        with patch('main.Orchestrator') as mock_orchestrator_class:
            main(permission_manager=mock_dependencies['permission'])
            mock_orchestrator_class.assert_not_called()
        
        captured = capsys.readouterr()
        assert "Consent denied. Exiting." in captured.out

    def test_main_handles_no_files_found(self, mock_dependencies, capsys):
        """Tests that the main function handles an empty file list gracefully."""
        mock_dependencies['scanner'].get_input_file_path.return_value = None
        
        main(
            permission_manager=mock_dependencies['permission'],
            file_scanner=mock_dependencies['scanner'],
            storage=mock_dependencies['storage']
        )
        
        captured = capsys.readouterr()
        assert "No files found" in captured.out

    def test_main_dev_mode_initialization(self, monkeypatch, tmp_path, capsys):
        """Tests that the main function runs in DEV mode and loads mocks."""
        monkeypatch.setenv("SKILLSCOPE_MODE", "DEV")
        
        # Calling main without arguments should trigger DEV mode initialization.
        main()
        
        captured = capsys.readouterr()
        assert "Running in DEV mode" in captured.out

    def test_main_handles_keyboard_interrupt(self, monkeypatch, capsys):
        """Test main handles user cancellation gracefully."""
        monkeypatch.setenv("SKILLSCOPE_MODE", "DEV")
        
        def mock_main_logic():
            raise KeyboardInterrupt()
        
        # Simulate a KeyboardInterrupt by patching a lower-level call within the
        # main try-except block.
        with patch('main.Orchestrator', side_effect=KeyboardInterrupt):
            main()
            
            captured = capsys.readouterr()
            assert "Operation cancelled by user" in captured.out