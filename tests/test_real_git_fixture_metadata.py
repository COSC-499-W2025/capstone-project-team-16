from pathlib import Path

from services.scan_service import analyze_scan
from file_parser import check_file_validity
from repository_extractor import _run_git


def test_real_git_fixture_emits_repo_and_contributor_metadata():
    fixture = Path("input/test-data/full_project_detail_validation_repo.zip")
    result = check_file_validity(str(fixture))
    assert result is not None
    file_list, _zip_hash = result
    repo_entry = next(item for item in file_list if item["filename"].endswith("/.git/"))
    repo_root = Path(repo_entry["filename"]).parent
    direct = _run_git(
        str(repo_root),
        "log",
        "--all",
        "--date-order",
        "--pretty=format:__COMMIT__%n%H%x09%ae%x09%ct",
        "--numstat",
        "--no-renames",
    )
    assert direct.returncode == 0

    output = analyze_scan(file_list, "advanced", {})
    assert output is not None

    project = next(
        p for p in output["project_summaries"] if p.get("project") == "full_project_detail_validation_repo"
    )

    assert project["branch_count"] >= 2
    assert project["has_merges"] == "Yes"
    assert project["commit_frequency"] != "Unknown"
    assert project["project_type"] == "collaborative"
    assert project["per_contributor_pct"]
    assert project["per_contributor_scores"]
    assert project["per_contributor_skills"]
