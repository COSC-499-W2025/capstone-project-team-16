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
