from unittest.mock import MagicMock

import main


def test_orchestrator_basic_mode(monkeypatch):
    """
    SCENARIO: User selects basic analysis mode
    EXPECTED: Advanced options are not requested, analysis runs with empty options
    """
    monkeypatch.setattr(main, "get_analysis_mode", lambda: "basic")
    mock_advanced = MagicMock()
    monkeypatch.setattr(main, "get_advanced_options", mock_advanced)
    monkeypatch.setattr(main, "get_input_file_path", lambda: ["fake/path/project.zip"])

    mock_analyze = MagicMock(return_value={"project_summaries": []})
    mock_save = MagicMock()
    monkeypatch.setattr(main, "analyze_scan", mock_analyze)
    monkeypatch.setattr(main, "save_scan", mock_save)

    main.orchestrator(main.UserConfig(consent=True))

    assert not mock_advanced.called
    mock_analyze.assert_called_once_with(
        ["fake/path/project.zip"], "basic", {}
    )
    mock_save.assert_called_once()


def test_orchestrator_advanced_mode(monkeypatch):
    """
    SCENARIO: User selects advanced analysis mode
    EXPECTED: Advanced options are requested and passed to analysis
    """
    monkeypatch.setattr(main, "get_analysis_mode", lambda: "advanced")
    mock_advanced = MagicMock(return_value={"programming_scan": True})
    monkeypatch.setattr(main, "get_advanced_options", mock_advanced)
    monkeypatch.setattr(main, "get_input_file_path", lambda: ["fake/path/project.zip"])

    mock_analyze = MagicMock(return_value={"project_summaries": []})
    mock_save = MagicMock()
    monkeypatch.setattr(main, "analyze_scan", mock_analyze)
    monkeypatch.setattr(main, "save_scan", mock_save)

    main.orchestrator(main.UserConfig(consent=True))

    mock_analyze.assert_called_once_with(
        ["fake/path/project.zip"], "advanced", {"programming_scan": True}
    )
    mock_save.assert_called_once()
