# Provide alternative analyses if external services are not permitted - seperated from external service file

from datetime import datetime

def provide_alternative_analysis(parsed_data):
  
    """
    Example of what I will need from Parser vv

    [
  {
    "file_path": "ProjectA/src/main.py",
    "file_name": "main.py",
    "extension": ".py",
    "size_bytes": 1423,
    "created_at": "2025-10-31T10:23:00",
    "modified_at": "2025-11-02T14:12:00",
    "language": "Python",
    "activity": "code"
  },
  ...
]

    """

    print("Running local fallback analysis... ")

    # File count per project
  
    projects = {}
    for f in parsed_data:
        project = f["file_path"].split("/")[0]
        projects.setdefault(project, {"files": 0, "langs": set(), "activities": {}, "first": None, "last": None})
        projects[project]["files"] += 1
        projects[project]["langs"].add(f["language"])
        projects[project]["activities"][f["activity"]] = projects[project]["activities"].get(f["activity"], 0) + 1

        # track time range
        modified = datetime.fromisoformat(f["modified_at"])
        if projects[project]["first"] is None or modified < projects[project]["first"]:
            projects[project]["first"] = modified
        if projects[project]["last"] is None or modified > projects[project]["last"]:
            projects[project]["last"] = modified



    # Duration, skills, rankings
  
    summary = []
    for name, info in projects.items():
        duration = (info["last"] - info["first"]).days + 1
        skills = ", ".join(info["langs"])
        score = info["files"] + duration  # simple ranking formula
        summary.append((name, info["files"], duration, skills, score))

    # Display summaries
  
    print(f"\n{'Project':15} {'Files':>5} {'Days':>5} {'Languages':>20} {'Score':>6}")
    print("-" * 60)
    for name, files, days, langs, score in sorted(summary, key=lambda x: x[-1], reverse=True):
        print(f"{name:15} {files:5} {days:5} {langs:>20} {score:6}")

    print("\n Local analysis complete — results ranked by activity and duration.")
