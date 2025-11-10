# Module containing methods for repository extraction
# Recieves entry marked as repo. .git file is only dealt with at the moment

from git import Repo
import os

        



def analyze_repo_type(repo_path):
    print("repo analyzing")
    # Only proceed if it is a .git folder indicating .git is likely a legimate repository directory
    if repo_path["extension"].endswith(".git")  and repo_path["isFile"] == False:
             # Compute repo root path by using parent directory of .git. This should be the name of the repository (usually).
        repo_root = os.path.dirname(repo_path["filename"].rstrip("/"))
        repo_name = os.path.basename(repo_root)
            #Try opening repo root. This will actually determine if .git 
        try:
            repo = Repo(repo_root)
            authors = {c.author.email for c in repo.iter_commits('--all')}
            branches = [b.name for b in repo.branches]

            has_merges = any(len(c.parents) > 1 for c in repo.iter_commits('--all'))
            collaborative_signals = sum([
                len(authors) > 1,
                len(branches) > 1,
                has_merges
            ])

            project_type = "collaborative" if collaborative_signals >= 2 else "individual"
            return {
                "is_valid": True,
                "repo_name": repo_name,
                "repo_root": repo_root,
                "authors": list(authors),
                "branch_count": len(branches),
                "has_merges": has_merges,
                "project_type": project_type
            }

        except Exception as e:
            #TODO: throw error into log
            print("Repo analysis failed:", e)
            return None
        
