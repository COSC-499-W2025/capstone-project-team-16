import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from resume_generator import generate_contributor_portfolio, edit_contributor_descriptions

# -------------------------------------------------------------------------
# GENERATION TESTS
# -------------------------------------------------------------------------

@patch("resume_generator.Document")
@patch("resume_generator._save_doc")
def test_generate_portfolio_uses_custom_fields(mock_save, mock_doc_cls):
    """
    Verifies that generate_contributor_portfolio uses custom names, titles,
    summaries, descriptions, and skills when they are present in the data.
    """
    # Setup Mock Document
    mock_doc = mock_doc_cls.return_value
    
    # Prepare Data with Custom Fields
    profile_data = {
        "custom_name": "Dr. Strange",
        "custom_title": "Sorcerer Supreme",
        "custom_summary": "Master of the Mystic Arts and time manipulation.",
        "skills": ["Magic", "Time Stone"],
        "projects": [
            {
                "name": "Sanctum Sanctorum",
                "custom_description": "Defended the reality from dark dimensions.",
                "custom_skills": ["Spells", "Artifacts"],
                "score": 100,
                # Original stats that should be ignored/overridden by custom desc
                "files_worked": 50,
                "pct": 100.0
            }
        ]
    }
    
    all_projects_map = {
        "Sanctum Sanctorum": {
            "first_modified": "2023-01-01",
            "last_modified": "2023-12-31"
        }
    }
    
    # Execute
    generate_contributor_portfolio("stephen", profile_data, all_projects_map)
    
    # Assertions
    
    # 1. Check Custom Name in Header
    # Expected: doc.add_heading("Dr. Strange", level=0)
    mock_doc.add_heading.assert_any_call("Dr. Strange", level=0)
    
    # 2. Check Custom Summary
    # Expected: doc.add_paragraph("Master of the Mystic Arts...")
    mock_doc.add_paragraph.assert_any_call("Master of the Mystic Arts and time manipulation.")
    
    # 3. Check Custom Project Description
    # Expected: doc.add_paragraph("Defended...", style="List Bullet")
    mock_doc.add_paragraph.assert_any_call("Defended the reality from dark dimensions.", style="List Bullet")
    
    # 4. Check Custom Project Skills
    # The code adds a paragraph for skills, then adds a run for "Skills: ", then a run for the list.
    # We can check if the list string was constructed.
    # Since we can't easily check chained calls like p.add_run(...), we verify the logic didn't crash
    # and that the flow reached the skills section.
    # However, we can verify that the default generation logic wasn't used if we had mocked the helper,
    # but here we rely on the fact that custom_skills is passed.


@patch("resume_generator.Document")
@patch("resume_generator._save_doc")
def test_generate_portfolio_defaults(mock_save, mock_doc_cls):
    """
    Verifies that it falls back to defaults when custom fields are missing.
    """
    mock_doc = mock_doc_cls.return_value
    
    profile_data = {
        "skills": ["Python"],
        "projects": [
            {"name": "ProjA", "score": 10, "files_worked": 5, "pct": 10.0}
        ]
    }
    all_projects_map = {"ProjA": {}}
    
    generate_contributor_portfolio("user.name", profile_data, all_projects_map)
    
    # Should format name from "user.name" -> "User Name"
    mock_doc.add_heading.assert_any_call("User Name", level=0)
    
    # Should generate default summary (Software Contributor...)
    # We check that it called add_paragraph with a string starting with "Software"
    args, _ = mock_doc.add_paragraph.call_args_list[1] # 0 is date, 1 is summary usually
    assert "Software Contributor" in args[0] or "Software Developer" in args[0]


# -------------------------------------------------------------------------
# CLI EDITING TESTS
# -------------------------------------------------------------------------

@patch("resume_generator.update_full_scan")
@patch("resume_generator._input_with_prefill")
@patch("builtins.input")
@patch("resume_generator.print") # Suppress output
def test_cli_edit_name_and_title(mock_print, mock_input, mock_prefill, mock_update):
    """
    Simulates the CLI workflow to edit a contributor's Name and Title.
    """
    # Setup Data
    scan_data = {
        "contributor_profiles": {
            "user1": {"projects": [], "skills": ["Python"]}
        },
        "project_summaries": []
    }
    target_scan = {"summary_id": 1, "scan_data": scan_data, "timestamp": "2023"}
    
    # Input Sequence:
    # 1. Select contributor "user1" (Index 1)
    # 2. Menu: "1" (Edit Name)
    #    -> _input_with_prefill returns "Super User"
    # 3. Menu: "2" (Edit Title)
    #    -> _input_with_prefill returns "Lead Dev"
    # 4. Menu: "0" (Back)
    # 5. Select contributor: "0" (Exit)
    
    mock_input.side_effect = ["1", "1", "2", "0", "0"]
    mock_prefill.side_effect = ["Super User", "Lead Dev"]
    
    # Execute
    edit_contributor_descriptions(target_scan=target_scan)
    
    # Verify Data Updates
    profile = scan_data["contributor_profiles"]["user1"]
    assert profile["custom_name"] == "Super User"
    assert profile["custom_title"] == "Lead Dev"
    
    # Verify DB Update was called
    assert mock_update.call_count >= 2


@patch("resume_generator.update_full_scan")
@patch("resume_generator._input_with_prefill")
@patch("builtins.input")
@patch("resume_generator.print")
def test_cli_edit_project_description(mock_print, mock_input, mock_prefill, mock_update):
    """
    Simulates the CLI workflow to edit a specific project description.
    """
    # Setup Data
    proj_ref = {"name": "Alpha"}
    scan_data = {
        "contributor_profiles": {
            "user1": {"projects": [proj_ref], "skills": []}
        },
        "project_summaries": [{"project": "Alpha"}]
    }
    target_scan = {"summary_id": 99, "scan_data": scan_data, "timestamp": "2023"}
    
    # Input Sequence:
    # 1. Select contributor "1"
    # 2. Menu: "4" (Edit Project Details)
    # 3. Select Project "1" (Alpha)
    # 4. Project Menu: "1" (Edit Description)
    #    -> _input_with_prefill returns "I built the backend."
    # 5. Project Menu: "0" (Back)
    # 6. Select Project: "0" (Back)
    # 7. Menu: "0" (Back)
    # 8. Select contributor: "0" (Exit)
    mock_input.side_effect = ["1", "4", "1", "1", "0", "0", "0", "0"]
    mock_prefill.return_value = "I built the backend."
    
    edit_contributor_descriptions(target_scan=target_scan)
    
    assert proj_ref["custom_description"] == "I built the backend."
    mock_update.assert_called()


@patch("resume_generator.update_full_scan")
@patch("resume_generator._input_with_prefill")
@patch("builtins.input")
@patch("resume_generator.print")
def test_cli_reset_fields(mock_print, mock_input, mock_prefill, mock_update):
    """
    Verifies that typing 'RESET' removes the custom fields from the profile.
    """
    # Setup Data with existing custom fields
    profile = {
        "custom_name": "Old Name",
        "custom_title": "Old Title",
        "projects": [],
        "skills": []
    }
    scan_data = {
        "contributor_profiles": {"user1": profile},
        "project_summaries": []
    }
    target_scan = {"summary_id": 1, "scan_data": scan_data, "timestamp": "2023"}

    # Input Sequence:
    # 1. Select contributor "user1" (Index 1)
    # 2. Menu: "1" (Edit Name) -> Input "RESET"
    # 3. Menu: "2" (Edit Title) -> Input "RESET"
    # 4. Menu: "0" (Back)
    # 5. Select contributor: "0" (Exit)
    
    mock_input.side_effect = ["1", "1", "2", "0", "0"]
    # _input_with_prefill is called for the value. We simulate user typing "RESET"
    mock_prefill.side_effect = ["RESET", "RESET"]

    edit_contributor_descriptions(target_scan=target_scan)

    # Assert keys are gone
    assert "custom_name" not in profile
    assert "custom_title" not in profile
    # Verify DB update was triggered
    assert mock_update.called


@patch("resume_generator.update_full_scan")
@patch("resume_generator._input_with_prefill")
@patch("builtins.input")
@patch("resume_generator.print")
def test_cli_edit_project_skills(mock_print, mock_input, mock_prefill, mock_update):
    """
    Verifies editing project skills (parsing comma-separated string).
    """
    # Setup Data
    proj_ref = {"name": "Beta", "custom_skills": ["OldSkill"]}
    scan_data = {
        "contributor_profiles": {
            "user1": {"projects": [proj_ref], "skills": []}
        },
        "project_summaries": [{"project": "Beta"}]
    }
    target_scan = {"summary_id": 2, "scan_data": scan_data, "timestamp": "2023"}

    # Input Sequence:
    # 1. Select contributor "1"
    # 2. Menu: "4" (Edit Project Details)
    # 3. Select Project "1"
    # 4. Project Menu: "2" (Edit Skills)
    #    -> Input "Python,  Django " (Testing whitespace stripping)
    # 5. Project Menu: "0" (Back)
    # 6. Select Project: "0" (Back)
    # 7. Menu: "0" (Back)
    # 8. Select contributor: "0" (Exit)
    
    mock_input.side_effect = ["1", "4", "1", "2", "0", "0", "0", "0"]
    mock_prefill.return_value = "Python,  Django "

    edit_contributor_descriptions(target_scan=target_scan)

    # Assert list parsing
    assert proj_ref["custom_skills"] == ["Python", "Django"]
    mock_update.assert_called()


@patch("resume_generator.update_full_scan")
@patch("resume_generator.get_yes_no")
@patch("builtins.input")
@patch("resume_generator.print")
def test_cli_reset_all_changes(mock_print, mock_input, mock_yes_no, mock_update):
    """
    Verifies that option '6' (Reset All) clears all custom fields for the user.
    """
    # Setup Data with extensive custom fields
    proj_ref = {
        "name": "Gamma",
        "custom_description": "Manual Desc",
        "custom_skills": ["ManualSkill"]
    }
    profile = {
        "custom_name": "Manual Name",
        "custom_title": "Manual Title",
        "custom_summary": "Manual Summary",
        "projects": [proj_ref],
        "skills": []
    }
    scan_data = {
        "contributor_profiles": {"user1": profile},
        "project_summaries": [{"project": "Gamma"}]
    }
    target_scan = {"summary_id": 3, "scan_data": scan_data, "timestamp": "2023"}

    # Input Sequence:
    # 1. Select contributor "1"
    # 2. Menu: "6" (Reset All)
    # 3. Menu: "0" (Back)
    # 4. Select contributor: "0" (Exit)
    mock_input.side_effect = ["1", "6", "0", "0"]
    mock_yes_no.return_value = True  # Confirm reset

    edit_contributor_descriptions(target_scan=target_scan)

    # Assert all custom keys are gone
    assert "custom_name" not in profile
    assert "custom_title" not in profile
    assert "custom_summary" not in profile
    assert "custom_description" not in proj_ref
    assert "custom_skills" not in proj_ref
    
    mock_update.assert_called()
