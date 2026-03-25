# Module containing methods for repository extraction
# Recieves entry marked as repo. .git file is only dealt with at the moment

from collections import Counter, defaultdict
from datetime import datetime
import os
import shutil
import subprocess


def _run_git(repo_root, *args):
    return subprocess.run(
        ["git", f"--git-dir={os.path.join(repo_root, '.git')}", f"--work-tree={repo_root}", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _center_text(text):
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def _print_banner(title, line_char="~", min_width=23):
    line_width = max(len(title), min_width)
    line = line_char * line_width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))


def analyze_repo_type(repo_path):
    _print_banner("REPO ANALYZING")

    # Only proceed if it is a .git folder indicating .git is likely a legitimate repository directory.
    # Return project dictionary containing all repo-level metadata.
    if repo_path["extension"].endswith(".git") and repo_path["isFile"] == False:

        # Compute repo root path by using parent directory of .git. 
        # This should be the actual project directory name.
        repo_root = os.path.dirname(repo_path["filename"].rstrip("/"))
        repo_name = os.path.basename(repo_root)

        try:
            log_output = _run_git(
                repo_root,
                "log",
                "--all",
                "--date-order",
                "--pretty=format:__COMMIT__%n%H%x09%ae%x09%ct",
                "--numstat",
                "--no-renames",
            ).stdout
            branch_output = _run_git(
                repo_root,
                "branch",
                "--format=%(refname:short)",
            ).stdout
            parent_output = _run_git(
                repo_root,
                "rev-list",
                "--all",
                "--parents",
            ).stdout

            author_counts = Counter()
            author_files = defaultdict(set)
            author_loc = defaultdict(lambda: defaultdict(lambda: {"insertions": 0, "deletions": 0}))
            author_daily_commits = defaultdict(Counter)
            commit_dates = []

            current_author = None
            for line in log_output.splitlines():
                if not line:
                    continue
                if line == "__COMMIT__":
                    current_author = None
                    continue
                if current_author is None:
                    parts = line.split("\t")
                    if len(parts) != 3:
                        continue
                    _commit_hash, author_email, committed_ts = parts
                    current_author = author_email
                    author_counts[author_email] += 1
                    committed_date = datetime.fromtimestamp(int(committed_ts))
                    commit_dates.append(committed_date)
                    author_daily_commits[author_email][committed_date.strftime("%Y-%m-%d")] += 1
                    continue

                parts = line.split("\t", 2)
                if len(parts) != 3:
                    continue
                insertions, deletions, filepath = parts
                author_files[current_author].add(filepath)
                _, ext = os.path.splitext(filepath)
                ext = ext.lower() if ext else "no_extension"
                try:
                    ins_value = int(insertions)
                except ValueError:
                    ins_value = 0
                try:
                    del_value = int(deletions)
                except ValueError:
                    del_value = 0
                author_loc[current_author][ext]["insertions"] += ins_value
                author_loc[current_author][ext]["deletions"] += del_value

            total_commits = sum(author_counts.values())
            contributors = []
            for author, count in author_counts.items():
                percent = (count / total_commits) * 100 if total_commits > 0 else 0
                total_insertions = sum(d["insertions"] for d in author_loc[author].values())
                total_deletions = sum(d["deletions"] for d in author_loc[author].values())
                contributors.append({
                    "name": author,
                    "commit_count": count,
                    "contribution_percentage": round(percent, 1),
                    "files_edited": sorted(list(author_files[author])),
                    "insertions": total_insertions,
                    "deletions": total_deletions,
                    "loc_by_type": dict(author_loc[author]),
                    "daily_commits": dict(author_daily_commits[author]),
                })

            branches = [line.strip() for line in branch_output.splitlines() if line.strip()]
            has_merges = any(len(line.split()) > 2 for line in parent_output.splitlines() if line.strip())
            project_type = "collaborative" if len(author_counts) > 1 else "individual"

            if commit_dates:
                first_commit = min(commit_dates)
                last_commit = max(commit_dates)
                duration_days = (last_commit - first_commit).days + 1
                duration_weeks = max(duration_days / 7, 1)
                commits_per_week = total_commits / duration_weeks
                commit_frequency = f"{commits_per_week:.1f} commits/week"
                first_modified = first_commit.isoformat()
                last_modified = last_commit.isoformat()
            else:
                duration_days = 0
                commit_frequency = "0 commits/week"
                first_modified = None
                last_modified = None

            return {
                "is_valid": True,
                "repo_name": repo_name,
                "repo_root": repo_root,
                "authors": list(author_counts.keys()),
                "contributors": contributors,
                "branch_count": len(branches),
                "has_merges": has_merges,
                "project_type": project_type,
                "duration_days": duration_days,
                "commit_frequency": commit_frequency,
                "first_modified": first_modified,
                "last_modified": last_modified,
            }
        except Exception as e:
            # TODO: add error to logs
            _print_banner("REPO ANALYSIS FAILED")
            message = str(e)
            if isinstance(e, subprocess.CalledProcessError) and e.stderr:
                message = f"{message}\n{e.stderr.strip()}"
            print(_center_text(message))
            return None
