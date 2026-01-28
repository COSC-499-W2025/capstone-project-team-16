from typing import List, Dict, Any
from collections import Counter
import os

class Portfolio:
    """
    Represents a professional portfolio for a single contributor.
    """
    def __init__(self, user_name: str, global_skills: List[str]):
        self.user_name = user_name
        self.global_skills = sorted(global_skills)
        self.projects = []

    def add_project(self, name: str, role_description: str, tech_stack: List[str], impact_score: float, duration_days: int,
                    commits: int = 0, insertions: int = 0, deletions: int = 0, files_list: List[str] = None):
        """Adds a project entry to the portfolio."""
        file_breakdown_str = ""
        if files_list:
            exts = [os.path.splitext(f)[1].lower() for f in files_list]
            cnt = Counter(exts)
            sorted_cnt = sorted(cnt.items(), key=lambda x: x[1], reverse=True)
            file_breakdown_str = ", ".join([f"{count} {ext or 'no-ext'}" for ext, count in sorted_cnt])

        self.projects.append({
            "Project Name": name,
            "Role/Contribution": role_description,
            "Tech Stack Used": ", ".join(sorted(tech_stack)),
            "Project Impact Score": round(impact_score, 1),
            "Project Duration": f"{duration_days} days",
            "Commits": commits,
            "Lines Added": insertions,
            "Lines Removed": deletions,
            "File Breakdown": file_breakdown_str
        })

    def to_markdown(self) -> str:
        """Generates a Markdown representation of the portfolio."""
        md = f"# Portfolio: {self.user_name}\n\n"
        
        md += "## Global Skills\n"
        if self.global_skills:
            md += f"**{', '.join(self.global_skills)}**\n\n"
        else:
            md += "No specific skills detected.\n\n"
            
        md += "## Project Showcase\n"
        if not self.projects:
            md += "No projects found.\n"
        
        for p in self.projects:
            md += f"### {p['Project Name']}\n"
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


def create_portfolios(analysis_results: Dict[str, Any]) -> List[Portfolio]:
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
        
        for proj_data in user_projects:
            proj_name = proj_data.get("name")
            proj_details = project_map.get(proj_name)
            
            # Skip if for some reason the project summary is missing
            if not proj_details:
                continue
                
            # Extract user-specific metrics from the project summary
            contribution_pct = proj_details.get("per_contributor_pct", {}).get(user, 0)
            specific_skills = proj_details.get("per_contributor_skills", {}).get(user, [])
            
            p_obj.add_project(
                name=proj_name,
                role_description=f"{contribution_pct:.1f}% of codebase",
                tech_stack=specific_skills,
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
