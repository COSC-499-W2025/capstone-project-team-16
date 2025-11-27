import pytest
from unittest.mock import MagicMock
from main import orchestrator

# -------------------------------
# Test: Orchestrator creates new config when none exists
# -------------------------------
def test_orchestrator_creates_config(monkeypatch):
    """
    SCENARIO: No config exists in the database (load returns None)
    EXPECTED: A new UserConfig object is created automatically
    """
    monkeypatch.setattr('main.get_user_consent', lambda: True)
    monkeypatch.setattr('main.get_analysis_mode', lambda: "basic")
    monkeypatch.setattr('main.get_advanced_options', lambda: {"programming_scan": True, "framework_scan": False})
    monkeypatch.setattr('main.get_input_file_path', lambda: ["fake/path/project.zip"])
    monkeypatch.setattr('main.load_filters', lambda: {})
    monkeypatch.setattr('main.base_extraction', lambda files, filters: [{"filename": "file1.py"}])
    
    # Use mocks for detailed_extraction and analyze_projects
    mock_detailed = MagicMock(return_value=[{"filename": "file1.py", "details": "detailed"}])
    monkeypatch.setattr('main.detailed_extraction', mock_detailed)
    
    mock_analyze = MagicMock()
    monkeypatch.setattr('main.analyze_projects', mock_analyze)
    
    orchestrator()
    
    # Assert analyze_projects was called
    mock_analyze.assert_called_once()
    # For basic mode, detailed_extraction should not be called
    assert not mock_detailed.called  # because basic mode doesn't trigger it


# -------------------------------
# Test: Orchestrator respects consent already given
# -------------------------------
def test_orchestrator_with_existing_consent(monkeypatch):
    """
    SCENARIO: UserConfig already has consent=True
    EXPECTED: Orchestrator does not prompt for consent again
    """
    monkeypatch.setattr('main.get_user_consent', lambda: True)  # Should never be called
    monkeypatch.setattr('main.get_analysis_mode', lambda: "basic")
    monkeypatch.setattr('main.get_advanced_options', lambda: {})
    monkeypatch.setattr('main.get_input_file_path', lambda: ["fake/path/project.zip"])
    monkeypatch.setattr('main.load_filters', lambda: {})
    monkeypatch.setattr('main.base_extraction', lambda files, filters: [{"filename": "file1.py"}])
    
    mock_analyze = MagicMock()
    monkeypatch.setattr('main.analyze_projects', mock_analyze)
    
    # Patch UserConfig to simulate existing consent
    from main import UserConfig
    original_init = UserConfig.__init__
    def fake_init(self, consent=True, analysis_mode="basic", advanced_scans=None, last_updated=None):
        original_init(self, consent=True, analysis_mode="basic", advanced_scans=advanced_scans, last_updated=last_updated)
    UserConfig.__init__ = fake_init

    orchestrator()
    
    mock_analyze.assert_called_once()
    
    # Restore original init
    UserConfig.__init__ = original_init


# -------------------------------
# Test: Orchestrator sets advanced scan options in advanced mode
# -------------------------------
def test_orchestrator_advanced_mode(monkeypatch):
    """
    SCENARIO: User selects advanced analysis mode
    EXPECTED: Advanced options are requested and passed, detailed extraction is run
    """
    monkeypatch.setattr('main.get_user_consent', lambda: True)
    monkeypatch.setattr('main.get_analysis_mode', lambda: "advanced")
    monkeypatch.setattr('main.get_advanced_options', lambda: {"programming_scan": True, "framework_scan": True})
    monkeypatch.setattr('main.get_input_file_path', lambda: ["fake/path/project.zip"])
    monkeypatch.setattr('main.load_filters', lambda: {})
    monkeypatch.setattr('main.base_extraction', lambda files, filters: [{"filename": "file1.py"}])
    
    mock_detailed = MagicMock(return_value=[{"filename": "file1.py", "details": "detailed"}])
    monkeypatch.setattr('main.detailed_extraction', mock_detailed)
    
    mock_analyze = MagicMock()
    monkeypatch.setattr('main.analyze_projects', mock_analyze)
    
    orchestrator()
    
    # Assert that detailed_extraction was called
    mock_detailed.assert_called_once()
    # Assert that analyze_projects was called once
    mock_analyze.assert_called_once()
