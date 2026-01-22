# to print stuff - similar to whats happening in scan manager but i didn't want a circular import to analysis file so this exisit
import shutil

def _center_text(text: str) -> str:
    width = shutil.get_terminal_size(fallback=(80, 20)).columns
    if len(text) >= width:
        return text
    padding = (width - len(text) + 1) // 2
    return " " * padding + text


def _print_banner(title: str, line_char: str = "~", min_width: int = 23) -> None:
    line_width = max(len(title), min_width)
    line = line_char * line_width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))


def _print_line(text: str, file=None) -> None:
    if file:
        print(text, file=file)
    else:
        print(_center_text(text))


def is_noise(name: str) -> bool:
    """Returns True if the contributor name looks like a bot or system account."""
    n = (name or "").lower()
    return "bot" in n or "noreply" in n or "github-classroom" in n


def print_repo_summary(
    proj_name,
    repo_name,
    repo_root,
    repo_authors,
    repo_contributors,
    branch_count,
    has_merges,
    project_type,
    repo_duration_days,
    commit_frequency,
):
    _print_banner("REPOSITORY METADATA")

    def _kv(label, value):
        _print_line(f"{label:<14}: {value}")

    _kv("Project", proj_name)
    _kv("Repo Name", repo_name)
    _kv("Repo Root", repo_root)
    _kv("Authors", ", ".join(sorted(repo_authors)) if repo_authors else "None")
    _kv("Contributors", ", ".join(sorted(repo_contributors)) if repo_contributors else "None")
    _kv("Branch Count", branch_count)
    _kv("Has Merges", has_merges)
    _kv("Project Type", project_type)
    _kv("Repo Duration", f"{repo_duration_days} days")
    _kv("Commit Freq", commit_frequency)
    print()


def print_project_rankings(project_summaries, file=None):
    if not project_summaries:
        return

    if file:
        print("\nRanked Projects", file=file)
    else:
        _print_banner("RANKED PROJECTS")

    header = (
        f"{'Project':<30} "
        f"{'Files':>6} {'Days':>6} {'Code':>6} {'Test':>6} "
        f"{'Doc':>6} {'Assets':>6} "
        f"{'Languages':<25} {'Frameworks':<40} "
        f"{'Collab':>7} {'Score':>7}"
    )
    if file:
        print(f"\n{header}", file=file)
    else:
        _print_line(header)
    _print_line("-" * 155, file=file)

    for p in project_summaries:
        langs_str = p.get("languages", "") or ""
        if len(langs_str) > 25:
            langs_str = langs_str[:22] + "..."

        fw_str = p.get("frameworks", "") or ""
        if len(fw_str) > 40:
            fw_str = fw_str[:37] + "..."

        line = (
            f"{(p.get('project', 'Unknown') or 'Unknown')[:30]:<30} "
            f"{p.get('total_files', 0):6} {p.get('duration_days', 0):6} {p.get('code_files', 0):6} "
            f"{p.get('test_files', 0):6} {p.get('doc_files', 0):6} {p.get('design_files', 0):6} "
            f"{langs_str:<25} {fw_str:<40} "
            f"{p.get('is_collaborative', 'No'):>7} {p.get('score', 0):7.1f}"
        )
        _print_line(line, file=file)


def print_chronological_projects(projects_chronological, file=None):
    if not projects_chronological:
        return
    if file:
        print("\nProjects in Chronological Order", file=file)
    else:
        _print_banner("PROJECTS IN CHRONOLOGICAL ORDER")
    _print_line("-" * 80, file=file)
    for p in projects_chronological:
        _print_line(f"- {p['name']}: {p['first_used']} → {p['last_used']}", file=file)


def print_skills_timeline(skills_chronological, file=None):
    if not skills_chronological:
        return
    if file:
        print("\nSkills Exercised Over Time", file=file)
    else:
        _print_banner("SKILLS EXERCISED OVER TIME")
    _print_line("-" * 80, file=file)
    for s in skills_chronological:
        _print_line(f"- {s['first_used']} → {s['last_used']}: {s['skill']}", file=file)


def print_resume_summaries(resume_summaries, file=None):
    if not resume_summaries:
        return
    if file:
        print("\nTop Project Résumé Summaries", file=file)
    else:
        _print_banner("TOP PROJECT RESUME SUMMARIES")
    _print_line("-" * 80, file=file)
    for bullet in resume_summaries:
        _print_line(f"- {bullet}", file=file)


def print_contributor_stats(project_summaries, file=None):
    contributor_totals = {}  # name -> {adj, pct, count}

    for p in project_summaries or []:
        pc_scores = p.get("per_contributor_scores", {}) or {}
        pc_pcts = p.get("per_contributor_pct", {}) or {}
        all_contributors = set(pc_scores.keys()) | set(pc_pcts.keys())

        for person in all_contributors:
            if is_noise(person):
                continue
            contributor_totals.setdefault(person, {"adj": 0.0, "pct": 0.0, "count": 0})

            score = float(pc_scores.get(person, 0.0) or 0.0)
            pct = float(pc_pcts.get(person, 0.0) or 0.0)

            if pct > 0:
                contributor_totals[person]["count"] += 1
                contributor_totals[person]["adj"] += score
                contributor_totals[person]["pct"] += pct

    leaderboard = [(person, s["adj"], s["pct"], s["count"]) for person, s in contributor_totals.items()]
    leaderboard.sort(key=lambda x: x[1], reverse=True)

    if not leaderboard:
        return

    if file:
        print("\n=== Contributor Leaderboard (by total adjusted score) ===", file=file)
    else:
        _print_banner("CONTRIBUTOR LEADERBOARD")

    _print_line(
        f"{'Rank':>4}  {'Contributor':<28} {'Projects':>8} {'TotalAdj':>10} {'TotalPct':>9}",
        file=file,
    )
    _print_line("-" * 70, file=file)

    for i, (person, total_adj, total_pct, projects_count) in enumerate(leaderboard, start=1):
        _print_line(
            f"{i:4}  {person[:28]:<28} {projects_count:8} {total_adj:10.1f} {total_pct:8.1f}%",
            file=file,
        )

    if file:
        print("\n=== Contributor Contribution Breakdown ===", file=file)
    else:
        _print_banner("CONTRIBUTOR CONTRIBUTION BREAKDOWN")

    for person, _, _, _ in leaderboard:
        person_projects = []
        for p in project_summaries or []:
            pct = float((p.get("per_contributor_pct", {}) or {}).get(person, 0.0) or 0.0)
            if pct >= 0.1:
                adj = float((p.get("per_contributor_scores", {}) or {}).get(person, 0.0) or 0.0)
                base = float(p.get("score", 0.0) or 0.0)
                person_projects.append((p.get("project", "Unknown"), pct, adj, base))

        person_projects.sort(key=lambda x: x[2], reverse=True)
        if not person_projects:
            continue

        if file:
            print(f"\n-- {person} --", file=file)
        else:
            print()
            _print_line(f"-- {person} --", file=file)

        _print_line(f"{'Project':<32} {'Pct':>7} {'AdjScore':>10} {'Base':>10}", file=file)
        _print_line("-" * 65, file=file)

        for proj, pct, adj, base in person_projects[:3]:
            _print_line(f"{proj[:32]:<32} {pct:5.1f}% {adj:10.1f} {base:10.1f}", file=file)
