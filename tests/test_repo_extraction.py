import pytest
from unittest.mock import MagicMock, patch
from repository_extractor import analyze_repo_type

def test_valid_git_repo_single_author_single_branch(monkeypatch):
    """
    SCENARIO: Valid .git folder with a single author, single branch, no merges
    EXPECTED: Returns valid repo info with project_type = "individual"
    """
    repo_path = {
        "filename": "/path/to/repo/.git/",
        "extension": ".git",
        "isFile": False
    }

    mock_repo = MagicMock()
    mock_commit = MagicMock()
    mock_commit.author.email = "author@example.com"
    mock_commit.parents = []

    # Patch Repo to return the mock
    with patch("repository_extractor.Repo", return_value=mock_repo):
        mock_repo.iter_commits.return_value = [mock_commit]
        mock_repo.branches = [MagicMock(name="main")]

        result = analyze_repo_type(repo_path)

        assert result is not None
        assert result["is_valid"] is True
        assert result["repo_name"] == "repo"
        assert result["repo_root"] == "/path/to/repo"
        assert result["authors"] == ["author@example.com"]
        assert result["branch_count"] == 1
        assert result["has_merges"] is False
        assert result["project_type"] == "individual"

def test_valid_git_repo_collaborative():
    """
    SCENARIO: Multiple authors, multiple branches, has merges
    EXPECTED: project_type = "collaborative"
    """
    repo_path = {
        "filename": "/path/to/repo/.git/",
        "extension": ".git",
        "isFile": False
    }

    mock_repo = MagicMock()
    mock_commit1 = MagicMock()
    mock_commit1.author.email = "author1@example.com"
    mock_commit1.parents = []

    mock_commit2 = MagicMock()
    mock_commit2.author.email = "author2@example.com"
    mock_commit2.parents = [MagicMock(), MagicMock()]  # two parents → merge commit

    mock_repo.branches = [MagicMock(name="main"), MagicMock(name="dev")]
    mock_repo.iter_commits.side_effect = lambda *args, **kwargs: [mock_commit1, mock_commit2]

    with patch("repository_extractor.Repo", return_value=mock_repo):
        result = analyze_repo_type(repo_path)

        assert result is not None
        assert result["is_valid"] is True
        assert result["project_type"] == "collaborative"
        assert len(result["authors"]) == 2
        assert result["branch_count"] == 2
        assert result["has_merges"] is True


def test_non_git_folder_returns_none():
    """
    SCENARIO: Folder is not a .git directory
    EXPECTED: Function returns None
    """
    repo_path = {
        "filename": "/path/to/repo/some_folder/",
        "extension": ".txt",
        "isFile": False
    }

    result = analyze_repo_type(repo_path)
    assert result is None

def test_git_repo_raises_exception(monkeypatch):
    """
    SCENARIO: Repo raises an exception when opened
    EXPECTED: Function returns None
    """
    repo_path = {
        "filename": "/path/to/repo/.git/",
        "extension": ".git",
        "isFile": False
    }

    with patch("repository_extractor.Repo", side_effect=Exception("Failed to open")):
        result = analyze_repo_type(repo_path)
        assert result is None
