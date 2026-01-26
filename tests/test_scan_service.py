from unittest.mock import MagicMock

from services import scan_service


def test_analyze_scan_basic(monkeypatch):
    file_list = ["fake/path/project.zip"]
    monkeypatch.setattr(scan_service, "load_filters", lambda: {"x": 1})
    monkeypatch.setattr(
        scan_service,
        "base_extraction",
        lambda files, filters: [{"filename": "file1.py"}],
    )
    mock_detailed = MagicMock()
    monkeypatch.setattr(scan_service, "detailed_extraction", mock_detailed)

    mock_analyze = MagicMock(return_value={"project_summaries": []})
    monkeypatch.setattr(scan_service, "analyze_projects", mock_analyze)

    result = scan_service.analyze_scan(file_list, "Basic", {})

    assert result == {"project_summaries": []}
    assert not mock_detailed.called
    mock_analyze.assert_called_once()


def test_run_scan_persists(monkeypatch):
    mock_analyze = MagicMock(return_value={"project_summaries": []})
    mock_save = MagicMock()
    monkeypatch.setattr(scan_service, "analyze_scan", mock_analyze)
    monkeypatch.setattr(scan_service, "save_scan", mock_save)

    result = scan_service.run_scan(
        ["fake/path/project.zip"],
        "basic",
        {"programming_scan": True},
        consent=True,
        persist=True,
    )

    assert result == {"project_summaries": []}
    mock_save.assert_called_once_with({"project_summaries": []}, "basic", True)
