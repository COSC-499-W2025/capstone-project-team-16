# Builds both a plain text summary and a Word resume

import os
from datetime import datetime
from collections import Counter

from docx import Document
from docx.shared import Pt


def build_project_line(p: dict) -> str:
    """
    Builds a short resume description about a project (General/Team view).
    Used for the full resume summary.
    """
    name = p.get("project", "Unknown")
    langs = p.get("languages", "Unknown")
    skills = p.get("skills", "NA")
    frameworks = p.get("frameworks", "None")
    duration = p.get("duration_days", 0)
    code_files = p.get("code_files", 0)
    test_files = p.get("test_files", 0)
    project_type = p.get("project_type", "software")

    pieces = []

    main = f"Contributed to project '{name}'"
    if project_type and project_type.lower() != "unknown":
        main = f"Contributed to {project_type.lower()} project '{name}'"
    if langs and langs.lower() != "unknown":
        main += f" using {langs}"
    pieces.append(main)

    details = []
    if code_files:
        details.append(f"{code_files} code files")
    if test_files:
        details.append(f"{test_files} test files")

    if duration:
        details.append(f"over {duration} days")

    if details:
        pieces.append("comprising " + ", ".join(details))

    if frameworks and frameworks not in ("None", "NA"):
        pieces.append(f"with frameworks such as {frameworks}")

    return "; ".join(pieces) + "."


def _write_txt_summary(
    txt_path: str,
    top_projects: list[dict],
    chronological_projects: list[dict],
    skills_output: list[dict],
) -> None:
    """
    plain-text summary for debugging / quick copy paste. we can remove this if we don't need a text file.
    """
    lines: list[str] = []
    lines.append("PROJECT PORTFOLIO SUMMARY")
    lines.append("=" * 60)
    lines.append("")

    # Top projects
    lines.append("Top Projects")
    lines.append("Projects")
    lines.append("-" * 40)
    for p in top_projects:
        lines.append(f"- {build_project_line(p)}")
    lines.append("")

    # Project timeline
    lines.append("Chronological Project Timeline")
    lines.append("-" * 40)
    for p in chronological_projects:
        lines.append(
            f"- {p['name']} – {p['first_used']} → {p['last_used']}"
        )
    lines.append("")

    # Skills over time
    lines.append("Skills Used Over Time")
    lines.append("-" * 40)
    for row in skills_output:
        lines.append(
            f"- {row['skill']} – {row['first_used']} → {row['last_used']}"
        )
    lines.append("")

    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_docx_resume(
    docx_path: str,
    top_projects: list[dict],
    chronological_projects: list[dict],
    skills_output: list[dict],
) -> str:

    """
    Word document
    """
    os.makedirs(os.path.dirname(docx_path), exist_ok=True)

    doc = Document()

    def _fmt_date(val):
        if isinstance(val, datetime):
            return val.date().isoformat()
        if isinstance(val, str):
            # If it's already a string (from DB), try to keep just the date part
            return val.split("T")[0]
        return ""

    # --- Header / title ---
    title = doc.add_heading("Project Portfolio Resume", level=0)
    title.runs[0].font.size = Pt(20)

    # Placeholder for user info (later on, when we store user infos this need to be updated)
    info_p = doc.add_paragraph()
    info_p.add_run("Name: ").bold = True
    info_p.add_run("  |  Email: .gmail.com  |  GitHub: github.com/")
    info_p.style.font.size = Pt(10)

    doc.add_paragraph()  # blank line

    # --- Top Projects section ---
    doc.add_heading("Top Projects", level=1)
    doc.add_heading("Projects", level=1)

    if not top_projects:
        doc.add_paragraph("No projects detected.", style="List Bullet")
    else:
        for p in top_projects:
            # First line: bold project name + timeframe
            first_date = _fmt_date(p.get("first_modified"))
            last_date = _fmt_date(p.get("last_modified"))

            para = doc.add_paragraph(style="List Bullet")
            run_name = para.add_run(p["project"])
            run_name.bold = True

            if first_date and last_date:
                para.add_run(f"  ({first_date} – {last_date})")

            # Second line (same bullet) – description
            para.add_run("\n" + build_project_line(p))

    doc.add_paragraph()  # spacing

    # --- Chronological Project Timeline ---
    doc.add_heading("Project Timeline", level=1)
    for p in chronological_projects:
        para = doc.add_paragraph(style="List Bullet")
        para.add_run(p["name"]).bold = True
        para.add_run(f" – {p['first_used']} → {p['last_used']}")

    doc.add_paragraph()

    # --- Skills Used Over Time ---
    doc.add_heading("Skills Used Over Time", level=1)

    if skills_output:
        table = doc.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Skill"
        hdr_cells[1].text = "First Used"
        hdr_cells[2].text = "Last Used"

        for row in skills_output:
            row_cells = table.add_row().cells
            row_cells[0].text = row["skill"]
            row_cells[1].text = row["first_used"]
            row_cells[2].text = row["last_used"]
    else:
        doc.add_paragraph("No skills detected.", style="List Bullet")

    # footer note
    doc.add_paragraph()
    foot = doc.add_paragraph()
    foot_run = foot.add_run(
        "Generated automatically from code repositories using Skill Scope."
    )
    foot_run.italic = True
    foot_run.font.size = Pt(8)

    while True:
        try:
            doc.save(docx_path)
            return docx_path
        except PermissionError:
            print(f"\n[!] Could not save to '{docx_path}' because it is open.")
            print("Please close the file and press Enter to retry, or type 'cancel' to stop.")
            if input("> ").strip().lower() == "cancel":
                return None


def generate_resume(
    project_summaries: list[dict],
    chronological_projects: list[dict],
    skills_output: list[dict],
    scan_timestamp: str = None
) -> tuple[str, str]:
    """
    Main entry point called from alternative_analysis.analyze_projects.
    """
    # Sort projects by score again just in case
    sorted_projects = sorted(
        project_summaries, key=lambda p: p.get("score", 0), reverse=True
    )

    from file_parser import OUTPUT_DIR

    suffix = ""
    if scan_timestamp:
        # Clean timestamp for filename
        suffix = "_" + scan_timestamp.replace(":", "-").replace(" ", "_")

    txt_path = os.path.join(OUTPUT_DIR, f"resume_output{suffix}.txt")
    docx_path = os.path.join(OUTPUT_DIR, f"portfolio_resume{suffix}.docx")

    _write_txt_summary(txt_path, sorted_projects, chronological_projects, skills_output)
    final_docx_path = _write_docx_resume(docx_path, sorted_projects, chronological_projects, skills_output)

    return txt_path, final_docx_path


def _build_personal_project_description(project_name, project_context, user_stats):
    """
    Constructs a sentence describing the user's specific contribution to a project.
    """
    # Context from the project as a whole
    langs = project_context.get("languages", "Unknown")
    skills = project_context.get("skills", "NA")
    frameworks = project_context.get("frameworks", "None")
    
    # User specific stats
    u_files = user_stats.get("files_worked", 0)
    u_code = user_stats.get("user_code_files", 0)
    u_test = user_stats.get("user_test_files", 0)
    u_doc = user_stats.get("user_doc_files", 0)
    u_design = user_stats.get("user_design_files", 0)
    
    parts = []
    parts.append(f"Contributed to '{project_name}'")
    
    if langs and langs != "Unknown":
        parts.append(f"using {langs}")
        
    # Work breakdown
    work_details = []
    if u_code: work_details.append(f"{u_code} code files")
    if u_test: work_details.append(f"{u_test} test files")
    if u_doc: work_details.append(f"{u_doc} documents")
    if u_design: work_details.append(f"{u_design} design assets")
    
    if work_details:
        parts.append("working on " + ", ".join(work_details))
    elif u_files:
        parts.append(f"working on {u_files} files")
        
    if frameworks and frameworks not in ("None", "NA"):
        parts.append(f"utilizing frameworks such as {frameworks}")
        
    return " ".join(parts) + "."

def generate_contributor_portfolio(
    contributor_name: str,
    profile_data: dict,
    all_projects_map: dict,
    scan_timestamp: str = None
) -> str:
    """
    Generates a specific portfolio Word doc for a single contributor.
    """
    if not profile_data:
        print(f"Error: No profile data found for {contributor_name}")
        return None

    from file_parser import OUTPUT_DIR
    
    safe_name = "".join(c for c in contributor_name if c.isalnum() or c in (' ', '_', '-')).strip()
    
    suffix = ""
    if scan_timestamp:
        suffix = "_" + scan_timestamp.replace(":", "-").replace(" ", "_")
        
    filename = f"Portfolio_{safe_name}{suffix}.docx"
    docx_path = os.path.join(OUTPUT_DIR, filename)
    
    doc = Document()
    
    # --- Header ---
    # Try to make the name look a bit better (e.g. capitalize words)
    if "@" in contributor_name:
        # If email, use local part as name
        display_name = contributor_name.split("@")[0].replace(".", " ").replace("_", " ").title()
    else:
        display_name = contributor_name.replace(".", " ").replace("_", " ").title()
    
    title = doc.add_heading(f"Portfolio: {display_name}", level=0)
    title.runs[0].font.size = Pt(24)
    doc.add_paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}")
    
    # --- Professional Summary ---
    doc.add_heading("Professional Summary", level=1)
    
    skills = profile_data.get("skills", [])
    projects_ref = profile_data.get("projects", [])
    
    if "@" in contributor_name:
        summary_text = f"Contributor ({contributor_name}) with active contributions across {len(projects_ref)} project(s)."
    else:
        summary_text = f"Contributor with active contributions across {len(projects_ref)} project(s)."

    if skills:
        top_skills = ", ".join(skills[:5])
        summary_text += f" Demonstrated technical proficiency in: {top_skills}."
    doc.add_paragraph(summary_text)
    doc.add_paragraph()

    # --- Technical Skills ---
    doc.add_heading("Technical Skills", level=1)
    if skills:
        p = doc.add_paragraph()
        p.add_run("Languages & Technologies: ").bold = True
        p.add_run(", ".join(skills))
    else:
        doc.add_paragraph("No specific skills detected from file extensions.")
    doc.add_paragraph()

    # --- Project Contributions ---
    doc.add_heading("Project Contributions", level=1)
    
    # Get project details and sort by their contribution score
    user_projects = []
    for p_ref in projects_ref:
        p_name = p_ref.get("name", "Unknown Project")
        
        # Extract user stats directly from the profile reference
        user_stats = {
            "files_worked": p_ref.get("files_worked", 0),
            "files_list": p_ref.get("files_list", []),
            "user_code_files": p_ref.get("user_code_files", 0),
            "user_test_files": p_ref.get("user_test_files", 0),
            "user_doc_files": p_ref.get("user_doc_files", 0),
            "user_design_files": p_ref.get("user_design_files", 0),
            "pct": p_ref.get("pct", 0.0),
            "score": p_ref.get("score", 0.0),
            "insertions": p_ref.get("insertions", 0),
            "deletions": p_ref.get("deletions", 0),
            "commit_count": p_ref.get("commit_count", 0)
        }

        # Fallback: if counts are zero but list exists, update files_worked
        if user_stats["files_worked"] == 0 and user_stats["files_list"]:
             user_stats["files_worked"] = len(user_stats["files_list"])

        # Get general project context (dates, frameworks, etc.)
        project_context = all_projects_map.get(p_name, {})
        
        # Store everything needed for generation
        user_projects.append((p_name, user_stats, project_context))

    # Sort by the user's specific impact (score)
    user_projects.sort(key=lambda x: x[1]["score"], reverse=True)

    if not user_projects:
        doc.add_paragraph("No project contributions found.")
    else:
        for p_name, u_stats, p_context in user_projects:
            pct = u_stats["pct"]
            # Skip negligible contributions only if no actual work recorded (Fixing indentation/logic)
            if pct < 0.1 and u_stats.get('files_worked', 0) == 0 and u_stats.get('commit_count', 0) == 0:
                continue

            # Format Dates
            start_date = p_context.get("first_modified")
            end_date = p_context.get("last_modified")
            date_str = ""
            
            def _fmt_d(d):
                if isinstance(d, str):
                    try: return datetime.fromisoformat(d).strftime('%Y-%m-%d')
                    except: return d
                if isinstance(d, datetime):
                    return d.strftime('%Y-%m-%d')
                return str(d)

            if start_date and end_date:
                date_str = f" ({_fmt_d(start_date)} – {_fmt_d(end_date)})"

            # Project Header
            p_head = doc.add_heading(level=2)
            p_head.add_run(p_name).bold = True
            if date_str:
                p_head.add_run(date_str).font.size = Pt(11)
            
            # Project Scope Stats (Total project context)
            scope_p = doc.add_paragraph()
            scope_p.style.font.size = Pt(9)
            scope_p.add_run("Project Scope: ").bold = True
            scope_p.add_run(f"{p_context.get('total_files', 0)} files, {p_context.get('duration_days', 0)} days. Languages: {p_context.get('languages', 'Unknown')}")

            # Stats
            stats_p = doc.add_paragraph()
            stats_p.add_run(f"Contribution: {pct:.1f}%").bold = True 
            stats_p.add_run(f"  |  Impact Score: {u_stats['score']:.1f}")
            
            if u_stats.get("files_worked"):
                stats_p.add_run(f"  |  Files Edited: {u_stats['files_worked']}")
            
            if u_stats.get("commit_count"):
                stats_p.add_run(f"  |  Commits: {u_stats['commit_count']}")
            
            if u_stats.get("insertions") or u_stats.get("deletions"):
                stats_p.add_run(f"  |  Lines: +{u_stats['insertions']} / -{u_stats['deletions']}")

            # Add breakdown of file types
            types_breakdown = []
            if u_stats["user_code_files"] > 0:
                types_breakdown.append(f"{u_stats['user_code_files']} Code")
            if u_stats["user_test_files"] > 0:
                types_breakdown.append(f"{u_stats['user_test_files']} Test")
            if u_stats["user_doc_files"] > 0:
                types_breakdown.append(f"{u_stats['user_doc_files']} Docs")
            if u_stats["user_design_files"] > 0:
                types_breakdown.append(f"{u_stats['user_design_files']} Design")
            
            if types_breakdown:
                stats_p.add_run(f"  |  Work: {', '.join(types_breakdown)}")

            # Files Breakdown
            files_list = u_stats["files_list"]
            if files_list:
                exts = [os.path.splitext(f)[1].lower() for f in files_list]
                cnt = Counter(exts)
                sorted_cnt = sorted(cnt.items(), key=lambda x: x[1], reverse=True)
                breakdown_str = ", ".join([f"{count} {ext or 'no-ext'}" for ext, count in sorted_cnt])
                fb_p = doc.add_paragraph()
                fb_p.add_run("File Breakdown: ").bold = True
                fb_p.add_run(breakdown_str)
            
            # Description
            desc = _build_personal_project_description(p_name, p_context, u_stats)
            doc.add_paragraph(desc)
            
            # Specific Skills Used in this project
            # The key in per_contributor_skills matches the contributor_name (normalized)
            pcs = p_context.get("per_contributor_skills", {})
            my_skills = pcs.get(contributor_name, [])
            
            if my_skills:
                s_p = doc.add_paragraph()
                s_p.add_run("Skills Applied: ").italic = True
                s_p.add_run(", ".join(my_skills))
            
            doc.add_paragraph() # spacing
            
    while True:
        try:
            doc.save(docx_path)
            return docx_path
        except PermissionError:
            print(f"\n[!] Could not save to '{docx_path}' because it is open.")
            print("Please close the file and press Enter to retry, or type 'cancel' to stop.")
            if input("> ").strip().lower() == "cancel":
                return None
        except Exception as e:
            print(f"Error saving portfolio: {e}")
            return None