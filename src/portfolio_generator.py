from typing import List, Dict, Any
from collections import Counter
import os
import base64
import mimetypes

from db import update_full_scan
from print_utils import _center_text, is_noise
from file_parser import OUTPUT_DIR
from print_utils import _input_with_prefill

class Portfolio:
    """
    Represents a professional portfolio for a single contributor.
    """
    def __init__(self, user_name: str, global_skills: List[str], skills_progression: List[Dict[str, Any]] = None):
        self.user_name = user_name
        self.global_skills = sorted(global_skills)
        self.skills_progression = skills_progression or []
        self.projects = []

    def add_project(self, name: str, project_description: str, role_description: str, tech_stack: List[str], impact_score: float, duration_days: int,
                    commits: int = 0, insertions: int = 0, deletions: int = 0, files_list: List[str] = None, thumbnail: str = None):
        """Adds a project entry to the portfolio."""
        file_breakdown_str = ""
        if files_list:
            exts = [os.path.splitext(f)[1].lower() for f in files_list]
            cnt = Counter(exts)
            sorted_cnt = sorted(cnt.items(), key=lambda x: x[1], reverse=True)
            file_breakdown_str = ", ".join([f"{count} {ext or 'no-ext'}" for ext, count in sorted_cnt])

        self.projects.append({
            "Project Name": name,
            "Description": project_description,
            "Role/Contribution": role_description,
            "Tech Stack Used": ", ".join(sorted(tech_stack)),
            "Project Impact Score": round(impact_score, 1),
            "Project Duration": f"{duration_days} days",
            "Commits": commits,
            "Lines Added": insertions,
            "Lines Removed": deletions,
            "File Breakdown": file_breakdown_str,
            "Thumbnail": thumbnail
        })

    def to_markdown(self) -> str:
        """Generates a Markdown representation of the portfolio."""
        md = f"# Portfolio: {self.user_name}\n\n"
        
        md += "## Global Skills\n"
        if self.global_skills:
            md += f"**{', '.join(self.global_skills)}**\n\n"
        else:
            md += "No specific skills detected.\n\n"
            
        if self.skills_progression:
            md += "## Skills Progression & Depth\n\n"
            md += "| Skill | First Used | Last Used | Projects | Lines Added | Lines Removed |\n"
            md += "|-------|------------|-----------|----------|-------------|---------------|\n"
            for sp in self.skills_progression:
                f_used = sp.get('first_used') or 'Unknown'
                l_used = sp.get('last_used') or 'Unknown'
                ins_val = sp.get('insertions', 0)
                del_val = sp.get('deletions', 0)
                ins_str = f"+{ins_val}" if ins_val > 0 else "-"
                del_str = f"-{del_val}" if del_val > 0 else "-"
                md += f"| **{sp.get('skill', 'Unknown')}** | {f_used} | {l_used} | {sp.get('projects_count', 0)} | {ins_str} | {del_str} |\n"
            md += "\n"
            
        md += "## Project Showcase\n"
        if not self.projects:
            md += "No projects found.\n"
        
        for p in self.projects:
            md += f"### {p['Project Name']}\n"
            
            if p.get("Thumbnail"):
                thumb_path = os.path.join(OUTPUT_DIR, "thumbnails", p["Thumbnail"])
                if os.path.exists(thumb_path):
                    mime_type, _ = mimetypes.guess_type(thumb_path)
                    mime_type = mime_type or "image/png"
                    with open(thumb_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    md += f'<img src="data:{mime_type};base64,{b64}" alt="{p["Project Name"]} thumbnail" width="500"/>\n\n'

            if p.get("Description"):
                md += f"- **Description:** {p['Description']}\n"
            md += f"- **Role/Contribution:** {p['Role/Contribution']}\n"
            md += f"- **Tech Stack:** {p['Tech Stack Used']}\n"
            md += f"- **Impact Score:** {p['Project Impact Score']}\n"
            md += f"- **Duration:** {p['Project Duration']}\n"
            
            if p['Commits'] > 0:
                md += f"- **Commits:** {p['Commits']}\n"
            if p['Lines Added'] > 0 or p['Lines Removed'] > 0:
                md += f"- **Lines:** +{p['Lines Added']} / -{p['Lines Removed']}\n"
            if p['File Breakdown']:
                md += f"- **File Breakdown:** {p['File Breakdown']}\n"
            
            md += "\n"
            
        return md

    def __repr__(self):
        return f"<Portfolio: {self.user_name} ({len(self.projects)} projects)>"


def _get_effective_description(project_data: Dict[str, Any]) -> str:
    """
    Returns the effective portfolio description.
    Uses the custom description if available, otherwise generates a default based on stats.
    """
    custom = project_data.get("custom_portfolio_description")
    if custom:
        return custom
    
    pct = project_data.get("pct", 0.0)
    return f"{pct:.1f}% of codebase"


def _get_default_tech_stack(proj_details: Dict[str, Any], user: str) -> List[str]:
    """
    Generates the default tech stack by combining contributor skills
    with project-wide languages and frameworks.
    """

    stack_set = set()
    # Filter out noise often detected by language classifiers
    IGNORED_SKILLS = {"Plain Text", "Text", "Unknown"}

    # 2. Project languages
    p_langs = proj_details.get("languages", "")
    if p_langs and p_langs != "Unknown":
        for l in p_langs.split(","):
            cleaned = l.strip()
            if cleaned and cleaned not in IGNORED_SKILLS:
                stack_set.add(cleaned)

    # 3. Project frameworks
    p_fw = proj_details.get("frameworks", "")
    if p_fw and p_fw != "NA":
        for f in p_fw.split(","):
            if f.strip():
                stack_set.add(f.strip())

    return sorted(list(stack_set))


def create_portfolios(analysis_results: Dict[str, Any], use_custom_fields: bool = True) -> List[Portfolio]:
    """
    Factory function that takes the raw analysis results and returns a list 
    of Portfolio objects, one for each contributor found.
    """
    # Extract the raw data structures from alternative_analysis.py output
    profiles = analysis_results.get("contributor_profiles", {})
    summaries = analysis_results.get("project_summaries", [])
    
    # Create a lookup map for project details for faster access
    project_map = {p["project"]: p for p in summaries}
    
    portfolios = []
    
    for user, profile_data in profiles.items():
        # Initialize the portfolio object
        p_obj = Portfolio(user, profile_data.get("skills", []))
        
        # Get the list of projects this user is associated with
        user_projects = profile_data.get("projects", [])
        
        # Filter for showcase if any are flagged. If none flagged, use all.
        if use_custom_fields:
            showcase_projects = [p for p in user_projects if p.get("is_showcase")]
            projects_to_process = showcase_projects if showcase_projects else user_projects
        else:
            projects_to_process = user_projects

        for proj_data in projects_to_process:
            proj_name = proj_data.get("name")
            proj_details = project_map.get(proj_name)
            
            # Skip if for some reason the project summary is missing
            if not proj_details:
                continue
                
            # Extract user-specific metrics from the project summary
            contribution_pct = proj_details.get("per_contributor_pct", {}).get(user, 0)
            
            # 1. Project Description (General)
            proj_desc = ""
            if use_custom_fields:
                proj_desc = proj_data.get("custom_portfolio_project_description", "")

            # 2. Role Description (Contribution)
            if use_custom_fields:
                role_desc = _get_effective_description(proj_data)
            else:
                role_desc = f"{contribution_pct:.1f}% of codebase"

            # 3. Tech Stack
            tech_stack = None
            if use_custom_fields:
                tech_stack = proj_data.get("custom_portfolio_tech_stack")
            
            if tech_stack is None:
                tech_stack = _get_default_tech_stack(proj_details, user)

            p_obj.add_project(
                name=proj_name,
                project_description=proj_desc,
                role_description=role_desc,
                tech_stack=tech_stack,
                impact_score=proj_details.get("score", 0),
                duration_days=proj_details.get("duration_days", 0),
                commits=proj_data.get("commit_count", 0),
                insertions=proj_data.get("insertions", 0),
                deletions=proj_data.get("deletions", 0),
                files_list=proj_data.get("files_list", [])
            )
            
        # Sort the projects in the portfolio by Impact Score (highest first)
        p_obj.projects.sort(key=lambda x: x["Project Impact Score"], reverse=True)
        
        portfolios.append(p_obj)
        
    return portfolios


def generate_and_save_portfolio(data, user, use_custom_fields=True):
    """Generates and saves the Markdown portfolio for a user."""
    portfolios = create_portfolios(data, use_custom_fields=use_custom_fields)
    target_portfolio = next((p for p in portfolios if p.user_name == user), None)

    if target_portfolio:
        portfolio_dir = os.path.join(OUTPUT_DIR, "portfolios")
        os.makedirs(portfolio_dir, exist_ok=True)
        
        safe_name = "".join(c for c in user if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        filename = f"Portfolio_{safe_name}.md"
        out_path = os.path.join(portfolio_dir, filename)
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(target_portfolio.to_markdown())
        return out_path
    return None


def _edit_portfolio_details(user, user_projects, summary_id, data):
    """
    Helper to handle the UI loop for editing all portfolio details for a user.
    """
    # Create lookup for defaults
    summaries = data.get("project_summaries", [])
    project_map = {p["project"]: p for p in summaries}

    while True:
        print()
        print(_center_text(f"--- Edit Portfolio Details: {user} ---"))
        for i, p in enumerate(user_projects, 1):
            p_name = p.get("name", "Unknown")
            # Show a marker if any custom portfolio field is set
            has_custom = " *" if any(k.startswith("custom_portfolio_") for k in p.keys()) else ""
            print(_center_text(f"{i}. {p_name}{has_custom}"))

        print()
        print(_center_text("Select project to edit (0 to back)."))
        
        sel = input(_center_text("Select: ")).strip()
        
        if sel == "0":
            break
        
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(user_projects):
                target_p = user_projects[idx]
                
                while True:
                    p_name = target_p.get("name")
                    print()
                    print(_center_text(f"--- Editing: {p_name} ---"))
                    print(_center_text("1. Description (General)"))
                    print(_center_text("2. Role / Contribution"))
                    print(_center_text("3. Tech Stack"))
                    print(_center_text("0. Back to Project List"))
                    
                    sub = input(_center_text("Choose option: ")).strip()
                    
                    if sub == "0":
                        break
                    
                    elif sub == "1":
                        curr = target_p.get("custom_portfolio_project_description", "")
                        print(_center_text("Edit Project Description (General):"))
                        val = _input_with_prefill("Value: ", curr).strip()
                        if val: target_p["custom_portfolio_project_description"] = val
                        else: target_p.pop("custom_portfolio_project_description", None)

                    elif sub == "2":
                        curr = _get_effective_description(target_p)
                        print(_center_text("Edit Role/Contribution:"))
                        val = _input_with_prefill("Value: ", curr).strip()
                        if val: target_p["custom_portfolio_description"] = val
                        else: target_p.pop("custom_portfolio_description", None)

                    elif sub == "3":
                        # Tech stack is a list, input as comma-separated
                        curr_list = target_p.get("custom_portfolio_tech_stack")
                        
                        if curr_list is None:
                            p_name = target_p.get("name")
                            proj_details = project_map.get(p_name, {})
                            curr_list = _get_default_tech_stack(proj_details, user)

                        curr_str = ", ".join(curr_list) if curr_list else ""
                        print(_center_text("Edit Tech Stack (comma separated):"))
                        val = _input_with_prefill("Value: ", curr_str).strip()
                        if val:
                            target_p["custom_portfolio_tech_stack"] = [s.strip() for s in val.split(",") if s.strip()]
                        else:
                            target_p.pop("custom_portfolio_tech_stack", None)

                    # Save after every sub-edit
                    update_full_scan(summary_id, data)
                    print(_center_text("Saved."))

            else:
                print(_center_text("Invalid index."))


def manage_portfolio_showcase(target_scan=None):
    """
    Allows the user to select projects for the portfolio showcase and edit descriptions.
    """
    if target_scan:
        scan = target_scan
        summary_id = target_scan["summary_id"]
        data = target_scan["scan_data"]
    else:
        return

    profiles = data.get("contributor_profiles", {})
    contributors = sorted([c for c in profiles.keys() if not is_noise(c)])

    if not contributors:
        print(_center_text("No contributors found."))
        return

    while True:
        print()
        print(_center_text("Select contributor to customize portfolio:"))
        for i, c in enumerate(contributors, 1):
            print(_center_text(f"{i}. {c}"))

        sel = input(_center_text("Enter number (0 to back): ")).strip()
        if not sel.isdigit():
            continue
        
        c_idx = int(sel) - 1
        if c_idx == -1:
            break
        if c_idx < 0 or c_idx >= len(contributors):
            continue

        user = contributors[c_idx]
        profile = profiles[user]
        user_projects = profile.get("projects", [])

        while True:
            print()
            print(_center_text(f"--- Portfolio Showcase: {user} ---"))
            print(_center_text("1. Select Projects for Showcase"))
            print(_center_text("2. Edit Portfolio Details"))
            print(_center_text("3. Regenerate Portfolio"))
            print(_center_text("0. Back to Contributor List"))
            
            choice = input(_center_text("Choose option: ")).strip()
            
            if choice == "0":
                break
            
            elif choice == "1":
                while True:
                    print()
                    print(_center_text(f"--- Select Projects: {user} ---"))
                    print(_center_text("(Projects marked [x] will appear in the portfolio)"))
                    for i, p in enumerate(user_projects, 1):
                        is_showcase = p.get("is_showcase", False)
                        mark = "[x]" if is_showcase else "[ ]"
                        p_name = p.get("name", "Unknown")
                        print(_center_text(f"{i}. {mark} {p_name}"))

                    print()
                    print(_center_text("Type number to toggle selection (0 to back)."))
                    
                    sel = input(_center_text("Select: ")).strip()
                    
                    if sel == "0":
                        break
                    
                    if sel.isdigit():
                        idx = int(sel) - 1
                        if 0 <= idx < len(user_projects):
                            target_p = user_projects[idx]
                            target_p["is_showcase"] = not target_p.get("is_showcase", False)
                            update_full_scan(summary_id, data)
                        else:
                            print(_center_text("Invalid index."))

            elif choice == "2":
                _edit_portfolio_details(user, user_projects, summary_id, data)

            elif choice == "3":
                out = generate_and_save_portfolio(data, user, use_custom_fields=True)
                if out:
                    print(_center_text(f"Regenerated portfolio: {out}"))
                else:
                    print(_center_text("Error generating portfolio."))
                input(_center_text("Press Enter to continue..."))


def generate_portfolio_markdown(artifact_data: Dict[str, Any]) -> str:
    """
    Generates Markdown content from an API portfolio artifact data structure.
    This allows the API to use the same formatting logic as the local generator.
    """
    user_name = artifact_data.get("contributor_id", "User")
    global_skills = artifact_data.get("global_skills", [])
    skills_progression = artifact_data.get("skills_progression", [])
    
    # Create a Portfolio object to reuse its to_markdown method
    p_obj = Portfolio(user_name, global_skills, skills_progression)
    
    for item in artifact_data.get("items", []):
        # Reconstruct file breakdown string if needed
        fb_str = ""
        fb = item.get("file_breakdown")
        if isinstance(fb, dict):
            parts = [f"{count} {ext}" for ext, count in sorted(fb.items(), key=lambda x: x[1], reverse=True)]
            fb_str = ", ".join(parts)
        elif isinstance(fb, str):
            fb_str = fb
            
        p_obj.projects.append({
            "Project Name": item.get("project_name", "Unknown"),
            "Description": item.get("project_description"),
            "Role/Contribution": item.get("role_description") or item.get("contribution_display"),
            "Tech Stack Used": ", ".join(item.get("tech_stack", [])),
            "Project Impact Score": item.get("impact_score", 0),
            "Project Duration": f"{item.get('duration_days', 0)} days",
            "Commits": item.get("commits", 0),
            "Lines Added": item.get("lines_added", 0),
            "Lines Removed": item.get("lines_removed", 0),
            "File Breakdown": fb_str,
            "Thumbnail": item.get("thumbnail")
        })
        
    return p_obj.to_markdown()
