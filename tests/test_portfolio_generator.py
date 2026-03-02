import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from portfolio_generator import (
    Portfolio, 
    create_portfolios, 
    _get_default_tech_stack, 
    _get_effective_description
)

def test_portfolio_initialization():
    """Test that a Portfolio object initializes correctly."""
    p = Portfolio("test_user", ["Python", "Java"])
    assert p.user_name == "test_user"
    assert p.global_skills == ["Java", "Python"]  # Should be sorted
    assert p.projects == []

def test_add_project():
    """Test adding a project to the portfolio."""
    p = Portfolio("test_user", [])
    p.add_project(
        name="Proj1",
        project_description="A cool project",
        role_description="Lead Dev",
        tech_stack=["Python", "Flask"],
        impact_score=100.5,
        duration_days=10,
        commits=5,
        insertions=50,
        deletions=20,
        files_list=["main.py", "utils.py", "README.md"]
    )
    
    assert len(p.projects) == 1
    proj = p.projects[0]
    assert proj["Project Name"] == "Proj1"
    assert proj["Description"] == "A cool project"
    assert proj["Role/Contribution"] == "Lead Dev"
    assert proj["Tech Stack Used"] == "Flask, Python"  # Sorted
    assert proj["Project Impact Score"] == 100.5
    assert "2 .py" in proj["File Breakdown"]

def test_get_default_tech_stack_filters_noise():
    """Test that 'Plain Text' and 'Text' are filtered out of the tech stack."""
    proj_details = {
        
        "languages": "Java, Plain Text, Text, Go",
        "frameworks": "Spring"
    }
    
    stack = _get_default_tech_stack(proj_details, "user")
    

    assert "Java" in stack
    assert "Go" in stack
    assert "Spring" in stack
    assert "Plain Text" not in stack
    assert "Text" not in stack

def test_create_portfolios_logic():
    """Test the factory function with both custom fields enabled and disabled."""
    
    # Mock Analysis Results
    analysis_results = {
        "contributor_profiles": {
            "user@example.com": {
                "skills": ["Python"],
                "projects": [
                    {
                        "name": "ProjectA",
                        "is_showcase": True,
                        "custom_portfolio_project_description": "Custom Project Desc",
                        "custom_portfolio_description": "Custom Role Desc",
                        "custom_portfolio_tech_stack": ["CustomLang"]
                    },
                    {
                        "name": "ProjectB",
                        "is_showcase": False
                    }
                ]
            }
        },
        "project_summaries": [
            {
                "project": "ProjectA",
                "per_contributor_pct": {"user@example.com": 50.0},
                "languages": "Python",
                "score": 100,
                "duration_days": 5
            },
            {
                "project": "ProjectB",
                "per_contributor_pct": {"user@example.com": 10.0},
                "languages": "Java",
                "score": 50,
                "duration_days": 2
            }
        ]
    }

    # 1. Test with use_custom_fields=True
    # Should only include showcase projects (ProjectA) and use custom descriptions
    portfolios_custom = create_portfolios(analysis_results, use_custom_fields=True)
    assert len(portfolios_custom) == 1
    p_custom = portfolios_custom[0]
    
    assert len(p_custom.projects) == 1
    assert p_custom.projects[0]["Project Name"] == "ProjectA"
    assert p_custom.projects[0]["Description"] == "Custom Project Desc"
    assert p_custom.projects[0]["Role/Contribution"] == "Custom Role Desc"
    assert p_custom.projects[0]["Tech Stack Used"] == "CustomLang"

    # 2. Test with use_custom_fields=False
    # Should include ALL projects (ignoring showcase flag) and use default stats
    portfolios_default = create_portfolios(analysis_results, use_custom_fields=False)
    assert len(portfolios_default) == 1
    p_default = portfolios_default[0]
    
    assert len(p_default.projects) == 2
    
    # Check ProjectA defaults
    proj_a = next(p for p in p_default.projects if p["Project Name"] == "ProjectA")
    assert proj_a["Description"] == ""
    assert "50.0%" in proj_a["Role/Contribution"]
    assert "Python" in proj_a["Tech Stack Used"]
