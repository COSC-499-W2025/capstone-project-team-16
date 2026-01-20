import os
import shutil
from datetime import datetime
from db import delete_full_scan_by_id, get_full_scan_by_id, list_full_scans
from permission_manager import get_yes_no
from resume_generator import generate_resume, generate_contributor_portfolio


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


def _print_header(title, width=28, sep="="):
    line = sep * width
    print()
    print(_center_text(line))
    print(_center_text(title))
    print(_center_text(line))


def _print_menu(title, options, prompt="Choose an option: "):
    _print_banner(title)
    for key, label in options:
        print(_center_text(f"{key}) {label}"))
    return input(_center_text(prompt)).strip()


def _print_line(text, file=None):
    if file:
        print(text, file=file)
    else:
        print(_center_text(text))


def _print_scan_list(scans):
    for i, s in enumerate(scans, start=1):
        print(_center_text(f"{i}. [ID: {s['summary_id']}] {s['timestamp']} ({s['analysis_mode']})"))


def _format_timestamp(value):
    if not value:
        return value
    try:
        ts = value.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).strftime("%b %d, %Y %I:%M %p")
    except (TypeError, ValueError):
        return value


def scan_manager():
    """
    Main entry point for the Scan Manager UI.
    Provides a loop for viewing, generating portfolios, and deleting past scans.
    """
    while True:
        choice = _print_menu(
            "SCAN MANAGER",
            [
                ("0", "Return to home screen"),
                ("1", "View stored project analyses"),
                ("2", "Generate Resume/Portfolio"),
                ("3", "Delete stored scans"),
            ],
            prompt="Choose an option (0-3): ",
        )

        if choice == "1":
            view_full_scan_details()

        elif choice == "2":
            generate_portfolio_menu()

        elif choice == "3":
            delete_full_scan()

        elif choice == "0":
            break

        else:
            print("Invalid input. Try again.")


def view_full_scan_details():
    """
    Lists all saved scans, allows the user to select one, and prints a detailed report.
    The report includes project rankings, timelines, skills, and contributor stats.
    """
    scans = list_full_scans()
    if not scans:
        print("No scans found.")
        return

    # 1. List available scans (lightweight metadata only)
    print()
    print(_center_text("Select a scan to view:"))
    _print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        print(_center_text("Canceled."))
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print("Invalid selection.")
        return

    # 2. Fetch the full heavy JSON data for the selected scan
    summary_id = scans[idx]["summary_id"]
    scan = get_full_scan_by_id(summary_id)
    
    if not scan:
        print("Error: Could not retrieve scan data.")
        return
    data = scan["scan_data"]

    # Extract specific sections from the JSON blob
    project_summaries = data.get("project_summaries", [])
    resume_summaries = data.get("resume_summaries", [])
    skills_chronological = data.get("skills_chronological", [])
    projects_chronological = data.get("projects_chronological", [])
    contributor_profiles = data.get("contributor_profiles", {})

    # 3. Display the report sections using helper functions
    _print_header("FULL SCAN DETAILS")
    print(f"Timestamp: {_format_timestamp(scan['timestamp'])}")
    print(f"Mode: {scan['analysis_mode']}")
    print("=" * 28)

    # Print various sections of the report
    print_project_rankings(project_summaries)
    print_chronological_projects(projects_chronological)
    print_skills_timeline(skills_chronological)
    print_resume_summaries(resume_summaries)
    print_contributor_stats(project_summaries)

    print("\nEnd of scan view.\n")

    # Option to export the displayed report to a text file
    if get_yes_no("Do you want to export this report to a text file?"):
        from file_parser import OUTPUT_DIR
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = f"scan_report_{scan['timestamp'].replace(':', '-').replace(' ', '_')}.txt"
        txt_path = os.path.join(OUTPUT_DIR, filename)
        
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                print(f"Scan Report - {_format_timestamp(scan['timestamp'])}", file=f)
                print("=" * 60, file=f)
                print_project_rankings(project_summaries, file=f)
                print_chronological_projects(projects_chronological, file=f)
                print_skills_timeline(skills_chronological, file=f)
                print_resume_summaries(resume_summaries, file=f)
                print_contributor_stats(project_summaries, file=f)
            print(f"Report saved to: {txt_path}")
        except Exception as e:
            print(f"Error saving report: {e}")


def delete_full_scan():
    """
    Lists all saved scans and allows the user to permanently delete one from the database.
    """
    scans = list_full_scans()
    if not scans:
        print("No saved scans found to delete.")
        return

    # Display list for deletion
    print()
    print(_center_text("Select a scan to delete:"))
    _print_scan_list(scans)

    choice = input(_center_text("Enter number (or 0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        print("Deletion canceled.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print("Invalid selection.")
        return

    scan = scans[idx]

    # Confirm before deletion
    if get_yes_no(f"Are you sure you want to delete the scan from {scan['timestamp']}?"):
        success = delete_full_scan_by_id(scan["summary_id"])
        print(_center_text("Scan deleted.") if success else "Failed to delete scan.")
    else:
        print("Deletion canceled.")


def generate_portfolio_menu():
    """
    Menu for generating Word documents from a saved scan.
    Options:
    1) Full Project Resume (summary of all projects in the scan).
    2) Individual Contributor Portfolio (specific to one person).
    """
    scans = list_full_scans()
    if not scans:
        print("No scans found.")
        return

    # Select scan first
    print()
    print(_center_text("Select a scan to generate portfolio from:"))
    _print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        print(_center_text("Canceled."))
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print("Invalid selection.")
        return

    # Fetch full data to access contributor profiles and project details
    summary_id = scans[idx]["summary_id"]
    
    scan = get_full_scan_by_id(summary_id)
    if not scan:
        print("Error: Could not retrieve scan data.")
        return
    data = scan["scan_data"]
    
    # Choose generation type
    _print_header("GENERATION OPTIONS", width=48, sep="-")
    print(_center_text("1) Full Project Resume (Summary of all projects)"))
    print(_center_text("2) Individual Contributor Portfolio"))
    
    gen_choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    
    if gen_choice == "1":
        # Generate full resume (all projects summary)
        txt_path, docx_path = generate_resume(
            data.get("project_summaries", []),
            data.get("projects_chronological", []),
            data.get("skills_chronological", []),
            scan_timestamp=scan["timestamp"]
        )
        print(f"\nSUCCESS: Resume saved to:\n{txt_path}\n{docx_path}")
        return

    elif gen_choice != "2":
        print(_center_text("Canceled."))
        return

    # --- Contributor Portfolio Logic ---
    contributor_profiles = data.get("contributor_profiles", {})
    project_summaries = data.get("project_summaries", [])

    if not contributor_profiles:
        print(_center_text("No contributor data found in this scan."))
        return

    # List contributors
    contributors = sorted(contributor_profiles.keys())
    # Filter out bots/noise using the helper function
    contributors = [c for c in contributors if not is_noise(c)]
    
    if not contributors:
        print("No valid contributors found.")
        return

    print()
    print(_center_text("Select a contributor:"))
    for i, c in enumerate(contributors, 1):
        print(_center_text(f"{i}. {c}"))
    
    sel = input(_center_text("Enter number (0 to cancel): ")).strip()
    if sel.isdigit():
        idx = int(sel) - 1
        if 0 <= idx < len(contributors):
            target_user = contributors[idx]
            profile = contributor_profiles[target_user]
            
            # Need a map of project_name -> project_data for the generator
            all_projects_map = {p["project"]: p for p in project_summaries}
            
            out_path = generate_contributor_portfolio(target_user, profile, all_projects_map, scan_timestamp=scan["timestamp"])
            if out_path:
                print(f"\nSUCCESS: Portfolio saved to:\n{out_path}")
        elif idx != -1:
            print("Invalid selection.")
    else:
        print(_center_text("Canceled."))


# --------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------

def is_noise(name):
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
    """Prints metadata about a specific repository analysis."""
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
    """
    Prints a table of projects ranked by score.
    Supports redirection to a file via the 'file' argument.
    """
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
        # Truncate long language/framework lists for display
        langs_str = p.get("languages", "")
        if len(langs_str) > 25:
            langs_str = langs_str[:22] + "..."

        fw_str = p.get("frameworks", "")
        if len(fw_str) > 40:
            fw_str = fw_str[:37] + "..."

        line = (
            f"{p.get('project', 'Unknown')[:30]:<30} "
            f"{p.get('total_files', 0):6} {p.get('duration_days', 0):6} {p.get('code_files', 0):6} "
            f"{p.get('test_files', 0):6} {p.get('doc_files', 0):6} {p.get('design_files', 0):6} "
            f"{langs_str:<25} {fw_str:<40} "
            f"{p.get('is_collaborative', 'No'):>7} {p.get('score', 0):7.1f}"
        )
        _print_line(line, file=file)

def print_chronological_projects(projects_chronological, file=None):
    """
    Prints a list of projects ordered by start date.
    """
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
    """
    Prints a timeline of when specific skills were first and last used.
    """
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
    """
    Prints generated resume bullet points for top projects.
    """
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
    """
    Calculates and prints a leaderboard of contributors based on their impact scores,
    followed by a breakdown of their contributions per project.
    """
    contributor_totals = {}  # name -> {adj, pct, count}

    for p in project_summaries:
        pc_scores = p.get("per_contributor_scores", {})
        pc_pcts = p.get("per_contributor_pct", {})

        all_contributors = set(pc_scores.keys()) | set(pc_pcts.keys())

        for person in all_contributors:
            # Skip bots
            if is_noise(person):
                continue

            if person not in contributor_totals:
                contributor_totals[person] = {"adj": 0.0, "pct": 0.0, "count": 0}

            score = pc_scores.get(person, 0.0)
            pct = pc_pcts.get(person, 0.0)

            # Aggregate stats if they have a non-zero contribution
            if pct > 0:
                contributor_totals[person]["count"] += 1
                contributor_totals[person]["adj"] += score
                contributor_totals[person]["pct"] += pct

    # Convert to list for sorting
    leaderboard = []
    for person, stats in contributor_totals.items():
        leaderboard.append((person, stats["adj"], stats["pct"], stats["count"]))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    # Print Leaderboard Table
    if leaderboard:
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

        # Print Detailed Breakdown per Person
        if file:
            print("\n=== Contributor Contribution Breakdown ===", file=file)
        else:
            _print_banner("CONTRIBUTOR CONTRIBUTION BREAKDOWN")
        for person, _, _, _ in leaderboard:
            person_projects = []
            for p in project_summaries:
                pct = p.get("per_contributor_pct", {}).get(person, 0.0)
                if pct >= 0.1:
                    adj = p.get("per_contributor_scores", {}).get(person, 0.0)
                    base = p.get("score", 0.0)
                    person_projects.append((p["project"], pct, adj, base))
            
            person_projects.sort(key=lambda x: x[2], reverse=True)
            if person_projects:
                if file:
                    print(f"\n-- {person} --", file=file)
                else:
                    print()
                    _print_line(f"-- {person} --", file=file)
                _print_line(f"{'Project':<32} {'Pct':>7} {'AdjScore':>10} {'Base':>10}", file=file)
                _print_line("-" * 65, file=file)
                for proj, pct, adj, base in person_projects[:3]:
                    _print_line(
                        f"{proj[:32]:<32} {pct:5.1f}% {adj:10.1f} {base:10.1f}",
                        file=file,
                    )
