import json
from db import list_full_scans, get_full_scan_by_id, delete_full_scan_by_id
from permission_manager import get_yes_no
from resume_generator import generate_resume, generate_contributor_portfolio

def scan_manager():
    """
    Main entry point for the Scan Manager UI.
    Provides a loop for viewing, generating portfolios, and deleting past scans.
    """
    while True:
        print("\n===== SCAN MANAGER =====")
        print("1. View stored project analyses")
        print("2. Generate Resume/Portfolio")
        print("3. Delete stored scans")
        print("4. Return to home screen")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_full_scan_details()

        elif choice == "2":
            generate_portfolio_menu()

        elif choice == "3":
            delete_full_scan()

        elif choice == "4":
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
    print("Select a scan to view:")
    for i, s in enumerate(scans, start=1):
        print(f"{i}. {s['timestamp']} ({s['analysis_mode']})")

    choice = input("Enter number (0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        print("Canceled.")
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
    data = scan["project_summaries_json"]

    project_summaries = data.get("project_summaries", [])
    resume_summaries = data.get("resume_summaries", [])
    skills_chronological = data.get("skills_chronological", [])
    projects_chronological = data.get("projects_chronological", [])
    contributor_profiles = data.get("contributor_profiles", {})

    # 3. Display the report sections using helper functions
    print("\n============================")
    print(" FULL SCAN DETAILS")
    print("============================")
    print(f"Timestamp: {scan['timestamp']}")
    print(f"Mode: {scan['analysis_mode']}")
    print("============================\n")

    print_project_rankings(project_summaries)
    print_chronological_projects(projects_chronological)
    print_skills_timeline(skills_chronological)
    print_resume_summaries(resume_summaries)
    print_contributor_stats(project_summaries)

    print("\nEnd of scan view.\n")


def delete_full_scan():
    """
    Lists all saved scans and allows the user to permanently delete one from the database.
    """
    scans = list_full_scans()
    if not scans:
        print("No saved scans found to delete.")
        return

    print("\nSelect a scan to delete:")
    for i, s in enumerate(scans, start=1):
        print(f"{i}. [{s['timestamp']}]  Mode: {s['analysis_mode']}")

    choice = input("Enter number (or 0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        print("Deletion canceled.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print("Invalid selection.")
        return

    scan = scans[idx]

    if get_yes_no(f"Are you sure you want to delete the scan from {scan['timestamp']}?"):
        success = delete_full_scan_by_id(scan["summary_id"])
        print("Scan deleted." if success else "Failed to delete scan.")
    else:
        print("Deletion canceled.")


def generate_portfolio_menu():
    """
    Menu for generating Word documents from a saved scan.
    Options:
    1. Full Project Resume (summary of all projects in the scan).
    2. Individual Contributor Portfolio (specific to one person).
    """
    scans = list_full_scans()
    if not scans:
        print("No scans found.")
        return

    print("\nSelect a scan to generate portfolio from:")
    for i, s in enumerate(scans, start=1):
        print(f"{i}. {s['timestamp']} ({s['analysis_mode']})")

    choice = input("Enter number (0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        print("Canceled.")
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
    data = scan["project_summaries_json"]
    
    print("\n------------------------------------------------")
    print(" GENERATION OPTIONS")
    print("------------------------------------------------")
    print("1. Full Project Resume (Summary of all projects)")
    print("2. Individual Contributor Portfolio")
    
    gen_choice = input("Enter number (0 to cancel): ").strip()
    
    if gen_choice == "1":
        # Generate full resume
        generate_resume(
            data.get("project_summaries", []),
            data.get("projects_chronological", []),
            data.get("skills_chronological", [])
        )
        input("\nPress Enter to continue...")
        return

    elif gen_choice != "2":
        print("Canceled.")
        return

    # --- Contributor Portfolio Logic ---
    contributor_profiles = data.get("contributor_profiles", {})
    project_summaries = data.get("project_summaries", [])

    if not contributor_profiles:
        print("No contributor data found in this scan.")
        return

    # List contributors
    contributors = sorted(contributor_profiles.keys())
    # Filter out bots/noise using the helper function
    contributors = [c for c in contributors if not is_noise(c)]
    
    if not contributors:
        print("No valid contributors found.")
        return

    print("\nSelect a contributor:")
    for i, c in enumerate(contributors, 1):
        print(f"{i}. {c}")
    
    sel = input("\nEnter number (0 to cancel): ").strip()
    if sel.isdigit():
        idx = int(sel) - 1
        if 0 <= idx < len(contributors):
            target_user = contributors[idx]
            profile = contributor_profiles[target_user]
            
            # Need a map of project_name -> project_data for the generator
            all_projects_map = {p["project"]: p for p in project_summaries}
            
            out_path = generate_contributor_portfolio(target_user, profile, all_projects_map)
            if out_path:
                print(f"\nSUCCESS: Portfolio saved to:\n{out_path}")
        elif idx != -1:
            print("Invalid selection.")
    else:
        print("Canceled.")


# --------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------

def is_noise(name):
    """Returns True if the contributor name looks like a bot or system account."""
    n = (name or "").lower()
    return "bot" in n or "noreply" in n or "github-classroom" in n

def print_project_rankings(project_summaries):
    if not project_summaries:
        return
    print("\nRanked Projects")
    print(
        f"\n{'Project':<30} "
        f"{'Files':>6} {'Days':>6} {'Code':>6} {'Test':>6} "
        f"{'Doc':>6} {'Des':>6} "
        f"{'Languages':<25} {'Frameworks':<40} "
        f"{'Collab':>7} {'Score':>7}"
    )
    print("-" * 155)

    for p in project_summaries:
        # Truncate long language/framework lists for display
        langs_str = p.get("languages", "")
        if len(langs_str) > 25:
            langs_str = langs_str[:22] + "..."

        fw_str = p.get("frameworks", "")
        if len(fw_str) > 40:
            fw_str = fw_str[:37] + "..."

        print(
            f"{p.get('project', 'Unknown')[:30]:<30} "
            f"{p.get('total_files', 0):6} {p.get('duration_days', 0):6} {p.get('code_files', 0):6} "
            f"{p.get('test_files', 0):6} {p.get('doc_files', 0):6} {p.get('design_files', 0):6} "
            f"{langs_str:<25} {fw_str:<40} "
            f"{p.get('is_collaborative', 'No'):>7} {p.get('score', 0):7.1f}"
        )

def print_chronological_projects(projects_chronological):
    if not projects_chronological:
        return
    print("\nProjects in Chronological Order")
    print("-" * 80)
    for p in projects_chronological:
        print(f"- {p['name']}: {p['first_used']} → {p['last_used']}")

def print_skills_timeline(skills_chronological):
    if not skills_chronological:
        return
    print("\nSkills Exercised Over Time")
    print("-" * 80)
    for s in skills_chronological:
        print(f"- {s['first_used']} → {s['last_used']}: {s['skill']}")

def print_resume_summaries(resume_summaries):
    if not resume_summaries:
        return
    print("\nTop Project Résumé Summaries")
    print("-" * 80)
    for bullet in resume_summaries:
        print(f"- {bullet}")

def print_contributor_stats(project_summaries):
    contributor_totals = {}  # name -> {adj, pct, count}

    for p in project_summaries:
        pc_scores = p.get("per_contributor_scores", {})
        pc_pcts = p.get("per_contributor_pct", {})

        all_contributors = set(pc_scores.keys()) | set(pc_pcts.keys())

        for person in all_contributors:
            if is_noise(person):
                continue

            if person not in contributor_totals:
                contributor_totals[person] = {"adj": 0.0, "pct": 0.0, "count": 0}

            score = pc_scores.get(person, 0.0)
            pct = pc_pcts.get(person, 0.0)

            if pct > 0:
                contributor_totals[person]["count"] += 1
                contributor_totals[person]["adj"] += score
                contributor_totals[person]["pct"] += pct

    leaderboard = []
    for person, stats in contributor_totals.items():
        leaderboard.append((person, stats["adj"], stats["pct"], stats["count"]))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    if leaderboard:
        print("\n=== Contributor Leaderboard (by total adjusted score) ===")
        print(f"{'Rank':>4}  {'Contributor':<28} {'Projects':>8} {'TotalAdj':>10} {'TotalPct':>9}")
        print("-" * 70)
        for i, (person, total_adj, total_pct, projects_count) in enumerate(leaderboard, start=1):
            print(f"{i:4}  {person[:28]:<28} {projects_count:8} {total_adj:10.1f} {total_pct:8.1f}%")

        print("\n=== Contributor Contribution Breakdown ===")
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
                print(f"\n-- {person} --")
                print(f"{'Project':<32} {'Pct':>7} {'AdjScore':>10} {'Base':>10}")
                print("-" * 65)
                for proj, pct, adj, base in person_projects[:3]:
                    print(f"{proj[:32]:<32} {pct:5.1f}% {adj:10.1f} {base:10.1f}")