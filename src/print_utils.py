# to print stuff -moved from scan manager
import shutil
import os
import ctypes
from datetime import datetime

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

def _role_from_pct(pct: float) -> str:
    """
    Display-only role label based on contribution percent to a project.
    """
    if pct >= 50:
        return "Lead contributor"
    if pct >= 25:
        return "Core contributor"
    if pct >= 10:
        return "Major contributor"
    return "Contributor"


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

    _kv("Repo Name", repo_name)
    _kv("Repo Root", repo_root)
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
        f"{'Rank':>4} {'Show':>5} "
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

        rank_val = p.get("_custom_rank", "")
        rank_val = "-" if rank_val is None else rank_val
        show_val = "*" if p.get("selected_for_showcase") else ""  

        line = (
            f"{str(rank_val):>4} {show_val:>5} "
            f"{(p.get('project', 'Unknown') or 'Unknown')[:30]:<30} "
            f"{p.get('total_files', 0):6} {p.get('duration_days', 0):6} {p.get('code_files', 0):6} "
            f"{p.get('test_files', 0):6} {p.get('doc_files', 0):6} {p.get('design_files', 0):6} "
            f"{langs_str:<25} {fw_str:<40} "
            f"{p.get('is_collaborative', 'No'):>7} {p.get('score', 0):7.1f}"
        )
        _print_line(line, file=file)
        if p.get("highlighted_skills"):
            _print_line(f"      ↳ Highlighted skills: {', '.join(p['highlighted_skills'])}", file=file)

        if p.get("comparison_attributes"):
            attrs = p["comparison_attributes"]
            attrs_str = ", ".join(f"{k}={v}" for k, v in attrs.items())
            _print_line(f"      ↳ Comparison attributes: {attrs_str}", file=file)


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
        print("\n=== Contributor Leaderboard (by total Impact Score) ===", file=file)
    else:
        _print_banner("CONTRIBUTOR LEADERBOARD")

    _print_line(
        f"{'Rank':>4}  {'Contributor':<28} {'Projects':>8} {'Impact Score':>14} {'TotalPct':>9}",
        file=file,
    )
    _print_line("-" * 74, file=file)

    for i, (person, total_adj, total_pct, projects_count) in enumerate(leaderboard, start=1):
        _print_line(
            f"{i:4}  {person[:28]:<28} {projects_count:8} {total_adj:14.1f} {total_pct:8.1f}%",
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

        _print_line(f"{'Project':<32} {'Pct':>7} {'Impact Score':>14} {'Base':>10}", file=file)
        _print_line("-" * 69, file=file)

        for proj, pct, adj, base in person_projects[:3]:
            _print_line(f"{proj[:32]:<32} {pct:5.1f}% {adj:14.1f} {base:10.1f}", file=file)

        # key role under the contributor
            role = _role_from_pct(pct)
            _print_line(f"{'':<2}Role: {role}", file=file)

def print_full_scan_report(scan_data):
    """
    Prints the full scan report including repo metadata and all summaries.
    """
    # 1. Print Repository Metadata for each project (if available)
    project_summaries = scan_data.get("project_summaries", [])
    for p in project_summaries:
        if p.get("project"):
            repo_name = p.get("repo_name") or p.get("project")
            # Wrap strings in list because print_repo_summary expects iterables to join
            authors_arg = [p.get("authors")] if p.get("authors") else []
            contribs_arg = [p.get("contributors")] if p.get("contributors") else []
            
            print_repo_summary(
                p.get("project"),
                repo_name,
                p.get("repo_root", ""),
                authors_arg,
                contribs_arg,
                p.get("branch_count", 0),
                p.get("has_merges", "Unknown"),
                p.get("project_type", "Unknown"),
                p.get("repo_duration_days", 0),
                p.get("commit_frequency", "Unknown")
            )

    # 2. Print the rest of the reports
    print_project_rankings(scan_data.get("project_summaries", []))
    print_chronological_projects(scan_data.get("projects_chronological", []))
    print_skills_timeline(scan_data.get("skills_chronological", []))
    print_resume_summaries(scan_data.get("resume_summaries", []))
    print_contributor_stats(scan_data.get("project_summaries", []))


def format_timestamp(value):
    """Formats ISO timestamp to readable string."""
    if not value:
        return value
    try:
        ts = value.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).strftime("%b %d, %Y %I:%M %p")
    except (TypeError, ValueError):
        return value


def print_scan_list(scans):
    """Prints a numbered list of scans."""
    for i, s in enumerate(scans, start=1):
        ts = format_timestamp(s['timestamp'])
        print(
            _center_text(f"{i}. Scan {s['summary_id']} - {ts} ({s['analysis_mode']})")
        )


def _input_with_prefill(prompt, text):
    """
    Prompts for input with a default value pre-filled.
    Works on Windows (via ctypes) and Unix (via readline).
    """
    if not text:
        return input(prompt)

    if os.name == 'nt':
        try:
            # Windows implementation using WriteConsoleInputW
            class KEY_EVENT_RECORD(ctypes.Structure):
                _fields_ = [
                    ("bKeyDown", ctypes.c_int),
                    ("wRepeatCount", ctypes.c_ushort),
                    ("wVirtualKeyCode", ctypes.c_ushort),
                    ("wVirtualScanCode", ctypes.c_ushort),
                    ("uChar", ctypes.c_wchar),
                    ("dwControlKeyState", ctypes.c_ulong)
                ]
            
            class INPUT_RECORD_Event(ctypes.Union):
                _fields_ = [("KeyEvent", KEY_EVENT_RECORD)]
            
            class INPUT_RECORD(ctypes.Structure):
                _fields_ = [
                    ("EventType", ctypes.c_ushort),
                    ("Event", INPUT_RECORD_Event)
                ]

            STD_INPUT_HANDLE = -10
            hConsoleInput = ctypes.windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
            
            n = len(text)
            records = (INPUT_RECORD * n)()
            
            for i, char in enumerate(text):
                records[i].EventType = 0x0001 # KEY_EVENT
                records[i].Event.KeyEvent.bKeyDown = 1
                records[i].Event.KeyEvent.wRepeatCount = 1
                records[i].Event.KeyEvent.wVirtualKeyCode = 0
                records[i].Event.KeyEvent.wVirtualScanCode = 0
                records[i].Event.KeyEvent.uChar = char
                records[i].Event.KeyEvent.dwControlKeyState = 0

            written = ctypes.c_ulong(0)
            ctypes.windll.kernel32.WriteConsoleInputW(
                hConsoleInput,
                ctypes.byref(records),
                n,
                ctypes.byref(written)
            )
        except Exception:
            pass
    else:
        try:
            import readline
            def hook():
                readline.insert_text(text)
                readline.redisplay()
            readline.set_startup_hook(hook)
        except ImportError:
            pass

    try:
        return input(prompt)
    finally:
        if os.name != 'nt':
            try:
                import readline
                readline.set_startup_hook()
            except ImportError:
                pass
