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

def test_merge_scans_logic():
    """
    SCENARIO: Merging an existing scan with a new scan.
    EXPECTED: Lists are appended, contributor skills are unioned, new contributors are added.
    """
    # Existing data
    existing = {
        "project_summaries": [{"project": "A"}],
        "resume_summaries": ["Worked on A"],
        "skills_chronological": [{"skill": "Python"}],
        "projects_chronological": [{"name": "A"}],
        "contributor_profiles": {
            "Alice": {"skills": ["Python"], "projects": [{"name": "A"}]}
        },
        "source_hashes": ["hashA"]
    }

    # New data
    new_data = {
        "project_summaries": [{"project": "B"}],
        "resume_summaries": ["Worked on B"],
        "skills_chronological": [{"skill": "Go"}],
        "projects_chronological": [{"name": "B"}],
        "contributor_profiles": {
            "Alice": {"skills": ["Go"], "projects": [{"name": "B"}]},
            "Bob": {"skills": ["Java"], "projects": [{"name": "B"}]}
        },
        "source_hashes": ["hashB"]
    }

    # Merge
    merged = scan_service.merge_scans(existing, new_data)

    # Assertions
    assert len(merged["project_summaries"]) == 2
    assert merged["project_summaries"][1]["project"] == "B"
    assert len(merged["resume_summaries"]) == 2
    assert len(merged["skills_chronological"]) == 2

    # Alice should have Python AND Go (union of skills)
    alice_skills = merged["contributor_profiles"]["Alice"]["skills"]
    assert set(alice_skills) == {"Python", "Go"}
    
    # Bob should be added
    assert "Bob" in merged["contributor_profiles"]
    assert merged["contributor_profiles"]["Bob"]["skills"] == ["Java"]
    
    # Hashes
    assert set(merged["source_hashes"]) == {"hashA", "hashB"}

def test_merge_scans_empty_inputs():
    """
    SCENARIO: Both existing and new data are empty dictionaries.
    EXPECTED: Returns a dictionary with initialized empty lists/dicts for standard keys.
    """
    existing = {}
    new_data = {}
    
    merged = scan_service.merge_scans(existing, new_data)
    
    assert merged["project_summaries"] == []
    assert merged["resume_summaries"] == []
    assert merged["skills_chronological"] == []
    assert merged["projects_chronological"] == []
    assert merged["contributor_profiles"] == {}
    assert merged["source_hashes"] == []

def test_merge_scans_one_sided_new():
    """
    SCENARIO: Existing data is populated, new data is empty.
    EXPECTED: Returns data identical to existing (plus initialized keys if missing).
    """
    existing = {
        "project_summaries": [{"project": "A"}],
        "contributor_profiles": {"Alice": {"skills": ["Python"]}}
    }
    new_data = {}
    
    merged = scan_service.merge_scans(existing, new_data)
    
    assert len(merged["project_summaries"]) == 1
    assert merged["project_summaries"][0]["project"] == "A"
    assert merged["contributor_profiles"]["Alice"]["skills"] == ["Python"]

def test_merge_scans_one_sided_existing():
    """
    SCENARIO: Existing data is empty, new data is populated.
    EXPECTED: Returns data identical to new data.
    """
    existing = {}
    new_data = {
        "project_summaries": [{"project": "B"}],
        "contributor_profiles": {"Bob": {"skills": ["Java"]}}
    }
    
    merged = scan_service.merge_scans(existing, new_data)
    
    assert len(merged["project_summaries"]) == 1
    assert merged["project_summaries"][0]["project"] == "B"
    assert merged["contributor_profiles"]["Bob"]["skills"] == ["Java"]

def test_merge_scans_contributor_projects_concatenation():
    """
    SCENARIO: Merging contributor profiles where both have project lists.
    EXPECTED: Project lists are concatenated for the same user.
    """
    existing = {"contributor_profiles": {"Alice": {"projects": [{"name": "A"}]}}}
    new_data = {"contributor_profiles": {"Alice": {"projects": [{"name": "B"}]}}}
    
    merged = scan_service.merge_scans(existing, new_data)
    
    alice_projects = merged["contributor_profiles"]["Alice"]["projects"]
    assert len(alice_projects) == 2
    assert {p["name"] for p in alice_projects} == {"A", "B"}

def test_merge_scans_duplicate_skills():
    """
    SCENARIO: Merging skills for a contributor where duplicates exist.
    EXPECTED: Skills are unioned (no duplicates).
    """
    existing = {"contributor_profiles": {"Alice": {"skills": ["Python", "Java"]}}}
    new_data = {"contributor_profiles": {"Alice": {"skills": ["Java", "C++"]}}}
    
    merged = scan_service.merge_scans(existing, new_data)
    
    skills = merged["contributor_profiles"]["Alice"]["skills"]
    assert sorted(skills) == ["C++", "Java", "Python"]
