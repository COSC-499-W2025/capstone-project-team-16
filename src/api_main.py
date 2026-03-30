"""
API Client Entry Point

This script runs the Skill Scope system by making HTTP requests to the
FastAPI backend (src/api.py), rather than importing logic directly.

Usage:
    1. Start the API server: python src/api.py
    2. Run this client:      python src/api_main.py
"""

import os
import sys
import requests
import json
import urllib.parse
import subprocess
import time
import atexit

# Add the current directory to sys.path to allow importing local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from file_parser import compute_file_hash, OUTPUT_DIR
from permission_manager import get_user_consent, get_analysis_mode, get_advanced_options, get_yes_no
from print_utils import (
    _center_text,
    _print_banner,
    print_full_scan_report,
    print_scan_list,
    is_noise,
    _input_with_prefill
)
from resume_generator import _build_personal_project_description
from portfolio_generator import _get_default_tech_stack

# Configuration constants
API_URL = os.getenv("SKILLSCOPE_API_URL", "http://127.0.0.1:8000")
INPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input"))

API_PROCESS = None

def cleanup_api_process():
    """Terminates the API subprocess if it was started by this client."""
    global API_PROCESS
    if API_PROCESS:
        print(_center_text("Stopping API server..."))
        API_PROCESS.terminate()
        try:
            API_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            API_PROCESS.kill()

def start_api_server():
    """Attempts to start the API server as a subprocess."""
    global API_PROCESS
    src_dir = os.path.dirname(os.path.abspath(__file__))
    api_script = os.path.join(src_dir, "api.py")
    
    print(_center_text("Attempting to start API server automatically..."))
    
    try:
        log_path = os.path.join(OUTPUT_DIR, "api_server.log")
        log_file = open(log_path, "w")
        API_PROCESS = subprocess.Popen([sys.executable, api_script], cwd=src_dir, stdout=log_file, stderr=subprocess.STDOUT)
        atexit.register(cleanup_api_process)
        
        # Wait for server to initialize
        for _ in range(10):
            time.sleep(1)
            try:
                if requests.get(f"{API_URL}/health", timeout=1).status_code == 200:
                    print(_center_text("API server started successfully."))
                    return True
            except requests.RequestException:
                pass
    except Exception as e:
        print(_center_text(f"Failed to start API server: {e}"))
    
    return False

def _print_menu(title, options, prompt="Choose an option: "):
    """Helper to display a standardized menu and get user input."""
    _print_banner(title)
    for key, label in options:
        print(_center_text(f"{key}. {label}"))
    return input(_center_text(prompt)).strip()


def check_api_connection():
    """Verifies the API server is reachable by pinging the health endpoint."""
    print(_center_text(f"Connecting to API at {API_URL}..."))
    try:
        resp = requests.get(f"{API_URL}/health", timeout=2)
        if resp.status_code == 200:
            print(_center_text("API is online."))
            return True
    except requests.exceptions.RequestException:
        pass
    
    if start_api_server():
        return True

    print(_center_text("Error: Could not connect to API."))
    print(_center_text("Please ensure the API server is running in a separate terminal:"))
    print(_center_text("  python src/api.py"))
    return False


def get_input_zip_file():
    """
    Lists zip files in the input directory, filters duplicates by hash,
    and prompts the user to select one for upload.
    """
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
    
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".zip")]
    if not files:
        print(_center_text(f"No .zip files found in src/input. Please add valid zip files there."))
        return None
    
    # Deduplicate files based on content hash to avoid showing identical zips
    print(_center_text("Checking for duplicates..."))
    unique_zips = []
    seen_hashes = set()
    
    for f in files:
        full_path = os.path.join(INPUT_DIR, f)
        f_hash = compute_file_hash(full_path)
        
        if f_hash and f_hash in seen_hashes:
            continue
        if f_hash:
            seen_hashes.add(f_hash)
        unique_zips.append(f)
    files = unique_zips

    _print_banner("SELECT FILE TO UPLOAD")
    for i, f in enumerate(files, 1):
        print(_center_text(f"{i}. {f}"))
    
    choice = input(_center_text("Choose a file (0 to cancel): ")).strip()
    if not choice.isdigit():
        return None
    idx = int(choice) - 1
    if idx < 0 or idx >= len(files):
        return None
    
    return os.path.join(INPUT_DIR, files[idx])


def run_new_scan_via_api():
    """
    Orchestrates the new scan workflow:
    1. Select Analysis Mode -> 2. Select File -> 3. Consent -> 4. Upload & Scan
    """
    # 1. Analysis Mode (First)
    mode_raw = get_analysis_mode()
    if not mode_raw:
        return
    mode = mode_raw.lower()

    # 1b. Advanced Options
    advanced_options = {}
    if mode == "advanced":
        advanced_options = get_advanced_options()

    # 2. File Selection (Second)
    zip_path = get_input_zip_file()
    if not zip_path:
        return

    # Check for duplicates via API
    allow_duplicate = False
    zip_hash = compute_file_hash(zip_path)
    if zip_hash:
        try:
            resp = requests.get(f"{API_URL}/scans/check", params={"file_hash": zip_hash})
            if resp.status_code == 200 and resp.json().get("exists"):
                print()
                print(_center_text("Warning: This project has already been scanned."))
                if not get_yes_no("Do you want to scan it again?"):
                    return
                allow_duplicate = True
        except Exception:
            pass

    # 3. Consent
    # Check if consent is already granted via API (from initialization)
    consent = False
    try:
        r = requests.get(f"{API_URL}/privacy-consent")
        if r.status_code == 200:
            consent = r.json().get("privacy", {}).get("consent", False)
    except Exception:
        pass

    if not consent:
        print()
        if input(_center_text("Consent to process data? (y/n): ")).strip().lower() == 'y':
            consent = True
        else:
            print(_center_text("Consent denied. Aborting."))
            return

    # 4. Upload and Scan
    print(_center_text("Uploading and scanning via API... please wait..."))
    
    try:
        # Send file to API
        with open(zip_path, 'rb') as f:
            files = {'zip': f}
            data = {
                'analysis_mode': mode,
                'consent': str(consent).lower(),
                'persist': 'true',
                'allow_duplicate': str(allow_duplicate).lower(),
                'advanced_options': json.dumps(advanced_options)
            }
            resp = requests.post(f"{API_URL}/projects/upload", files=files, data=data)
            
        if resp.status_code in (200, 201):
            result = resp.json()

            print(_center_text("Scan Complete!"))
            # Display summary using the returned JSON data
            scan_data = result.get("results", {})
            if scan_data:
                print_full_scan_report(scan_data)
        else:
            print(_center_text(f"API Error: {resp.status_code} - {resp.text}"))

    except Exception as e:
        print(_center_text(f"Request failed: {e}"))
    
    input(_center_text("Press Enter to continue..."))


def _fetch_scans():
    """Helper to get list of scans."""
    try:
        resp = requests.get(f"{API_URL}/scans")
        if resp.status_code == 200:
            return resp.json().get("scans", [])
    except Exception:
        pass
    return []


def view_full_scan_details_via_api():
    """Lists scans and shows detailed report for selected one."""
    scans = _fetch_scans()
    if not scans:
        print(_center_text("No scans found."))
        input(_center_text("Press Enter..."))
        return

    print()
    print(_center_text("Select a scan to view:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        return
    
    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print(_center_text("Invalid selection."))
        return

    summary_id = scans[idx]["summary_id"]

    # Fetch full details
    try:
        resp = requests.get(f"{API_URL}/scans/{summary_id}")
        if resp.status_code != 200:
            print(_center_text("Failed to retrieve scan details."))
            input(_center_text("Press Enter..."))
            return
        
        scan_wrapper = resp.json().get("scan", {})
        data = scan_wrapper.get("scan_data", {})

        _print_banner("FULL SCAN DETAILS")
        print(f"Timestamp: {scan_wrapper.get('timestamp')}")
        print(f"Mode: {scan_wrapper.get('analysis_mode')}")
        print("=" * 28)

        print_full_scan_report(data)

        print(_center_text("\nEnd of scan view.\n"))
        input(_center_text("Press Enter to continue..."))
    except Exception as e:
        print(_center_text(f"Error fetching details: {e}"))
        input(_center_text("Press Enter..."))


def update_scan_via_api():
    """
    Allows updating an existing scan by uploading a new zip file (incremental merge).
    """
    # 1. Fetch scans
    scans = _fetch_scans()
    if not scans:
        print(_center_text("No scans found."))
        input(_center_text("Press Enter..."))
        return

    print()
    print(_center_text("Select a scan to update:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        return
    
    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        print(_center_text("Invalid selection."))
        return

    target_scan = scans[idx]
    summary_id = target_scan["summary_id"]
    # Use the same analysis mode as the original scan to ensure consistency
    analysis_mode = target_scan.get("analysis_mode", "basic")
    
    # Fetch existing hashes for this scan to prevent duplicate uploads
    existing_hashes = set()
    try:
        detail_resp = requests.get(f"{API_URL}/scans/{summary_id}")
        if detail_resp.status_code == 200:
            scan_data = detail_resp.json().get("scan", {}).get("scan_data", {})
            existing_hashes = set(scan_data.get("source_hashes", []))
    except Exception:
        # If we can't fetch details, we'll rely on the server-side check
        pass

    # 2. Select file
    zip_path = get_input_zip_file()
    if not zip_path:
        return
        
    # Check if file is already in the scan
    if existing_hashes:
        local_hash = compute_file_hash(zip_path)
        if local_hash and local_hash in existing_hashes:
            print(_center_text("This file has already been added to this scan."))
            input(_center_text("Press Enter..."))
            return

    # 3. Consent (check server or ask)
    consent = False
    try:
        r = requests.get(f"{API_URL}/privacy-consent")
        if r.status_code == 200:
            consent = r.json().get("privacy", {}).get("consent", False)
    except Exception:
        pass

    if not consent:
        print()
        if input(_center_text("Consent to process data? (y/n): ")).strip().lower() == 'y':
            consent = True
        else:
            print(_center_text("Consent denied. Aborting."))
            return

    # 4. Upload
    print(_center_text("Uploading and merging via API... please wait..."))
    try:
        with open(zip_path, 'rb') as f:
            files = {'zip': f}
            data = {
                'analysis_mode': analysis_mode,
                'consent': str(consent).lower(),
                'persist': 'true',
                'incremental': 'true',
                'existing_scan_id': str(summary_id)
            }
            
            resp = requests.post(f"{API_URL}/projects/upload", files=files, data=data)
            
        if resp.status_code in (200, 201):
            result = resp.json()
            
            if result.get("duplicate"):
                print(_center_text("This file has already been added to this scan."))
            elif result.get("merged"):
                print(_center_text("Scan updated successfully!"))
            else:
                print(_center_text("Scan processed."))
        else:
             print(_center_text(f"API Error: {resp.status_code} - {resp.text}"))

    except Exception as e:
        print(_center_text(f"Request failed: {e}"))
    
    input(_center_text("Press Enter to continue..."))


def edit_contributor_resume_via_api(scan_id):
    """
    Allows editing contributor profile details (Name, Title, Summary, Projects) via API.
    """
    # Fetch contributors
    contributors = []
    try:
        resp = requests.get(f"{API_URL}/scans/{scan_id}")
        if resp.status_code == 200:
            data = resp.json().get("scan", {}).get("scan_data", {})
            profiles = data.get("contributor_profiles", {})
            contributors = sorted([c for c in profiles.keys() if not is_noise(c)])
    except Exception:
        pass
    
    if not contributors:
        print(_center_text("No contributors found."))
        return

    # Select contributor
    print()
    print(_center_text("Select contributor to edit:"))
    for i, c in enumerate(contributors, 1):
        print(_center_text(f"{i}. {c}"))
    
    sel = input(_center_text("Enter number (0 to back): ")).strip()
    if not sel.isdigit(): return
    idx = int(sel) - 1
    if idx < 0 or idx >= len(contributors): return
    
    contributor_id = contributors[idx]
    
    while True:
        # Refresh profile data
        profile = {}
        project_map = {}
        try:
            resp = requests.get(f"{API_URL}/scans/{scan_id}")
            if resp.status_code == 200:
                data = resp.json().get("scan", {}).get("scan_data", {})
                profile = data.get("contributor_profiles", {}).get(contributor_id, {})
                summaries = data.get("project_summaries", [])
                for p in summaries:
                    if p.get("project"):
                        project_map[p["project"]] = p
        except:
            pass

        print()
        print(_center_text(f"--- Editing {contributor_id} ---"))
        print(_center_text("1. Edit Name"))
        print(_center_text("2. Edit Professional Title"))
        print(_center_text("3. Edit Professional Summary"))
        print(_center_text("4. Edit Project Details (Desc/Skills)"))
        print(_center_text("5. Regenerate Resume"))
        print(_center_text("6. Reset Resume Changes"))
        print(_center_text("0. Back to Contributor List"))
        
        choice = input(_center_text("Choose option: ")).strip()
        
        if choice == "0": break
        
        def _update(payload):
            safe_cid = urllib.parse.quote(contributor_id, safe='')
            url = f"{API_URL}/scans/{scan_id}/contributors/{safe_cid}"
            try:
                r = requests.post(url, json=payload)
                if r.status_code == 200:
                    print(_center_text("Saved."))
                else:
                    print(_center_text(f"Error: {r.text}"))
            except Exception as e:
                print(_center_text(f"Connection error: {e}"))

        if choice == "1":
            curr = profile.get("custom_name", "")
            print(_center_text("Edit Name (type 'RESET' to restore default):"))
            val = _input_with_prefill(_center_text("Value: "), curr).strip()
            if val == "RESET": val = ""
            _update({"custom_name": val})
            
        elif choice == "2":
            curr = profile.get("custom_title", "")
            print(_center_text("Edit Title (type 'RESET' to restore default):"))
            val = _input_with_prefill(_center_text("Value: "), curr).strip()
            if val == "RESET": val = ""
            _update({"custom_title": val})

        elif choice == "3":
            curr = profile.get("custom_summary", "")
            print(_center_text("Edit Summary (type 'RESET' to restore default):"))
            val = _input_with_prefill(_center_text("Value: "), curr).strip()
            if val == "RESET": val = ""
            _update({"custom_summary": val})

        elif choice == "4":
            projects = profile.get("projects", [])
            if not projects:
                print(_center_text("No projects."))
                continue
            
            while True:
                print()
                print(_center_text(f"Projects for {contributor_id}:"))
                for i, p in enumerate(projects, 1):
                    marker = " *" if p.get("custom_description") or p.get("custom_skills") else ""
                    print(_center_text(f"{i}. {p.get('name')}{marker}"))
                
                psel = input(_center_text("Select project (0 to back): ")).strip()
                if not psel.isdigit(): continue
                pidx = int(psel) - 1
                if pidx < 0 or pidx >= len(projects): break
                
                target_p = projects[pidx]
                p_name = target_p.get("name")
                
                print()
                print(_center_text(f"--- Editing Project: {p_name} ---"))
                print(_center_text("1. Edit Description"))
                print(_center_text("2. Edit Skills"))
                print(_center_text("0. Back"))
                
                sub = input(_center_text("Choose: ")).strip()
                if sub == "0": continue
                
                if sub == "1":
                    curr = target_p.get("custom_description")
                    
                    # Generate default if no custom value exists
                    default_val = ""
                    p_context = project_map.get(p_name, {})
                    if p_context:
                        stats = dict(target_p)
                        if stats.get("files_worked", 0) == 0 and stats.get("files_list"):
                            stats["files_worked"] = len(stats["files_list"])
                        default_val = _build_personal_project_description(p_name, p_context, stats)
                    
                    print(_center_text("Edit Description (type 'RESET' to restore default):"))
                    val = _input_with_prefill(_center_text("Value: "), curr if curr else default_val).strip()
                    if val == "RESET": val = ""
                    _update({"project_updates": {p_name: {"custom_description": val}}})
                    # Optimistic update
                    if val: target_p["custom_description"] = val
                    else: target_p.pop("custom_description", None)

                elif sub == "2":
                    curr_list = target_p.get("custom_skills")
                    
                    # Get default skills if no custom value exists
                    default_skills = []
                    p_context = project_map.get(p_name, {})
                    if p_context:
                        pcs = p_context.get("per_contributor_skills", {})
                        default_skills = pcs.get(contributor_id, [])
                    
                    print(_center_text("Edit Skills (comma-separated, type 'RESET' to restore default):"))
                    val = _input_with_prefill(_center_text("Value: "), ", ".join(curr_list if curr_list is not None else default_skills)).strip()
                    
                    if val == "RESET":
                         _update({"project_updates": {p_name: {"reset_custom_skills": True}}})
                         target_p.pop("custom_skills", None)
                    else:
                         new_skills = [s.strip() for s in val.split(",") if s.strip()]
                         _update({"project_updates": {p_name: {"custom_skills": new_skills}}})
                         target_p["custom_skills"] = new_skills

        elif choice == "5":
            print(_center_text("Regenerating..."))
            payload = {
                "scan_id": scan_id,
                "contributor_id": contributor_id,
                "title": f"Resume - {contributor_id}"
            }
            try:
                r = requests.post(f"{API_URL}/resume/generate", json=payload)
                if r.status_code == 200:
                    rid = r.json().get("resume", {}).get("resume_id")
                    exp = requests.get(f"{API_URL}/resume/{rid}/export")
                    if exp.status_code == 200:
                        safe_title = "".join(c for c in payload["title"] if c.isalnum() or c in (' ', '_', '-')).strip()
                        filename = f"{safe_title}.docx"
                        out_dir = os.path.join(OUTPUT_DIR, "resumes")
                        os.makedirs(out_dir, exist_ok=True)
                        out_path = os.path.join(out_dir, filename)
                        with open(out_path, "wb") as f:
                            f.write(exp.content)
                        print(_center_text(f"Saved to: {out_path}"))
                    else:
                        print(_center_text("Export failed."))
                else:
                    print(_center_text("Generation failed."))
            except Exception as e:
                print(_center_text(f"Error: {e}"))
            input(_center_text("Press Enter..."))

        elif choice == "6":
            if get_yes_no(f"Discard ALL manual edits for {contributor_id}?"):
                _update({"reset_profile": True})


def edit_portfolio_via_api(scan_id):
    """
    Allows editing portfolio settings (Showcase selection, descriptions) via API.
    """
    # Fetch contributors
    contributors = []
    try:
        resp = requests.get(f"{API_URL}/scans/{scan_id}")
        if resp.status_code == 200:
            data = resp.json().get("scan", {}).get("scan_data", {})
            profiles = data.get("contributor_profiles", {})
            contributors = sorted([c for c in profiles.keys() if not is_noise(c)])
    except Exception:
        pass
    
    if not contributors:
        print(_center_text("No contributors found."))
        return

    # Select contributor
    print()
    print(_center_text("Select contributor to customize portfolio:"))
    for i, c in enumerate(contributors, 1):
        print(_center_text(f"{i}. {c}"))
    
    sel = input(_center_text("Enter number (0 to back): ")).strip()
    if not sel.isdigit(): return
    idx = int(sel) - 1
    if idx < 0 or idx >= len(contributors): return
    
    contributor_id = contributors[idx]

    # Fetch all projects to filter by contributor
    all_projects = []
    try:
        p_resp = requests.get(f"{API_URL}/projects", params={"scan_id": scan_id})
        if p_resp.status_code == 200:
            all_projects = p_resp.json().get("projects", [])
    except:
        pass

    user_projects = []
    for p in all_projects:
        pcts = p.get("data", {}).get("per_contributor_pct", {})
        if pcts.get(contributor_id, 0) > 0:
            user_projects.append(p)
    
    if not user_projects:
        print(_center_text("No projects found for this contributor."))
        return

    while True:
        print()
        print(_center_text(f"--- Portfolio Showcase: {contributor_id} ---"))
        print(_center_text("1. Select Projects for Showcase"))
        print(_center_text("2. Edit Portfolio Details"))
        print(_center_text("3. Regenerate Portfolio"))
        print(_center_text("0. Back to Contributor List"))
        
        choice = input(_center_text("Choose option: ")).strip()
        
        if choice == "0": break
        
        if choice == "1":
            while True:
                print()
                print(_center_text(f"--- Select Projects: {contributor_id} ---"))
                print(_center_text("(Projects marked [x] will appear in the portfolio)"))
                
                for i, p in enumerate(user_projects, 1):
                    cust = p.get("customization", {})
                    is_showcase = cust.get("selected_for_showcase")
                    # Default to included if not explicitly False
                    mark = "[x]" if is_showcase is not False else "[ ]"
                    p_name = p.get("project_name", "Unknown")
                    print(_center_text(f"{i}. {mark} {p_name}"))
                
                print()
                print(_center_text("Type number to toggle selection (0 to back)."))
                sel = input(_center_text("Select: ")).strip()
                if sel == "0": break
                
                if sel.isdigit():
                    pidx = int(sel) - 1
                    if 0 <= pidx < len(user_projects):
                        target = user_projects[pidx]
                        pid = target["project_id"]
                        curr = target.get("customization", {}).get("selected_for_showcase")
                        new_val = True if curr is False else False
                        
                        try:
                            r = requests.post(f"{API_URL}/projects/{pid}/edit", json={"selected_for_showcase": new_val})
                            if r.status_code == 200:
                                target["customization"] = r.json().get("customization", {})
                        except:
                            pass

        elif choice == "2":
            while True:
                print()
                print(_center_text(f"--- Edit Portfolio Details: {contributor_id} ---"))
                for i, p in enumerate(user_projects, 1):
                    p_name = p.get("project_name", "Unknown")
                    cust = p.get("customization", {})
                    has_custom = " *" if (cust.get("custom_portfolio_project_description") or cust.get("custom_portfolio_description") or cust.get("custom_portfolio_tech_stack")) else ""
                    print(_center_text(f"{i}. {p_name}{has_custom}"))
                
                sel = input(_center_text("Select project to edit (0 to back): ")).strip()
                if sel == "0": break
                
                if sel.isdigit():
                    pidx = int(sel) - 1
                    if 0 <= pidx < len(user_projects):
                        target = user_projects[pidx]
                        pid = target["project_id"]
                        p_name = target.get("project_name")
                        
                        while True:
                            cust = target.get("customization", {})
                            print()
                            print(_center_text(f"--- Editing: {p_name} ---"))
                            print(_center_text("1. Description (General)"))
                            print(_center_text("2. Role / Contribution"))
                            print(_center_text("3. Tech Stack"))
                            print(_center_text("4. Upload Thumbnail"))
                            print(_center_text("0. Back"))
                            
                            sub = input(_center_text("Choose: ")).strip()
                            if sub == "0": break
                            
                            payload = {}
                            if sub == "1":
                                curr = cust.get("custom_portfolio_project_description", "")
                                print(_center_text("Edit Project Description (General) [Type 'RESET' to restore default]:"))
                                val = _input_with_prefill(_center_text("Value: "), curr).strip()
                                if val == "RESET": payload["custom_portfolio_project_description"] = ""
                                elif val: payload["custom_portfolio_project_description"] = val
                                else: continue
                                
                            elif sub == "2":
                                curr = cust.get("custom_portfolio_description")
                                # Generate default if not set
                                default_val = ""
                                pct = target.get("data", {}).get("per_contributor_pct", {}).get(contributor_id, 0)
                                default_val = f"{pct:.1f}% of codebase"

                                print(_center_text("Edit Role/Contribution [Type 'RESET' to restore default]:"))
                                val = _input_with_prefill(_center_text("Value: "), curr if curr else default_val).strip()
                                if val == "RESET": payload["custom_portfolio_description"] = ""
                                elif val: payload["custom_portfolio_description"] = val
                                else: continue

                            elif sub == "3":
                                curr_list = cust.get("custom_portfolio_tech_stack")
                                # Generate default if not set
                                default_list = _get_default_tech_stack(target.get("data", {}), contributor_id)
                                curr_str = ", ".join(curr_list) if curr_list else ", ".join(default_list)

                                print(_center_text("Edit Tech Stack (comma separated) [Type 'RESET' to restore default]:"))
                                val = _input_with_prefill(_center_text("Value: "), curr_str).strip()
                                if val == "RESET": payload["custom_portfolio_tech_stack"] = []
                                elif val: payload["custom_portfolio_tech_stack"] = [s.strip() for s in val.split(",") if s.strip()]
                                else: continue
                            
                            elif sub == "4":
                                print(_center_text("Enter path to image file:"))
                                fpath = input(_center_text("> ")).strip().strip('"').strip("'")
                                if os.path.isfile(fpath):
                                    try:
                                        with open(fpath, "rb") as f:
                                            url = f"{API_URL}/projects/{pid}/thumbnail"
                                            r = requests.post(url, files={"file": f})
                                            if r.status_code == 200:
                                                print(_center_text("Thumbnail uploaded."))
                                                target["customization"] = r.json().get("customization", {})
                                            else:
                                                print(_center_text(f"Error: {r.text}"))
                                    except Exception as e:
                                        print(_center_text(f"Error: {e}"))
                                else:
                                    print(_center_text("File not found."))
                                continue

                            if payload:
                                try:
                                    r = requests.post(f"{API_URL}/projects/{pid}/edit", json=payload)
                                    if r.status_code == 200:
                                        print(_center_text("Saved."))
                                        target["customization"] = r.json().get("customization", {})
                                    else:
                                        print(_center_text(f"Error: {r.text}"))
                                except Exception as e:
                                    print(_center_text(f"Error: {e}"))

        elif choice == "3":
            print(_center_text("Regenerating Portfolio..."))
            gen_payload = {
                "scan_id": scan_id,
                "contributor_id": contributor_id,
                "title": f"Portfolio - {contributor_id}"
            }
            try:
                r = requests.post(f"{API_URL}/portfolio/generate", json=gen_payload)
                if r.status_code == 200:
                    pid = r.json().get("portfolio", {}).get("portfolio_id")
                    exp = requests.get(f"{API_URL}/portfolio/{pid}/export")
                    if exp.status_code == 200:
                        safe_title = "".join(c for c in payload["title"] if c.isalnum() or c in (' ', '_', '-')).strip()
                        filename = f"{safe_title}.md"
                        out_dir = os.path.join(OUTPUT_DIR, "portfolios")
                        os.makedirs(out_dir, exist_ok=True)
                        out_path = os.path.join(out_dir, filename)
                        with open(out_path, "wb") as f:
                            f.write(exp.content)
                        print(_center_text(f"Saved to: {out_path}"))
                    else:
                        print(_center_text("Export failed."))
                else:
                    print(_center_text("Generation failed."))
            except Exception as e:
                print(_center_text(f"Error: {e}"))
            input(_center_text("Press Enter..."))


def generate_artifacts_via_api():
    """Generates Resume or Portfolio artifacts via API."""
    scans = _fetch_scans()
    if not scans:
        print(_center_text("No scans found."))
        return

    print()
    print(_center_text("Select a scan to generate from:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        return
    
    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        return

    scan_id = scans[idx]["summary_id"]

    # Fetch full scan details to get contributors
    contributors = []
    try:
        resp = requests.get(f"{API_URL}/scans/{scan_id}")
        if resp.status_code == 200:
            data = resp.json().get("scan", {}).get("scan_data", {})
            profiles = data.get("contributor_profiles", {})
            contributors = sorted([c for c in profiles.keys() if not is_noise(c)])
    except Exception:
        pass

    while True:
        sub = _print_menu("GENERATION OPTIONS", [
            ("1", "Full Project Resume"),
            ("2", "Contributor Resume (Word)"),
            ("3", "Contributor Portfolio (Markdown)"),
            ("4", "Edit Resume"),
            ("5", "Edit Portfolio"),
            ("0", "Back")
        ])
        
        if sub == "0":
            break
        
        endpoint = ""
        key = ""
        payload = {"scan_id": scan_id}

        if sub == "1":
            endpoint = "/resume/generate"
            key = "resume"
        
        elif sub in ("2", "3"):
            if not contributors:
                print(_center_text("No valid contributors found in this scan."))
                input(_center_text("Press Enter..."))
                continue
            
            print()
            print(_center_text("Select contributor:"))
            for i, c in enumerate(contributors, 1):
                print(_center_text(f"{i}. {c}"))
            
            sel = input(_center_text("Enter number (0 to back): ")).strip()
            if not sel.isdigit():
                continue
            c_idx = int(sel) - 1
            if c_idx < 0 or c_idx >= len(contributors):
                continue
            
            payload["contributor_id"] = contributors[c_idx]
            
            if sub == "2":
                endpoint = "/resume/generate"
                key = "resume"
            else:
                endpoint = "/portfolio/generate"
                key = "portfolio"

        elif sub == "4":
            edit_contributor_resume_via_api(scan_id)
            continue
        elif sub == "5":
             edit_portfolio_via_api(scan_id)
             continue

        if endpoint:
            default_title = f"Project Portfolio {key.capitalize()}"
            if payload.get("contributor_id"):
                cleanName = payload["contributor_id"]
                if "@" in cleanName:
                    cleanName = cleanName.split("@")[0].replace(".", " ").replace("_", " ").title()
                default_title = f"{cleanName} {key.capitalize()}"
            
            print(_center_text(f"Generating {key} as '{default_title}'..."))
            payload["title"] = default_title

            try:
                resp = requests.post(f"{API_URL}{endpoint}", json=payload)
                if resp.status_code == 200:
                    data = resp.json().get(key, {})
                    art_id = data.get(f"{key}_id")

                    if key == "resume":
                        try:
                            export_resp = requests.get(f"{API_URL}/resume/{art_id}/export")
                            if export_resp.status_code == 200:
                                safe_title = "".join(c for c in payload["title"] if c.isalnum() or c in (' ', '_', '-')).strip()
                                filename = f"{safe_title}.docx"
                                out_dir = os.path.join(OUTPUT_DIR, "resumes")
                                os.makedirs(out_dir, exist_ok=True)
                                out_path = os.path.join(out_dir, filename)
                                with open(out_path, "wb") as f:
                                    f.write(export_resp.content)
                                print(_center_text(f"Saved to: {out_path}"))
                            else:
                                print(_center_text(f"Export failed: {export_resp.text}"))
                        except Exception as ex:
                            print(_center_text(f"Download error: {ex}"))
                    
                    elif key == "portfolio":
                        print(_center_text(f"Exporting portfolio '{payload['title']}'..."))
                        try:
                            export_resp = requests.get(f"{API_URL}/portfolio/{art_id}/export")
                            if export_resp.status_code == 200:
                                safe_title = "".join(c for c in payload["title"] if c.isalnum() or c in (' ', '_', '-')).strip()
                                filename = f"{safe_title}.md"
                                out_dir = os.path.join(OUTPUT_DIR, "portfolios")
                                os.makedirs(out_dir, exist_ok=True)
                                out_path = os.path.join(out_dir, filename)
                                with open(out_path, "wb") as f:
                                    f.write(export_resp.content)
                                print(_center_text(f"Saved to: {out_path}"))
                            else:
                                print(_center_text(f"Export failed: {export_resp.text}"))
                        except Exception as ex:
                            print(_center_text(f"Download error: {ex}"))
                else:
                    print(_center_text(f"Error: {resp.text}"))
            except Exception as e:
                print(_center_text(f"Request failed: {e}"))
            input(_center_text("Press Enter..."))


def delete_scan_via_api():
    """Lists scans and deletes selected one."""
    scans = _fetch_scans()
    if not scans:
        print(_center_text("No scans found."))
        return

    print()
    print(_center_text("Select a scan to delete:"))
    print_scan_list(scans)

    choice = input(_center_text("Enter number (0 to cancel): ")).strip()
    if not choice.isdigit() or int(choice) == 0:
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(scans):
        return

    scan = scans[idx]
    if get_yes_no(f"Are you sure you want to delete scan {scan['summary_id']}?"):
        try:
            resp = requests.delete(f"{API_URL}/scans/{scan['summary_id']}")
            if resp.status_code == 200:
                print(_center_text("Scan deleted."))
            else:
                print(_center_text("Failed to delete scan."))
        except Exception as e:
            print(_center_text(f"Error: {e}"))
    else:
        print(_center_text("Deletion canceled."))
    
    input(_center_text("Press Enter..."))


def scan_manager_via_api():
    """Submenu for managing scans via API."""
    while True:
        sub_choice = _print_menu(
            "SCAN MANAGER (API)",
            [
                ("0", "Return to home screen"),
                ("1", "View stored project analyses"),
                ("2", "Update an existing scan"),
                ("3", "Generate Resume/Portfolio"),
                ("4", "Delete stored scans"),
            ],
            prompt="Choose an option (0-4): "
        )
        if sub_choice == "1": view_full_scan_details_via_api()
        elif sub_choice == "2": update_scan_via_api()
        elif sub_choice == "3": generate_artifacts_via_api()
        elif sub_choice == "4": delete_scan_via_api()
        elif sub_choice == "0": break


def initialize_app():
    """
    Application startup routine:
    - Checks API connection.
    - Displays welcome banner.
    - Checks/Sets privacy consent via API.
    - Returns the user's initial menu choice.
    """
    if not check_api_connection():
        sys.exit(1)

    print()
    print(_center_text("~~~~~~~~~~~~~~~~~~~~~~~"))
    print(_center_text("Welcome to Skill Scope!"))
    print(_center_text("~~~~~~~~~~~~~~~~~~~~~~~"))
    print()
    intro_lines = [
        "Skill Scope scans a project folder to summarize languages, frameworks,",
        "timelines, and contributions, then saves the results for later review.",
        "",
        "1) Run a new scan: choose files and an analysis mode to generate a report.",
        "2) Scan Manager: view previous scans, generate resumes/portfolios, or delete scans.",
        "3) Quit: exit the program.",
    ]
    for line in intro_lines:
        print(_center_text(line))
    print()
    initial_choice = input(_center_text("Choose an option (1-3): ")).strip()

    if initial_choice == "3":
        return initial_choice

    # Check if privacy consent is already set on the server; if not, ask locally.
    try:
        resp = requests.get(f"{API_URL}/privacy-consent")
        if resp.status_code == 200:
            settings = resp.json().get("privacy", {})
            if not settings.get("consent"):
                # Ask for consent locally if not set on server
                if not get_user_consent():
                    sys.exit(0)
                # Update API
                requests.post(f"{API_URL}/privacy-consent", json={"consent": True})
    except Exception:
        # If API check fails here, we proceed; check_api_connection already warned if down.
        pass

    return initial_choice


def home_screen(initial_choice=None):
    """Main application loop handling the top-level menu navigation."""
    pending_choice = initial_choice
    while True:
        if pending_choice is None:
            choice = _print_menu(
                "SKILL SCOPE HOME",
                [
                    ("1", "Run a new scan: choose files and an analysis mode to generate a report."),
                    ("2", "Scan Manager: view previous scans, generate resumes/portfolios, or delete scans."),
                    ("3", "Quit: exit the program."),
                ],
                prompt="Choose an option (1-3): ",
            )
        else:
            choice = pending_choice
            pending_choice = None

        if choice == "1":
            run_new_scan_via_api()
        elif choice == "2":
            scan_manager_via_api()
        elif choice == "3":
            print(_center_text("Goodbye!"))
            break
        else:
            print(_center_text("Invalid input. Try again."))


if __name__ == "__main__":
    try:
        choice = initialize_app()
        home_screen(initial_choice=choice)
    except KeyboardInterrupt:
        print()
        print(_center_text("Goodbye!"))
