from resume_generator import build_project_line, _build_personal_project_description


def test_build_project_line_accepts_list_fields():
    project = {
        "project": "Alpha",
        "languages": ["Python", "Markdown"],
        "skills": ["Testing"],
        "frameworks": ["FastAPI"],
        "duration_days": 12,
        "project_type": "collaborative",
    }

    line = build_project_line(project)

    assert "Alpha" in line
    assert "using Python, Markdown" in line
    assert "with frameworks such as FastAPI" in line


def test_personal_project_description_accepts_list_fields():
    project_context = {
        "languages": ["Python", "SQL"],
        "skills": ["Backend Development"],
        "frameworks": ["FastAPI", "SQLite"],
        "duration_days": 30,
    }
    user_stats = {
        "pct": 42.0,
        "files_worked": 4,
        "user_code_files": 3,
        "user_test_files": 1,
        "user_doc_files": 0,
        "user_design_files": 0,
    }

    description = _build_personal_project_description("Alpha", project_context, user_stats)

    assert "using Python, SQL" in description
    assert "utilizing frameworks such as FastAPI, SQLite" in description
