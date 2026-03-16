"""
FastAPI application for Skill Scope milestone API endpoints.

This module keeps the existing scan endpoints while adding project/resume/portfolio
endpoints for milestone requirements.
"""

import json
import logging
import os
import tempfile
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Path, Query, Request, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from api_store import (
    create_portfolio_artifact,
    create_resume_artifact,
    get_portfolio_artifact,
    get_privacy_settings,
    get_project_customization,
    get_resume_artifact,
    set_privacy_settings,
    update_portfolio_artifact,
    update_resume_artifact,
    upsert_project_customization,
)
from db import (
    delete_full_scan_by_id,
    get_full_scan_by_id,
    list_full_scans,
    save_full_scan,
    scan_exists,
    update_full_scan,
)
from resume_generator import render_resume_artifact, _build_personal_project_description, _fmt_date

try:
    from portfolio_generator import generate_portfolio_markdown
except ImportError:
    generate_portfolio_markdown = None

logger = logging.getLogger(__name__)

THUMBNAILS_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "thumbnails")
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

VALID_ANALYSIS_MODES = {"basic", "advanced"}
VALID_ADVANCED_OPTION_KEYS = {
    "programming_scan",
    "framework_scan",
    "skills_gen",
    "resume_gen",
}


class PrivacyConsentPayload(BaseModel):
    consent: bool
    external_services_allowed: bool = False
    notes: str = ""


class ProjectEditPayload(BaseModel):
    ranking: Optional[int] = None
    chronology_correction: Optional[Dict[str, Any]] = None
    comparison_attributes: Optional[Dict[str, Any]] = None
    highlighted_skills: Optional[List[str]] = None
    selected_for_showcase: Optional[bool] = None
    role: Optional[str] = None
    evidence_of_success: Optional[Any] = None
    thumbnail: Optional[str] = None
    portfolio_showcase_text: Optional[str] = None
    resume_wording: Optional[str] = None
    custom_portfolio_project_description: Optional[str] = None
    custom_portfolio_description: Optional[str] = None
    custom_portfolio_tech_stack: Optional[List[str]] = None


class ContributorProjectEdit(BaseModel):
    custom_description: Optional[str] = None
    custom_skills: Optional[List[str]] = None
    reset_custom_skills: bool = False
    custom_portfolio_description: Optional[str] = None
    custom_portfolio_tech_stack: Optional[List[str]] = None
    reset_custom_portfolio_tech_stack: bool = False
    custom_portfolio_project_description: Optional[str] = None


class ContributorProfileEditPayload(BaseModel):
    custom_name: Optional[str] = None
    custom_title: Optional[str] = None
    custom_summary: Optional[str] = None
    project_updates: Optional[Dict[str, ContributorProjectEdit]] = None
    reset_profile: bool = False


class MergeContributorsPayload(BaseModel):
    primary_contributor: str
    contributors_to_merge: List[str]


class ResumeGeneratePayload(BaseModel):
    scan_id: Optional[int] = None
    contributor_id: Optional[str] = None
    project_ids: List[str] = Field(default_factory=list)
    title: str = "Generated Resume"
    selected_project_ids: List[str] = Field(default_factory=list)
    project_order: List[str] = Field(default_factory=list)


class ResumeEditPayload(BaseModel):
    user_name: Optional[str] = None
    user_title: Optional[str] = None
    user_summary: Optional[str] = None
    title: Optional[str] = None
    project_order: Optional[List[str]] = None
    selected_project_ids: Optional[List[str]] = None
    items: Optional[List[Dict[str, Any]]] = None
    project_wording_edits: Optional[Dict[str, str]] = None


class PortfolioGeneratePayload(BaseModel):
    scan_id: Optional[int] = None
    contributor_id: Optional[str] = None
    project_ids: List[str] = Field(default_factory=list)
    title: str = "Generated Portfolio"
    selected_project_ids: List[str] = Field(default_factory=list)
    project_order: List[str] = Field(default_factory=list)


class PortfolioEditPayload(BaseModel):
    title: Optional[str] = None
    project_order: Optional[List[str]] = None
    selected_project_ids: Optional[List[str]] = None
    items: Optional[List[Dict[str, Any]]] = None
    project_edits: Optional[Dict[str, ProjectEditPayload]] = None


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return default


def _parse_analysis_mode(value: Any) -> Optional[str]:
    if value is None:
        return "basic"
    if not isinstance(value, str):
        return None
    parsed = value.strip().lower()
    if not parsed:
        return "basic"
    if parsed not in VALID_ANALYSIS_MODES:
        return None
    return parsed


def _parse_advanced_options(value: Any) -> Tuple[Optional[Dict[str, bool]], Optional[str]]:
    if value is None or value == "":
        return {}, None
    if isinstance(value, dict):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None, "advanced_options must be valid JSON"
        if not isinstance(parsed, dict):
            return None, "advanced_options must be a JSON object"
    else:
        return None, "advanced_options must be an object"

    normalized: Dict[str, bool] = {}
    for key, option_value in parsed.items():
        if key not in VALID_ADVANCED_OPTION_KEYS:
            return None, f"unsupported advanced option: {key}"
        if not isinstance(option_value, bool):
            return None, f"advanced option '{key}' must be boolean"
        normalized[key] = option_value

    return normalized, None


def _json_safe(payload: Any) -> Any:
    return json.loads(json.dumps(payload, default=str))


def _model_dump(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _model_dump_exclude_none(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


def _check_file_validity(zip_path: str):
    from file_parser import check_file_validity

    return check_file_validity(zip_path)


def _analyze_scan(file_list: list, analysis_mode: str, advanced_options: Optional[Dict[str, bool]]):
    from services.scan_service import analyze_scan

    return analyze_scan(file_list, analysis_mode, advanced_options)


def _merge_scans(existing_data: Dict[str, Any], new_data: Dict[str, Any]):
    from services.scan_service import merge_scans

    return merge_scans(existing_data, new_data)


def _split_project_id(project_id: str) -> Tuple[int, int]:
    try:
        scan_str, project_idx_str = project_id.split(":", 1)
        return int(scan_str), int(project_idx_str)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="project id must be in '<scan_id>:<index>' format") from exc


def _project_id(scan_id: int, project_index: int) -> str:
    return f"{scan_id}:{project_index}"


def _apply_project_customization(project_record: Dict[str, Any], customization: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(project_record)
    if customization:
        custom = dict(customization)
        custom.pop("updated_at", None)
        merged["customization"] = custom
        for key in (
            "ranking",
            "chronology_correction",
            "comparison_attributes",
            "highlighted_skills",
            "selected_for_showcase",
            "role",
            "evidence_of_success",
            "thumbnail",
            "portfolio_showcase_text",
            "resume_wording",
            "custom_portfolio_project_description",
            "custom_portfolio_description",
            "custom_portfolio_tech_stack",
        ):
            if key in custom:
                merged[key] = custom[key]
    else:
        merged["customization"] = {}
    return merged


def _build_project_record(scan_id: int, project_index: int, project: Dict[str, Any]) -> Dict[str, Any]:
    base = {
        "project_id": _project_id(scan_id, project_index),
        "scan_id": scan_id,
        "project_index": project_index,
        "project_name": project.get("project") or project.get("name") or f"Project {project_index + 1}",
        "data": project,
        "skills": project.get("skills", []),
        "frameworks": project.get("frameworks", []),
        "languages": project.get("languages", []),
        "score": project.get("score"),
        "project_type": project.get("project_type"),
    }
    return _apply_project_customization(base, get_project_customization(base["project_id"]))


def _iter_projects(scan_id: Optional[int] = None) -> List[Dict[str, Any]]:
    project_rows: List[Dict[str, Any]] = []
    if scan_id is not None:
        scan = get_full_scan_by_id(scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="scan not found")
        scans = [scan]
    else:
        scan_meta = list_full_scans()
        scans = []
        for meta in scan_meta:
            full = get_full_scan_by_id(meta["summary_id"])
            if full:
                scans.append(full)

    for scan in scans:
        sid = int(scan["summary_id"])
        project_summaries = (scan.get("scan_data") or {}).get("project_summaries", [])
        for idx, project in enumerate(project_summaries):
            if isinstance(project, dict):
                project_rows.append(_build_project_record(sid, idx, project))
    return project_rows


def _get_project_by_id(project_id: str) -> Dict[str, Any]:
    scan_id, idx = _split_project_id(project_id)
    scan = get_full_scan_by_id(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="scan not found")
    project_summaries = (scan.get("scan_data") or {}).get("project_summaries", [])
    if idx < 0 or idx >= len(project_summaries):
        raise HTTPException(status_code=404, detail="project not found")
    project = project_summaries[idx]
    if not isinstance(project, dict):
        raise HTTPException(status_code=404, detail="project not found")
    return _build_project_record(scan_id, idx, project)


def _project_sort_key(project: Dict[str, Any]) -> Tuple[int, Any, str]:
    custom_rank = project.get("ranking")
    if isinstance(custom_rank, int):
        # Custom rank (Group 2). Higher rank (1) > Lower rank (2) via negation (-1 > -2)
        return (2, -custom_rank, project["project_id"])
    
    # Default (Group 1). Sort by date descending (Newest first).
    data = project.get("data", {})
    last_mod = data.get("last_modified")
    date_str = str(last_mod) if last_mod is not None else ""
    return (1, date_str, project["project_id"])


def _project_to_resume_item(project: Dict[str, Any], user_stats: Optional[Dict[str, Any]] = None, contributor_id: Optional[str] = None) -> Dict[str, Any]:
    custom_text = project.get("resume_wording")
    project_name = project.get("project_name", "Unnamed Project")
    role = project.get("role")
    evidence = project.get("evidence_of_success")
    
    # Determine skills source
    skills_raw = None
    
    # 1. Contributor custom skills (Highest priority for contributor resumes)
    if user_stats and user_stats.get("custom_skills"):
        skills_raw = user_stats.get("custom_skills")

    # 2. Custom overrides (highlighted_skills) - Project level
    if not skills_raw:
        skills_raw = project.get("highlighted_skills")
    
    # 3. Contributor-specific skills (auto-detected)
    if not skills_raw and contributor_id:
        pcs = project.get("data", {}).get("per_contributor_skills", {})
        skills_raw = pcs.get(contributor_id)
    
    # 4. Fallback to project-wide skills
    if not skills_raw:
        skills_raw = project.get("skills") or []

    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    else:
        skills = skills_raw

    # Format dates
    data = project.get("data", {})
    start = data.get("first_modified")
    end = data.get("last_modified")
    date_str = ""
    if start and end:
        date_str = f" ({_fmt_date(start)} – {_fmt_date(end)})"

    if custom_text:
        text = custom_text
    elif user_stats:
        # Check for custom description in user_stats (Contributor specific edit)
        if user_stats.get("custom_description"):
            text = user_stats.get("custom_description")
        else:
            # Use rich description logic from resume_generator
            project_context = {
                "languages": data.get("languages", "Unknown"),
                "skills": data.get("skills", "NA"),
                "frameworks": data.get("frameworks", "None"),
                "duration_days": data.get("duration_days", 0)
            }
            text = _build_personal_project_description(project_name, project_context, user_stats)
    else:
        parts = [f"Contributed to {project_name}"]
        if role:
            parts.append(f"as {role}")
        if skills:
            parts.append(f"highlighting {', '.join(skills[:5])}")
        if evidence:
            parts.append(f"with evidence of success: {evidence}")
        text = "; ".join(parts) + "."
        
    return {
        "project_id": project["project_id"],
        "project_name": project_name,
        "text": text,
        "role": role,
        "evidence_of_success": evidence,
        "date_str": date_str,
        "skills": skills,
    }


def _project_to_portfolio_item(project: Dict[str, Any], contributor_id: Optional[str] = None, user_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    project_name = project.get("project_name", "Unnamed Project")
    custom_text = project.get("portfolio_showcase_text")
    data = project.get("data", {})

    # New granular fields
    proj_desc = project.get("custom_portfolio_project_description")
    role_desc = project.get("custom_portfolio_description")
    
    if user_stats and user_stats.get("custom_portfolio_project_description"):
        proj_desc = user_stats.get("custom_portfolio_project_description")

    if user_stats and user_stats.get("custom_portfolio_description"):
        role_desc = user_stats.get("custom_portfolio_description")

    role = project.get("role")
    evidence = project.get("evidence_of_success")
    thumbnail = project.get("thumbnail")

    if custom_text:
        text = custom_text
    else:
        text_parts = [f"{project_name} showcase"]
        if role:
            text_parts.append(f"role: {role}")
        skills = project.get("highlighted_skills") or project.get("skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        if skills:
            text_parts.append(f"skills: {', '.join(map(str, skills[:6]))}")
        if evidence:
            text_parts.append(f"evidence: {evidence}")
        text = " | ".join(text_parts)

    # Determine tech stack (custom > highlighted > auto-detected)
    tech_stack = project.get("custom_portfolio_tech_stack")
    if user_stats and "custom_portfolio_tech_stack" in user_stats:
        tech_stack = user_stats.get("custom_portfolio_tech_stack")
        
    if not tech_stack:
        # Try to combine languages and frameworks for a richer stack
        langs = data.get("languages", [])
        fworks = data.get("frameworks", [])
        if langs or fworks:
            if isinstance(langs, str): langs = [langs]
            if isinstance(fworks, str): fworks = [fworks]
            combined = sorted(list(set(langs + fworks)))
            tech_stack = [t for t in combined if t and str(t).upper() not in ("NA", "NONE", "UNKNOWN")]
        else:
            tech_stack = project.get("highlighted_skills") or project.get("skills") or []
            if isinstance(tech_stack, str):
                tech_stack = [s.strip() for s in tech_stack.split(",") if s.strip()]

    # Contribution Stats
    contribution_display = None
    commits = data.get("commit_count")
    lines_added = data.get("lines_added")
    lines_removed = data.get("lines_removed")
    file_breakdown = data.get("extension_counts")
    daily_commits = {}
    
    if contributor_id:
        pcts = data.get("per_contributor_pct", {})
        val = pcts.get(contributor_id)
        if val is not None:
            contribution_display = f"{val:.1f}% of codebase"
        
        # Use user_stats from contributor_profiles if available (Rich Data)
        if user_stats:
            commits = user_stats.get("commit_count", 0)
            lines_added = user_stats.get("insertions", 0)
            lines_removed = user_stats.get("deletions", 0)
            daily_commits = user_stats.get("daily_commits", {})
            
            files_list = user_stats.get("files_list", [])
            if files_list:
                exts = [os.path.splitext(f)[1].lower() for f in files_list]
                cnt = Counter(exts)
                file_breakdown = dict(cnt)
        else:
            # Fallback to per_contributor_* keys in project summary
            c_commits = data.get("per_contributor_commits", {}).get(contributor_id) or data.get("per_contributor_commit_counts", {}).get(contributor_id)
            if c_commits is not None:
                commits = c_commits
                
            pc_adds = data.get("per_contributor_additions", {}) or data.get("per_contributor_lines_added", {})
            pc_dels = data.get("per_contributor_deletions", {}) or data.get("per_contributor_lines_removed", {})
            if contributor_id in pc_adds:
                lines_added = pc_adds[contributor_id]
            if contributor_id in pc_dels:
                lines_removed = pc_dels[contributor_id]
                
            pc_exts = data.get("per_contributor_extensions", {}) or data.get("per_contributor_file_breakdown", {})
            if contributor_id in pc_exts:
                file_breakdown = pc_exts[contributor_id]

    return {
        "project_id": project["project_id"],
        "project_name": project_name,
        "text": text,
        "role": role,
        "evidence_of_success": evidence,
        "thumbnail": thumbnail,
        "comparison_attributes": project.get("comparison_attributes", {}),
        "project_description": proj_desc,
        "role_description": role_desc,
        "tech_stack": tech_stack,
        "contribution_display": contribution_display,
        "impact_score": data.get("score"),
        "duration_days": data.get("duration_days"),
        "first_modified": data.get("first_modified"),
        "last_modified": data.get("last_modified"),
        "commits": commits,
        "daily_commits": daily_commits,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "file_breakdown": file_breakdown,
    }


def _ordered_project_ids(candidates: List[Dict[str, Any]], explicit_order: Optional[List[str]] = None) -> List[str]:
    ids = [p["project_id"] for p in sorted(candidates, key=_project_sort_key, reverse=True)]
    if not explicit_order:
        return ids
    ordered: List[str] = []
    seen = set()
    for pid in explicit_order:
        if pid in ids and pid not in seen:
            ordered.append(pid)
            seen.add(pid)
    for pid in ids:
        if pid not in seen:
            ordered.append(pid)
    return ordered


async def _parse_upload_inputs(request: Request) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    payload: Dict[str, Any] = {}
    form = None
    if "multipart/form-data" in content_type:
        form = await request.form()
        payload = dict(form)
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                payload = body
        except Exception:
            payload = {}

    return {
        "payload": payload,
        "form": form,
        "content_type": content_type,
    }


async def _materialize_zip_from_request(parsed_inputs: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    payload = parsed_inputs["payload"]
    form = parsed_inputs["form"]
    temp_zip_path: Optional[str] = None
    zip_path = payload.get("zip_path")

    if form is not None:
        zip_file = form.get("zip")
        if zip_file is not None and hasattr(zip_file, "read"):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            data = await zip_file.read()
            tmp.write(data)
            tmp.close()
            zip_path = tmp.name
            temp_zip_path = tmp.name
            close_fn = getattr(zip_file, "close", None)
            if callable(close_fn):
                maybe_awaitable = close_fn()
                if hasattr(maybe_awaitable, "__await__"):
                    await maybe_awaitable

    return zip_path, temp_zip_path


def _resolve_incremental_target(payload: Dict[str, Any]) -> Optional[int]:
    existing_scan_id = payload.get("existing_scan_id")
    if existing_scan_id is not None and str(existing_scan_id).strip() != "":
        try:
            return int(existing_scan_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="existing_scan_id must be an integer") from exc

    portfolio_id = payload.get("portfolio_id")
    if portfolio_id is not None and str(portfolio_id).strip() != "":
        try:
            portfolio_id_int = int(portfolio_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="portfolio_id must be an integer") from exc
        artifact = get_portfolio_artifact(portfolio_id_int)
        if not artifact:
            raise HTTPException(status_code=404, detail="portfolio not found")
        if artifact.get("scan_summary_id") is None:
            raise HTTPException(status_code=400, detail="portfolio is not linked to a scan")
        return int(artifact["scan_summary_id"])

    resume_id = payload.get("resume_id")
    if resume_id is not None and str(resume_id).strip() != "":
        try:
            resume_id_int = int(resume_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="resume_id must be an integer") from exc
        artifact = get_resume_artifact(resume_id_int)
        if not artifact:
            raise HTTPException(status_code=404, detail="resume not found")
        if artifact.get("scan_summary_id") is None:
            raise HTTPException(status_code=400, detail="resume is not linked to a scan")
        return int(artifact["scan_summary_id"])

    return None


async def _handle_scan_upload(request: Request, include_project_summary: bool) -> JSONResponse:
    parsed = await _parse_upload_inputs(request)
    payload = parsed["payload"]
    zip_path, temp_zip_path = await _materialize_zip_from_request(parsed)

    analysis_mode = _parse_analysis_mode(payload.get("analysis_mode"))
    if not analysis_mode:
        raise HTTPException(status_code=400, detail="analysis_mode must be one of: basic, advanced")

    advanced_options, advanced_options_error = _parse_advanced_options(payload.get("advanced_options"))
    if advanced_options_error:
        raise HTTPException(status_code=400, detail=advanced_options_error)
    if analysis_mode == "basic" and advanced_options:
        raise HTTPException(status_code=400, detail="advanced_options is only supported in advanced mode")

    consent = _parse_bool(payload.get("consent"), default=False)
    persist = _parse_bool(payload.get("persist"), default=True)
    allow_duplicate = _parse_bool(payload.get("allow_duplicate"), default=False)
    incremental = _parse_bool(payload.get("incremental"), default=False)

    if not zip_path:
        raise HTTPException(status_code=400, detail="zip file or zip_path is required")

    try:
        validation_result = _check_file_validity(str(zip_path))
        if not validation_result:
            raise HTTPException(status_code=400, detail="invalid or empty zip file")

        # Backward compatibility if older code returns only file_list.
        if isinstance(validation_result, tuple) and len(validation_result) == 2:
            file_list, zip_hash = validation_result
        else:
            file_list = validation_result
            zip_hash = None

        results = await run_in_threadpool(_analyze_scan, file_list, analysis_mode, advanced_options or {})
        if results is None:
            raise HTTPException(status_code=500, detail="scan execution failed")

        if isinstance(results, dict) and zip_hash:
            results["zip_hash"] = zip_hash
            source_hashes = list(results.get("source_hashes", []))
            if zip_hash not in source_hashes:
                source_hashes.append(zip_hash)
            results["source_hashes"] = source_hashes

        persisted_scan_id: Optional[int] = None
        duplicate = False
        merge_applied = False

        target_scan_id = _resolve_incremental_target(payload) if incremental else None

        if persist:
            if zip_hash and not target_scan_id and not allow_duplicate and scan_exists(zip_hash):
                duplicate = True
            elif target_scan_id:
                existing_scan = get_full_scan_by_id(target_scan_id)
                if not existing_scan:
                    raise HTTPException(status_code=404, detail="target scan not found")
                existing_data = (existing_scan.get("scan_data") or {})
                existing_hashes = set(existing_data.get("source_hashes", []))
                if zip_hash and (zip_hash in existing_hashes) and not allow_duplicate:
                    duplicate = True
                    persisted_scan_id = target_scan_id
                else:
                    merged = _merge_scans(existing_data, results)
                    update_full_scan(target_scan_id, merged)
                    persisted_scan_id = target_scan_id
                    merge_applied = True
            else:
                persisted_scan_id = save_full_scan(results, analysis_mode, consent)

        response_body: Dict[str, Any] = {
            "analysis_mode": analysis_mode,
            "persisted": persist,
            "duplicate": duplicate,
            "incremental": incremental,
            "merged": merge_applied,
            "summary_id": persisted_scan_id,
            "results": _json_safe(results),
        }

        if include_project_summary:
            scan_id_for_projects = persisted_scan_id
            projects = []
            for idx, project in enumerate(results.get("project_summaries", []) if isinstance(results, dict) else []):
                if not isinstance(project, dict):
                    continue
                sid = int(scan_id_for_projects) if scan_id_for_projects is not None else -1
                proj = _build_project_record(sid, idx, project)
                if sid == -1:
                    proj["project_id"] = f"temp:{idx}"
                projects.append(_json_safe(proj))
            response_body["projects"] = projects

        status_code = 201
        if duplicate:
            status_code = 200
            response_body["message"] = "duplicate upload recognized; no duplicate persisted"
        elif merge_applied:
            status_code = 200

        return JSONResponse(content=_json_safe(response_body), status_code=status_code)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Scan execution failed")
        raise HTTPException(status_code=500, detail="scan execution failed")
    finally:
        if temp_zip_path:
            try:
                os.remove(temp_zip_path)
            except OSError:
                pass


def _select_projects_for_artifact(
    scan_id: Optional[int],
    project_ids: List[str],
    selected_project_ids: Optional[List[str]],
    project_order: Optional[List[str]],
) -> Tuple[Optional[int], List[Dict[str, Any]], List[str]]:
    candidates = []
    if project_ids:
        candidates = [_get_project_by_id(pid) for pid in project_ids]
    elif scan_id is not None:
        candidates = _iter_projects(scan_id=scan_id)
    else:
        candidates = _iter_projects()

    if selected_project_ids:
        selected_set = set(selected_project_ids)
        candidates = [p for p in candidates if p["project_id"] in selected_set]

    ordered_ids = _ordered_project_ids(candidates, explicit_order=project_order)
    project_map = {p["project_id"]: p for p in candidates}
    ordered_projects = [project_map[pid] for pid in ordered_ids if pid in project_map]
    return scan_id, ordered_projects, ordered_ids


def create_app() -> FastAPI:
    app = FastAPI(
        title="Skill Scope API",
        version="0.2.0",
        description="FastAPI endpoints for project upload, portfolio, and resume workflows.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    def _http_exception_handler(_request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.get("/")
    def root():
        return {
            "app": "Skill Scope API",
            "version": "0.2.0",
            "status": "ready",
            "message": "Welcome to Skill Scope. Use /docs for API documentation."
        }

    @app.get("/health")
    def health():
        """
        Simple health check endpoint to verify the API is running.
        """
        return {"status": "ok"}

    # Legacy scan endpoints kept for compatibility
    @app.post("/scans")
    async def create_scan(request: Request):
        """
        Legacy endpoint for creating a scan.
        Wraps the upload logic but returns a simplified response structure if needed.
        """
        return await _handle_scan_upload(request, include_project_summary=False)

    @app.get("/scans")
    def get_scans():
        """
        Retrieves a list of all historical scans (metadata only).
        """
        try:
            scans = list_full_scans()
        except Exception:
            logger.exception("Failed to list scans")
            raise HTTPException(status_code=500, detail="failed to list scans")
        return {"scans": _json_safe(scans)}

    @app.get("/scans/check")
    def check_scan_exists(file_hash: str = Query(..., min_length=1)):
        """
        Checks if a scan with the given file hash already exists.
        """
        return {"exists": scan_exists(file_hash)}

    @app.get("/scans/{summary_id}")
    def get_scan(summary_id: int = Path(..., ge=1)):
        """
        Retrieves the full detailed analysis results for a specific scan ID.
        """
        try:
            scan = get_full_scan_by_id(summary_id)
        except Exception:
            logger.exception("Failed to fetch scan summary_id=%s", summary_id)
            raise HTTPException(status_code=500, detail="failed to retrieve scan")
        if not scan:
            raise HTTPException(status_code=404, detail="scan not found")
        return {"scan": _json_safe(scan)}

    @app.delete("/scans/{summary_id}")
    def delete_scan(summary_id: int = Path(..., ge=1)):
        """
        Permanently deletes a scan and its associated data from the database.
        """
        try:
            deleted = delete_full_scan_by_id(summary_id)
        except Exception:
            logger.exception("Failed to delete scan summary_id=%s", summary_id)
            raise HTTPException(status_code=500, detail="failed to delete scan")
        if not deleted:
            raise HTTPException(status_code=404, detail="scan not found")
        return {"deleted": True, "summary_id": summary_id}

    # Milestone endpoints
    @app.post("/privacy-consent")
    def post_privacy_consent(payload: PrivacyConsentPayload):
        """
        Updates the user's privacy and data processing consent settings.
        """
        saved = set_privacy_settings(_model_dump(payload))
        return {"privacy": _json_safe(saved)}

    @app.get("/privacy-consent")
    def get_privacy():
        """
        Retrieves the current privacy and consent settings.
        """
        return {"privacy": _json_safe(get_privacy_settings())}

    @app.post("/projects/upload")
    async def upload_projects(request: Request):
        """
        Main entry point for scanning. Accepts a ZIP file or path.
        Performs analysis and persists results. Supports incremental updates.
        """
        return await _handle_scan_upload(request, include_project_summary=True)

    @app.get("/projects")
    def list_projects(scan_id: Optional[int] = Query(None, ge=1)):
        """
        Lists all individual projects found across all scans (or filtered by scan_id).
        """
        projects = _iter_projects(scan_id=scan_id)
        return {"projects": _json_safe(sorted(projects, key=_project_sort_key, reverse=True))}

    @app.get("/projects/{project_id:path}")
    def get_project(project_id: str):
        """
        Retrieves details for a specific project, including any user customizations.
        """
        return {"project": _json_safe(_get_project_by_id(project_id))}

    @app.post("/projects/{project_id:path}/edit")
    def edit_project(project_id: str, payload: ProjectEditPayload):
        """
        Updates project metadata (e.g., custom descriptions, showcase flags).
        """
        _get_project_by_id(project_id)  # validate existence
        saved = upsert_project_customization(project_id, _model_dump_exclude_none(payload))
        return {"project_id": project_id, "customization": _json_safe(saved)}

    @app.post("/projects/{project_id:path}/thumbnail")
    async def upload_project_thumbnail(
        project_id: str,
        file: UploadFile = File(...)
    ):
        """
        Uploads a thumbnail image for a project.
        """
        _get_project_by_id(project_id)  # validate existence
        
        # Generate safe filename
        safe_pid = project_id.replace(":", "_")
        # Get extension from uploaded filename
        _, ext = os.path.splitext(file.filename)
        if not ext:
            ext = ".jpg" # Default fallback
            
        filename = f"{safe_pid}_thumb{ext}"
        path = os.path.join(THUMBNAILS_DIR, filename)
        
        try:
            content = await file.read()
            with open(path, "wb") as f:
                f.write(content)
        except Exception:
            logger.exception("Failed to save thumbnail")
            raise HTTPException(status_code=500, detail="Failed to save file")
            
        # Update customization
        saved = upsert_project_customization(project_id, {"thumbnail": filename})
        
        return {"project_id": project_id, "thumbnail": filename, "customization": _json_safe(saved)}

    @app.post("/scans/{summary_id}/contributors/merge")
    def merge_contributors(
        payload: MergeContributorsPayload,
        summary_id: int = Path(..., ge=1)
    ):
        """
        Merges one or more secondary contributor identities into a primary contributor profile.
        """
        scan = get_full_scan_by_id(summary_id)
        if not scan:
            raise HTTPException(status_code=404, detail="scan not found")
            
        data = scan.get("scan_data", {})
        profiles = data.get("contributor_profiles", {})
        
        primary = payload.primary_contributor
        secondaries = [s for s in payload.contributors_to_merge if s in profiles and s != primary]
        
        if primary not in profiles or not secondaries:
            return {"status": "no_action"}
            
        # 1. Merge the main contributor profiles
        prim_prof = profiles[primary]
        for sec in secondaries:
            sec_prof = profiles[sec]
            prim_prof["skills"] = sorted(list(set(prim_prof.get("skills", []) + sec_prof.get("skills", []))))
            
            prim_proj_map = {p["name"]: p for p in prim_prof.get("projects", [])}
            for sp in sec_prof.get("projects", []):
                pname = sp.get("name")
                if pname in prim_proj_map:
                    pp = prim_proj_map[pname]
                    pp["pct"] = pp.get("pct", 0) + sp.get("pct", 0)
                    pp["score"] = pp.get("score", 0) + sp.get("score", 0)
                    pp["files_worked"] = pp.get("files_worked", 0) + sp.get("files_worked", 0)
                    pp["insertions"] = pp.get("insertions", 0) + sp.get("insertions", 0)
                    pp["deletions"] = pp.get("deletions", 0) + sp.get("deletions", 0)
                    pp["commit_count"] = pp.get("commit_count", 0) + sp.get("commit_count", 0)
                    
                    if "daily_commits" not in pp: pp["daily_commits"] = {}
                    for d, cnt in sp.get("daily_commits", {}).items():
                        pp["daily_commits"][d] = pp["daily_commits"].get(d, 0) + cnt
                        
                    pp["files_list"] = sorted(list(set(pp.get("files_list", []) + sp.get("files_list", []))))
                else:
                    prim_prof["projects"].append(sp)
            del profiles[sec]
            
        # 2. Merge stats inside project_summaries
        for proj in data.get("project_summaries", []):
            for key in ["per_contributor_pct", "per_contributor_commits", "per_contributor_commit_counts", "per_contributor_additions", "per_contributor_lines_added", "per_contributor_deletions", "per_contributor_lines_removed"]:
                sub = proj.get(key)
                if isinstance(sub, dict):
                    for sec in secondaries:
                        if sec in sub: sub[primary] = sub.get(primary, 0) + sub.pop(sec)
                        
        update_full_scan(summary_id, data)
        return {"status": "merged"}

    @app.post("/scans/{summary_id}/contributors/{contributor_id:path}")
    def update_contributor_profile(
        payload: ContributorProfileEditPayload,
        summary_id: int = Path(..., ge=1),
        contributor_id: str = Path(...)
    ):
        """
        Updates a contributor's profile details (name, title, summary) and project-specific overrides.
        """
        scan = get_full_scan_by_id(summary_id)
        if not scan:
            raise HTTPException(status_code=404, detail="scan not found")
        
        data = scan["scan_data"]
        profiles = data.get("contributor_profiles", {})
        if contributor_id not in profiles:
             raise HTTPException(status_code=404, detail="contributor not found")
        
        profile = profiles[contributor_id]
        
        if payload.reset_profile:
            # Clear custom fields
            for k in list(profile.keys()):
                if k.startswith("custom_"):
                    profile.pop(k)
            # Clear project custom fields
            for p in profile.get("projects", []):
                for k in list(p.keys()):
                    if k.startswith("custom_") and k != "custom_portfolio_description":
                        p.pop(k)
        else:
            if payload.custom_name is not None:
                profile["custom_name"] = payload.custom_name if payload.custom_name else None
                if profile["custom_name"] is None: profile.pop("custom_name", None)
            
            if payload.custom_title is not None:
                profile["custom_title"] = payload.custom_title if payload.custom_title else None
                if profile["custom_title"] is None: profile.pop("custom_title", None)
            
            if payload.custom_summary is not None:
                profile["custom_summary"] = payload.custom_summary if payload.custom_summary else None
                if profile["custom_summary"] is None: profile.pop("custom_summary", None)
            
            if payload.project_updates:
                p_map = {p.get("name"): p for p in profile.get("projects", [])}
                for p_name, p_edit in payload.project_updates.items():
                    if p_name in p_map:
                        target = p_map[p_name]
                        if p_edit.custom_description is not None:
                            target["custom_description"] = p_edit.custom_description if p_edit.custom_description else None
                            if target["custom_description"] is None: target.pop("custom_description", None)
                        
                        if p_edit.reset_custom_skills:
                            target.pop("custom_skills", None)
                        elif p_edit.custom_skills is not None:
                            target["custom_skills"] = p_edit.custom_skills
                            
                        if p_edit.custom_portfolio_project_description is not None:
                            target["custom_portfolio_project_description"] = p_edit.custom_portfolio_project_description if p_edit.custom_portfolio_project_description else None
                            if target["custom_portfolio_project_description"] is None: target.pop("custom_portfolio_project_description", None)
                            
                        if p_edit.custom_portfolio_description is not None:
                            target["custom_portfolio_description"] = p_edit.custom_portfolio_description if p_edit.custom_portfolio_description else None
                            if target["custom_portfolio_description"] is None: target.pop("custom_portfolio_description", None)
                        
                        if p_edit.reset_custom_portfolio_tech_stack:
                            target.pop("custom_portfolio_tech_stack", None)
                        elif p_edit.custom_portfolio_tech_stack is not None:
                            target["custom_portfolio_tech_stack"] = p_edit.custom_portfolio_tech_stack

        update_full_scan(summary_id, data)
        return {"status": "updated", "contributor_id": contributor_id}

    @app.get("/skills")
    def get_skills(scan_id: Optional[int] = Query(None, ge=1)):
        """
        Returns an aggregated list of skills and their frequency across projects.
        """
        projects = _iter_projects(scan_id=scan_id)
        skills_count: Dict[str, int] = {}
        for project in projects:
            skills = project.get("highlighted_skills") or project.get("skills") or []
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",") if s.strip()]
            for skill in skills:
                skills_count[str(skill)] = skills_count.get(str(skill), 0) + 1
        skills = [{"skill": name, "project_count": count} for name, count in sorted(skills_count.items())]
        return {"skills": skills}

    @app.post("/resume/generate")
    def generate_resume(payload: ResumeGeneratePayload):
        """
        Creates a new Resume artifact (JSON) based on selected projects.
        """
        scan_id, selected_projects, ordered_ids = _select_projects_for_artifact(
            payload.scan_id,
            payload.project_ids,
            payload.selected_project_ids or None,
            payload.project_order or None,
        )

        # Filter by contributor if specified
        if payload.contributor_id:
            filtered_projects = []
            for p in selected_projects:
                # Check if contributor has > 0 percentage in this project
                pcts = p.get("data", {}).get("per_contributor_pct", {})
                if pcts.get(payload.contributor_id, 0) > 0:
                    filtered_projects.append(p)
            selected_projects = filtered_projects

        # Resolve user header info if contributor_id is provided
        user_header = {}
        user_project_stats = {}

        if scan_id and payload.contributor_id:
            scan = get_full_scan_by_id(scan_id)
            if scan:
                profiles = scan.get("scan_data", {}).get("contributor_profiles", {})
                profile = profiles.get(payload.contributor_id)
                if profile:
                    # Use custom fields from profile if they exist, else defaults
                    # 1. Name
                    name = profile.get("custom_name") or payload.contributor_id
                    if "@" in name and not profile.get("custom_name"):
                        name = name.split("@")[0].replace(".", " ").title()
                    user_header["user_name"] = name

                    # 2. Title
                    title = profile.get("custom_title")
                    if not title:
                        user_skills = profile.get("skills", [])
                        title = "Software Contributor"
                        dev_keywords = {"Development", "Programming", "Engineering"}
                        if any(any(k in s for k in dev_keywords) for s in user_skills):
                            title = "Software Developer"
                    user_header["user_title"] = title

                    # 3. Summary
                    summary = profile.get("custom_summary")
                    if not summary:
                        proj_count = len(profile.get("projects", []))
                        summary = f"{title} with a track record of contributions across {proj_count} project(s)."
                        p_skills = profile.get("skills", [])
                        if p_skills:
                            summary += f" Proficient in {', '.join(p_skills[:3])}"
                            if len(p_skills) > 3:
                                summary += f", along with expertise in {len(p_skills)-3} other technologies"
                            summary += "."
                    user_header["user_summary"] = summary
                    user_header["skills"] = profile.get("skills", [])

                    # 4. Map project stats for rich descriptions
                    for p_entry in profile.get("projects", []):
                        if p_entry.get("name"):
                            user_project_stats[p_entry["name"]] = p_entry

        items = [_project_to_resume_item(p, user_project_stats.get(p.get("project_name")), payload.contributor_id) for p in selected_projects]
        artifact_data = {
            "kind": "resume",
            "items": items,
            "selected_project_ids": [p["project_id"] for p in selected_projects],
            "project_order": ordered_ids,
            # Header fields
            "user_name": user_header.get("user_name"),
            "user_title": user_header.get("user_title"),
            "user_summary": user_header.get("user_summary"),
            "skills": user_header.get("skills", []),
        }
        saved = create_resume_artifact(artifact_data, scan_summary_id=scan_id, title=payload.title)
        return {"resume": _json_safe(saved)}

    @app.get("/resume/{resume_id}")
    def get_resume(resume_id: int = Path(..., ge=1)):
        """
        Retrieves a stored Resume artifact.
        """
        artifact = get_resume_artifact(resume_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="resume not found")
        return {"resume": _json_safe(artifact)}

    @app.post("/resume/{resume_id}/edit")
    def edit_resume(resume_id: int, payload: ResumeEditPayload):
        """
        Updates an existing Resume artifact (reorder projects, edit wording).
        """
        artifact = get_resume_artifact(resume_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="resume not found")

        if payload.project_wording_edits:
            for project_id, wording in payload.project_wording_edits.items():
                _get_project_by_id(project_id)  # validate
                upsert_project_customization(project_id, {"resume_wording": wording})

        patch: Dict[str, Any] = _model_dump_exclude_none(payload)
        if payload.selected_project_ids is not None or payload.project_order is not None:
            selected_ids = payload.selected_project_ids or artifact["data"].get("selected_project_ids", [])
            ordered_ids = payload.project_order or artifact["data"].get("project_order", [])
            selected_projects = [_get_project_by_id(pid) for pid in selected_ids]
            ordered_ids = _ordered_project_ids(selected_projects, explicit_order=ordered_ids)
            project_map = {p["project_id"]: p for p in selected_projects}
            patch["items"] = [_project_to_resume_item(project_map[pid]) for pid in ordered_ids if pid in project_map]
            patch["selected_project_ids"] = selected_ids
            patch["project_order"] = ordered_ids

        saved = update_resume_artifact(resume_id, patch)
        return {"resume": _json_safe(saved)}

    @app.get("/resume/{resume_id}/export")
    def export_resume(resume_id: int = Path(..., ge=1)):
        """
        Generates and downloads a DOCX file for the specified resume artifact.
        """
        artifact = get_resume_artifact(resume_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="resume not found")
        
        try:
            # Sanitize title for filename
            title = artifact.get("title", "resume")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
            filename = f"{safe_title}.docx"
            
            # Use temp directory to avoid cluttering output folder
            fd, path = tempfile.mkstemp(suffix=".docx")
            os.close(fd)
            
            # Render the document
            render_resume_artifact(artifact["data"], path)
            
            return FileResponse(path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception:
            logger.exception("Failed to export resume")
            raise HTTPException(status_code=500, detail="failed to generate document")

    @app.post("/portfolio/generate")
    def generate_portfolio(payload: PortfolioGeneratePayload):
        """
        Creates a new Portfolio artifact (JSON). Honors 'selected_for_showcase' flags.
        """
        scan_id, selected_projects, ordered_ids = _select_projects_for_artifact(
            payload.scan_id,
            payload.project_ids,
            payload.selected_project_ids or None,
            payload.project_order or None,
        )

        # Filter by contributor if specified
        if payload.contributor_id:
            filtered_projects = []
            for p in selected_projects:
                pcts = p.get("data", {}).get("per_contributor_pct", {})
                if pcts.get(payload.contributor_id, 0) > 0:
                    filtered_projects.append(p)
            selected_projects = filtered_projects

        # Default showcase selection honors project customization if explicit selection not provided.
        if not payload.selected_project_ids:
            showcase_filtered = [
                p for p in selected_projects if p.get("selected_for_showcase") is not False
            ]
            if showcase_filtered:
                selected_projects = showcase_filtered
        
        # Resolve user stats from contributor_profiles
        user_project_stats_map = {}
        if scan_id and payload.contributor_id:
            scan = get_full_scan_by_id(scan_id)
            if scan:
                profiles = scan.get("scan_data", {}).get("contributor_profiles", {})
                profile = profiles.get(payload.contributor_id)
                if profile:
                    for p_entry in profile.get("projects", []):
                        if p_entry.get("name"):
                            user_project_stats_map[p_entry["name"]] = p_entry

        items = [_project_to_portfolio_item(p, contributor_id=payload.contributor_id, user_stats=user_project_stats_map.get(p.get("project_name"))) for p in selected_projects]
        
        # Calculate Global Skills
        all_skills = set()
        for p in selected_projects:
            s = p.get("skills", [])
            if isinstance(s, str):
                s = [x.strip() for x in s.split(",") if x.strip()]
            if isinstance(s, list):
                all_skills.update(s)
        global_skills = sorted(list(all_skills))

        artifact_data = {
            "kind": "portfolio",
            "items": items,
            "selected_project_ids": [p["project_id"] for p in selected_projects],
            "project_order": ordered_ids,
            "contributor_id": payload.contributor_id,
            "global_skills": global_skills,
        }
        saved = create_portfolio_artifact(artifact_data, scan_summary_id=scan_id, title=payload.title)
        return {"portfolio": _json_safe(saved)}

    @app.get("/portfolio/{portfolio_id}")
    def get_portfolio(portfolio_id: int = Path(..., ge=1)):
        """
        Retrieves a stored Portfolio artifact.
        """
        artifact = get_portfolio_artifact(portfolio_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="portfolio not found")
        return {"portfolio": _json_safe(artifact)}

    @app.post("/portfolio/{portfolio_id}/edit")
    def edit_portfolio(portfolio_id: int, payload: PortfolioEditPayload):
        """
        Updates an existing Portfolio artifact.
        """
        artifact = get_portfolio_artifact(portfolio_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="portfolio not found")

        if payload.project_edits:
            for project_id, edit in payload.project_edits.items():
                _get_project_by_id(project_id)  # validate
                upsert_project_customization(project_id, _model_dump_exclude_none(edit))

        patch: Dict[str, Any] = _model_dump_exclude_none(payload)
        if payload.selected_project_ids is not None or payload.project_order is not None:
            selected_ids = payload.selected_project_ids or artifact["data"].get("selected_project_ids", [])
            ordered_ids = payload.project_order or artifact["data"].get("project_order", [])
            selected_projects = [_get_project_by_id(pid) for pid in selected_ids]
            ordered_ids = _ordered_project_ids(selected_projects, explicit_order=ordered_ids)
            project_map = {p["project_id"]: p for p in selected_projects}
            contributor_id = artifact["data"].get("contributor_id")
            
            # Fetch user stats to preserve data on edit
            user_project_stats_map = {}
            scan_id = artifact.get("scan_summary_id")
            if scan_id and contributor_id:
                scan = get_full_scan_by_id(scan_id)
                if scan:
                    profiles = scan.get("scan_data", {}).get("contributor_profiles", {})
                    profile = profiles.get(contributor_id)
                    if profile:
                        for p_entry in profile.get("projects", []):
                            if p_entry.get("name"):
                                user_project_stats_map[p_entry["name"]] = p_entry

            patch["items"] = [_project_to_portfolio_item(project_map[pid], contributor_id=contributor_id, user_stats=user_project_stats_map.get(project_map[pid].get("project_name"))) for pid in ordered_ids if pid in project_map]
            patch["selected_project_ids"] = selected_ids
            patch["project_order"] = ordered_ids

        saved = update_portfolio_artifact(portfolio_id, patch)
        return {"portfolio": _json_safe(saved)}

    @app.get("/portfolio/{portfolio_id}/export")
    def export_portfolio(portfolio_id: int = Path(..., ge=1)):
        """
        Generates and downloads a Markdown file for the specified portfolio artifact.
        """
        artifact = get_portfolio_artifact(portfolio_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="portfolio not found")
        
        try:
            title = artifact.get("title", "portfolio")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
            filename = f"{safe_title}.md"
            
            # Try using the shared generator if available
            if generate_portfolio_markdown:
                try:
                    content = generate_portfolio_markdown(artifact["data"])
                    fd, path = tempfile.mkstemp(suffix=".md")
                    os.write(fd, content.encode("utf-8"))
                    os.close(fd)
                    logger.info(f"Exported portfolio {portfolio_id} using shared generator")
                    return FileResponse(path, filename=filename, media_type="text/markdown")
                except Exception as e:
                    logger.warning(f"Failed to use portfolio_generator: {e}")
            
            # Generate Markdown content
            data = artifact["data"]
            lines = [f"# {title}", ""]
            
            if data.get("global_skills"):
                lines.append("## Global Skills")
                lines.append(f"**{', '.join(data['global_skills'])}**")
                lines.append("")

            lines.append("## Project Showcase")
            lines.append("")
            
            for item in data.get("items", []):
                name = item.get("project_name", "Unknown Project")
                lines.append(f"### {name}")
                
                if item.get("project_description"):
                    lines.append(f"- **Description:** {item['project_description']}")
                
                if item.get("role_description"):
                    lines.append(f"- **Role/Contribution:** {item['role_description']}")
                elif item.get("contribution_display"):
                    lines.append(f"- **Role/Contribution:** {item['contribution_display']}")
                elif item.get("role"):
                    lines.append(f"- **Role:** {item['role']}")
                
                tech = item.get("tech_stack")
                if tech:
                    val = ", ".join(str(t) for t in tech) if isinstance(tech, list) else str(tech)
                    lines.append(f"- **Tech Stack:** {val}")
                
                if item.get("impact_score") is not None:
                    lines.append(f"- **Impact Score:** {item['impact_score']}")
                
                if item.get("duration_days") is not None:
                    lines.append(f"- **Duration:** {item['duration_days']} days")
                
                if item.get("commits") is not None:
                    lines.append(f"- **Commits:** {item['commits']}")
                
                if item.get("lines_added") is not None or item.get("lines_removed") is not None:
                    la = item.get("lines_added", 0)
                    lr = item.get("lines_removed", 0)
                    lines.append(f"- **Lines:** +{la} / -{lr}")
                
                if item.get("file_breakdown"):
                    fb = item["file_breakdown"]
                    parts = [f"{count} {ext}" for ext, count in sorted(fb.items(), key=lambda x: x[1], reverse=True)]
                    lines.append(f"- **File Breakdown:** {', '.join(parts)}")

                if item.get("evidence_of_success"):
                    lines.append(f"- **Evidence:** {item['evidence_of_success']}")
                
                lines.append("")

            fd, path = tempfile.mkstemp(suffix=".md")
            os.write(fd, "\n".join(lines).encode("utf-8"))
            os.close(fd)
            
            return FileResponse(path, filename=filename, media_type="text/markdown")
        except Exception:
            logger.exception("Failed to export portfolio")
            raise HTTPException(status_code=500, detail="failed to generate document")

    return app


app = create_app()


if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:  # pragma: no cover
        raise SystemExit("Install uvicorn to run the FastAPI app directly")

    uvicorn.run("api:app", host="0.0.0.0", port=5000, reload=True)
