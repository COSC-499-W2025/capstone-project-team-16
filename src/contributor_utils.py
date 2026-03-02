"""
Helpers for per-contributor scoring + contributor profile building.

- Make contributor logic reusable elsewhere (resume gen / reports)

"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Callable, Dict, List, MutableMapping, Set, Tuple


def normalize_name(name: str) -> str:
    return (name or "").strip().lower()


def get_contrib_pct(contrib_obj: Any) -> float:
    """Safely read contribution_percentage from contributor dict."""
    if not isinstance(contrib_obj, dict):
        return 0.0
    pct = contrib_obj.get("contribution_percentage")
    try:
        return float(pct)
    except Exception:
        return 0.0


def apply_contributor_breakdown(
    *,
    proj_name: str,
    score: float,
    filters: Dict[str, Any],
    project_meta: Dict[str, Any] | None,
    contributor_profiles: MutableMapping[str, Dict[str, Any]],
    detect_activity: Callable[[str, str], str],
    get_skill: Callable[..., str | None],
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, Set[str]]]:
    """
    Builds:
      - per_contributor_scores: name -> adjusted score
      - per_contributor_pct:    name -> contribution %
      - per_contributor_skills: name -> {skills}

    Also updates contributor_profiles[name] with:
      - skills set
      - projects list (with stats)
    """
    per_contributor_scores: Dict[str, float] = {}
    per_contributor_pct: Dict[str, float] = {}
    per_contributor_skills: Dict[str, Set[str]] = defaultdict(set)

    contributors_raw = project_meta.get("contributors", []) if project_meta else []

    ext_map = filters.get("extensions", {})
    lang_map = filters.get("languages", {})
    skill_map = filters.get("skills", {})

    for c in contributors_raw:
        # contributor objects are usually dicts
        if isinstance(c, dict):
            name = c.get("name") or c.get("email") or ""
            key = normalize_name(name)
            if not key:
                continue

            pct = get_contrib_pct(c)
            per_contributor_pct[key] = pct
            per_contributor_scores[key] = score * (pct / 100.0)

            # skills from loc_by_type
            loc_map = c.get("loc_by_type", {}) or {}
            for ext in loc_map:
                s = get_skill(ext=ext, skill_map=skill_map, ext_map=lang_map)
                if s:
                    contributor_profiles[key]["skills"].add(s)
                    per_contributor_skills[key].add(s)

            # detailed file stats (for resume generator / summary)
            files_edited: List[str] = c.get("files_edited", []) or []
            user_code = user_test = user_doc = user_design = 0

            for fpath in files_edited:
                _, ext = os.path.splitext(fpath)
                ext = ext.lower()
                cat = ext_map.get(ext, "uncategorized")
                act = detect_activity(cat, fpath)

                if act == "code":
                    user_code += 1
                elif act == "test":
                    user_test += 1
                elif act == "documentation":
                    user_doc += 1
                elif act == "design":
                    user_design += 1

            contributor_profiles[key]["projects"].append(
                {
                    "name": proj_name,
                    "pct": pct,
                    "score": score * (pct / 100.0),
                    "files_worked": len(files_edited),
                    "files_list": files_edited,
                    "user_code_files": user_code,
                    "user_test_files": user_test,
                    "user_doc_files": user_doc,
                    "user_design_files": user_design,
                    "insertions": c.get("insertions", 0),
                    "deletions": c.get("deletions", 0),
                    "commit_count": c.get("commit_count", 0),
                }
            )

        # sometimes contributors list can contain strings
        elif c:
            key = normalize_name(str(c))
            if key:
                per_contributor_pct[key] = 0.0
                per_contributor_scores[key] = 0.0

    return per_contributor_scores, per_contributor_pct, per_contributor_skills
