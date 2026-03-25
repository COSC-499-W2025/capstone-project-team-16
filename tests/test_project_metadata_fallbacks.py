from datetime import datetime

import alternative_analysis as aa


def _filters():
    return {
        "extensions": {
            ".py": "source_code",
            ".js": "web_code",
            ".md": "documentation",
            ".json": "framework",
        },
        "languages": {
            ".py": "Python",
            ".js": "JavaScript",
            ".md": "Markdown",
        },
        "skills": {
            "python": "Python Development",
            "javascript": "JavaScript Development",
            "markdown": "Technical Documentation",
        },
        "frameworks": {
            "package.json": ["Node.js / React"],
        },
    }


def _row(logical_path, extension, category, language="", modified="2024-03-01T10:00:00"):
    return {
        "filename": f"/tmp/extracted/{logical_path}",
        "logical_path": logical_path,
        "size": 120,
        "last_modified": modified,
        "extension": extension,
        "category": category,
        "isFile": True,
        "language": language,
    }


def _silence_output(monkeypatch):
    for name in (
        "print_repo_summary",
        "print_project_rankings",
        "print_chronological_projects",
        "print_skills_timeline",
        "print_resume_summaries",
        "print_contributor_stats",
    ):
        monkeypatch.setattr(aa, name, lambda *args, **kwargs: None)


def test_non_git_project_uses_archive_relative_name_and_root(monkeypatch):
    _silence_output(monkeypatch)
    extracted_data = [
        _row("solo_demo/src/main.py", ".py", "source_code", "Python"),
        _row("solo_demo/README.md", ".md", "documentation", "Markdown", modified="2024-03-03T10:00:00"),
    ]

    result = aa.analyze_projects(
        extracted_data,
        _filters(),
        {"skills_gen": False, "framework_scan": False, "programming_scan": False, "resume_gen": False},
        detailed_data=None,
        write_csv=False,
    )

    project = result["project_summaries"][0]
    assert project["project"] == "solo_demo"
    assert project["repo_name"] == "solo_demo"
    assert project["repo_root"] == "solo_demo"
    assert project["project_type"] == "individual"


def test_team_signal_file_marks_non_git_project_collaborative(monkeypatch):
    _silence_output(monkeypatch)
    extracted_data = [
        _row("team_demo/src/main.py", ".py", "source_code", "Python"),
        _row("team_demo/docs/CONTRIBUTORS.md", ".md", "documentation", "Markdown", modified="2024-03-02T10:00:00"),
    ]

    result = aa.analyze_projects(
        extracted_data,
        _filters(),
        {"skills_gen": False, "framework_scan": False, "programming_scan": False, "resume_gen": False},
        detailed_data=None,
        write_csv=False,
    )

    project = result["project_summaries"][0]
    assert project["project"] == "team_demo"
    assert project["repo_root"] == "team_demo"
    assert project["project_type"] == "collaborative"
