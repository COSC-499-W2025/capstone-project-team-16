# Module containing methods for repository extraction
# Recieves entry marked as repo. .git file is only dealt with at the moment

from git import Repo
from collections import Counter, defaultdict
from datetime import datetime
import os
import shutil


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
            # Attempt to load repo. If this fails, it's not a valid git repo.
            repo = Repo(repo_root)

            # Collect all commits across all branches
            commits = list(repo.iter_commits('--all'))

            # Extract authors and their edited files
            author_counts = Counter()
            author_files = defaultdict(set)
            # author -> extension -> {insertions, deletions}
            author_loc = defaultdict(lambda: defaultdict(lambda: {"insertions": 0, "deletions": 0}))

            for c in commits:
                email = c.author.email
                author_counts[email] += 1
                try:
                    # c.stats.files provides a dict of changed files
                    stats = c.stats.files
                    author_files[email].update(stats.keys())
                    for filepath, stat in stats.items():
                        _, ext = os.path.splitext(filepath)
                        ext = ext.lower() if ext else "no_extension"
                        author_loc[email][ext]["insertions"] += stat.get("insertions", 0)
                        author_loc[email][ext]["deletions"] += stat.get("deletions", 0)
                except Exception:
                    pass

            # Commit count per user lets us compute contribution percentage
            total_commits = sum(author_counts.values())

            # Build contributor records (commit-count-based contribution)
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
                    "loc_by_type": dict(author_loc[author])
                })

            # Branch list for repo-level metadata
            branches = [b.name for b in repo.branches]

            # Determine if repo has merge commits (signals teamwork or branching strategy)
            has_merges = any(len(c.parents) > 1 for c in commits)

            if len(author_counts) > 1:
                project_type = "collaborative"
            else:
                project_type = "individual"

                # Compute project duration and commit frequency
            if commits:
                commit_dates = [datetime.fromtimestamp(c.committed_date) for c in commits]
                first_commit = min(commit_dates)
                last_commit = max(commit_dates)
                duration_days = (last_commit - first_commit).days + 1

                duration_weeks = max(duration_days / 7, 1)  # avoid division by zero
                commits_per_week = total_commits / duration_weeks
                commit_frequency = f"{commits_per_week:.1f} commits/week"
            else:
                duration_days = 0
                commit_frequency = "0 commits/week"

            # Return full project metadata block mapped into the entry during detailed extraction
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
                "commit_frequency": commit_frequency       
            }
        except Exception as e:
            # TODO: add error to logs
            _print_banner("REPO ANALYSIS FAILED")
            print(_center_text(str(e)))
            return None
