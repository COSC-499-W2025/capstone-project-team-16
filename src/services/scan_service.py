"""
Service helpers for running scans without CLI prompts.
"""

from typing import Any, Mapping, Optional

from alternative_analysis import analyze_projects
from db import save_full_scan
from metadata_extractor import base_extraction, detailed_extraction, load_filters


def analyze_scan(
    file_list: list,
    analysis_mode: str,
    advanced_options: Optional[Mapping[str, Any]] = None,
) -> Optional[Mapping[str, Any]]:
    """
    Run the scan pipeline and return analysis results without persisting.
    """
    if not file_list:
        return None

    filters = load_filters()
    scraped_data = base_extraction(file_list, filters)

    advanced_options = dict(advanced_options or {})
    detailed_data = None
    if analysis_mode and analysis_mode.lower() == "advanced":
        detailed_data = detailed_extraction(scraped_data, advanced_options, filters)

    return analyze_projects(scraped_data, filters, advanced_options, detailed_data)


def save_scan(
    analysis_results: Mapping[str, Any],
    analysis_mode: str,
    consent: bool,
) -> None:
    """
    Persist the analysis results to the DB.
    """
    save_full_scan(analysis_results, analysis_mode, consent)


def run_scan(
    file_list: list,
    analysis_mode: str,
    advanced_options: Optional[Mapping[str, Any]] = None,
    consent: bool = False,
    persist: bool = True,
) -> Optional[Mapping[str, Any]]:
    """
    Run a scan and optionally persist it.
    """
    results = analyze_scan(file_list, analysis_mode, advanced_options)
    if results and persist:
        save_scan(results, analysis_mode, consent)
    return results


def merge_scans(existing_data: Mapping[str, Any], new_data: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Merges new scan results into an existing scan dataset.
    Used for incremental updates to a portfolio.
    """
    merged = dict(existing_data)  # Shallow copy

    # 1. Merge Project Summaries (Append)
    existing_projects = merged.get("project_summaries", [])
    new_projects = new_data.get("project_summaries", [])
    merged["project_summaries"] = existing_projects + new_projects

    # 2. Merge Resume Summaries (Append)
    merged["resume_summaries"] = merged.get("resume_summaries", []) + new_data.get("resume_summaries", [])

    # 3. Merge Skills Chronological (Append)
    merged["skills_chronological"] = merged.get("skills_chronological", []) + new_data.get("skills_chronological", [])

    # 4. Merge Projects Chronological (Append)
    merged["projects_chronological"] = merged.get("projects_chronological", []) + new_data.get("projects_chronological", [])

    # 5. Merge Contributor Profiles (Union Skills)
    existing_profiles = dict(merged.get("contributor_profiles", {}))
    new_profiles = new_data.get("contributor_profiles", {})

    for user, info in new_profiles.items():
        if user in existing_profiles:
            # Merge skills for existing user
            old_skills = set(existing_profiles[user].get("skills", []))
            new_skills = set(info.get("skills", []))
            existing_profiles[user]["skills"] = list(old_skills.union(new_skills))
            
            # Merge projects list if present
            old_projs = existing_profiles[user].get("projects", [])
            new_projs = info.get("projects", [])
            existing_profiles[user]["projects"] = old_projs + new_projs
        else:
            # New user
            existing_profiles[user] = info
    
    merged["contributor_profiles"] = existing_profiles

    # 6. Merge Source Hashes
    existing_hashes = set(merged.get("source_hashes", []))
    existing_hashes.update(new_data.get("source_hashes", []))
    merged["source_hashes"] = list(existing_hashes)
    
    return merged
