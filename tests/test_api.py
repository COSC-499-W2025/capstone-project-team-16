import io
from copy import deepcopy

import api
from fastapi.testclient import TestClient


def _sample_analysis_results(project_suffix="A", zip_hash=None):
    payload = {
        "project_summaries": [
            {
                "project": f"Alpha-{project_suffix}",
                "skills": ["Python", "Testing"],
                "frameworks": ["FastAPI"],
                "languages": ["Python"],
                "score": 90,
                "project_type": "collaborative",
            },
            {
                "project": f"Beta-{project_suffix}",
                "skills": ["Docs"],
                "frameworks": [],
                "languages": ["Markdown"],
                "score": 50,
                "project_type": "individual",
            },
        ],
        "resume_summaries": [],
        "skills_chronological": [],
        "projects_chronological": [],
        "contributor_profiles": {},
    }
    if zip_hash:
        payload["zip_hash"] = zip_hash
    return payload


def _install_fake_backend(monkeypatch):
    state = {
        "privacy": {
            "consent": False,
            "external_services_allowed": False,
            "notes": "",
            "updated_at": None,
        },
        "scans": {},
        "scan_hashes": set(),
        "project_custom": {},
        "resumes": {},
        "portfolios": {},
        "next_scan_id": 1,
        "next_resume_id": 1,
        "next_portfolio_id": 1,
    }

    def list_full_scans():
        rows = []
        for sid, scan in sorted(state["scans"].items(), reverse=True):
            rows.append(
                {
                    "summary_id": sid,
                    "timestamp": scan["timestamp"],
                    "analysis_mode": scan["analysis_mode"],
                }
            )
        return rows

    def get_full_scan_by_id(summary_id):
        scan = state["scans"].get(summary_id)
        return deepcopy(scan) if scan else None

    def delete_full_scan_by_id(summary_id):
        return state["scans"].pop(summary_id, None) is not None

    def save_full_scan(results, analysis_mode, consent):
        sid = state["next_scan_id"]
        state["next_scan_id"] += 1
        scan_data = deepcopy(results)
        scan_data.setdefault("source_hashes", [])
        if scan_data.get("zip_hash"):
            scan_data["source_hashes"] = [scan_data["zip_hash"]]
            state["scan_hashes"].add(scan_data["zip_hash"])
        state["scans"][sid] = {
            "summary_id": sid,
            "timestamp": f"t{sid}",
            "analysis_mode": analysis_mode,
            "user_consent": "Yes" if consent else "No",
            "scan_data": scan_data,
        }
        return sid

    def update_full_scan(summary_id, merged_data):
        if summary_id not in state["scans"]:
            return
        state["scans"][summary_id]["scan_data"] = deepcopy(merged_data)
        for h in merged_data.get("source_hashes", []):
            state["scan_hashes"].add(h)

    def scan_exists(zip_hash):
        return zip_hash in state["scan_hashes"]

    def get_project_customization(project_id):
        return deepcopy(state["project_custom"].get(project_id, {}))

    def upsert_project_customization(project_id, patch):
        current = state["project_custom"].get(project_id, {})
        current.update(deepcopy(patch))
        current["updated_at"] = "now"
        state["project_custom"][project_id] = current
        return deepcopy(current)

    def set_privacy_settings(settings):
        saved = deepcopy(settings)
        saved["updated_at"] = "now"
        state["privacy"] = saved
        return deepcopy(saved)

    def get_privacy_settings():
        return deepcopy(state["privacy"])

    def create_resume_artifact(data, scan_summary_id=None, title=None):
        rid = state["next_resume_id"]
        state["next_resume_id"] += 1
        artifact = {
            "resume_id": rid,
            "scan_summary_id": scan_summary_id,
            "title": title,
            "data": deepcopy(data),
            "created_at": "now",
            "updated_at": "now",
        }
        state["resumes"][rid] = artifact
        return deepcopy(artifact)

    def get_resume_artifact(resume_id):
        artifact = state["resumes"].get(resume_id)
        return deepcopy(artifact) if artifact else None

    def update_resume_artifact(resume_id, patch):
        artifact = state["resumes"].get(resume_id)
        if not artifact:
            return None
        if "title" in patch:
            artifact["title"] = patch["title"]
        artifact["data"].update({k: deepcopy(v) for k, v in patch.items() if k != "title"})
        artifact["updated_at"] = "now2"
        return deepcopy(artifact)

    def create_portfolio_artifact(data, scan_summary_id=None, title=None):
        pid = state["next_portfolio_id"]
        state["next_portfolio_id"] += 1
        artifact = {
            "portfolio_id": pid,
            "scan_summary_id": scan_summary_id,
            "title": title,
            "data": deepcopy(data),
            "created_at": "now",
            "updated_at": "now",
        }
        state["portfolios"][pid] = artifact
        return deepcopy(artifact)

    def get_portfolio_artifact(portfolio_id):
        artifact = state["portfolios"].get(portfolio_id)
        return deepcopy(artifact) if artifact else None

    def update_portfolio_artifact(portfolio_id, patch):
        artifact = state["portfolios"].get(portfolio_id)
        if not artifact:
            return None
        if "title" in patch:
            artifact["title"] = patch["title"]
        artifact["data"].update({k: deepcopy(v) for k, v in patch.items() if k != "title"})
        artifact["updated_at"] = "now2"
        return deepcopy(artifact)

    def check_file_validity(_zip_path):
        return ([{"filename": "/tmp/file.py", "isFile": True}], "ziphash-1")

    def analyze_scan(file_list, analysis_mode, advanced_options):
        assert isinstance(file_list, list)
        assert analysis_mode in {"basic", "advanced"}
        assert isinstance(advanced_options, dict)
        return _sample_analysis_results(project_suffix="Upload")

    def merge_scans(existing_data, new_data):
        merged = deepcopy(existing_data)
        merged["project_summaries"] = list(merged.get("project_summaries", [])) + list(
            new_data.get("project_summaries", [])
        )
        hashes = set(merged.get("source_hashes", []))
        hashes.update(new_data.get("source_hashes", []))
        merged["source_hashes"] = sorted(hashes)
        return merged

    for name, fn in {
        "list_full_scans": list_full_scans,
        "get_full_scan_by_id": get_full_scan_by_id,
        "delete_full_scan_by_id": delete_full_scan_by_id,
        "save_full_scan": save_full_scan,
        "update_full_scan": update_full_scan,
        "scan_exists": scan_exists,
        "get_project_customization": get_project_customization,
        "upsert_project_customization": upsert_project_customization,
        "set_privacy_settings": set_privacy_settings,
        "get_privacy_settings": get_privacy_settings,
        "create_resume_artifact": create_resume_artifact,
        "get_resume_artifact": get_resume_artifact,
        "update_resume_artifact": update_resume_artifact,
        "create_portfolio_artifact": create_portfolio_artifact,
        "get_portfolio_artifact": get_portfolio_artifact,
        "update_portfolio_artifact": update_portfolio_artifact,
        "_check_file_validity": check_file_validity,
        "_analyze_scan": analyze_scan,
        "_merge_scans": merge_scans,
    }.items():
        monkeypatch.setattr(api, name, fn)

    return state


def _client(monkeypatch):
    state = _install_fake_backend(monkeypatch)
    app = api.create_app()
    return TestClient(app), state


def test_health_endpoint(monkeypatch):
    client, _state = _client(monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_privacy_consent_and_get(monkeypatch):
    client, _state = _client(monkeypatch)
    response = client.post(
        "/privacy-consent",
        json={"consent": True, "external_services_allowed": False, "notes": "local only"},
    )
    assert response.status_code == 200
    assert response.json()["privacy"]["consent"] is True

    response = client.get("/privacy-consent")
    assert response.status_code == 200
    assert response.json()["privacy"]["notes"] == "local only"


def test_projects_upload_persists_and_lists_projects(monkeypatch):
    client, state = _client(monkeypatch)

    response = client.post(
        "/projects/upload",
        json={
            "zip_path": "/tmp/sample.zip",
            "analysis_mode": "advanced",
            "advanced_options": {"framework_scan": False},
            "consent": True,
            "persist": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["summary_id"] == 1
    assert body["duplicate"] is False
    assert len(body["projects"]) == 2
    assert "ziphash-1" in state["scan_hashes"]

    list_resp = client.get("/projects")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["projects"]) == 2


def test_projects_upload_recognizes_duplicate_and_skips_new_persist(monkeypatch):
    client, state = _client(monkeypatch)
    state["scan_hashes"].add("ziphash-1")

    response = client.post("/projects/upload", json={"zip_path": "/tmp/sample.zip"})
    assert response.status_code == 200
    body = response.json()
    assert body["duplicate"] is True
    assert body["summary_id"] is None


def test_projects_upload_incremental_merge_same_scan(monkeypatch):
    client, state = _client(monkeypatch)
    # Seed existing scan.
    seed_id = api.save_full_scan(_sample_analysis_results(project_suffix="Seed", zip_hash="seedhash"), "basic", True)
    assert seed_id == 1

    def check_file_validity(_zip_path):
        return ([{"filename": "/tmp/file2.py", "isFile": True}], "ziphash-2")

    monkeypatch.setattr(api, "_check_file_validity", check_file_validity)

    response = client.post(
        "/projects/upload",
        json={"zip_path": "/tmp/new.zip", "incremental": True, "existing_scan_id": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["merged"] is True
    assert body["summary_id"] == 1
    assert len(state["scans"][1]["scan_data"]["project_summaries"]) == 4
    assert "ziphash-2" in state["scans"][1]["scan_data"]["source_hashes"]


def test_projects_edit_and_get_project_applies_customizations(monkeypatch):
    client, _state = _client(monkeypatch)
    client.post("/projects/upload", json={"zip_path": "/tmp/sample.zip"})

    edit_resp = client.post(
        "/projects/1:0/edit",
        json={
            "ranking": 10,
            "role": "Backend Developer",
            "evidence_of_success": {"metric": "latency", "value": "-35%"},
            "thumbnail": "/images/alpha.png",
            "portfolio_showcase_text": "Custom portfolio wording",
            "resume_wording": "Custom resume bullet",
            "selected_for_showcase": True,
            "highlighted_skills": ["FastAPI", "SQLite"],
        },
    )
    assert edit_resp.status_code == 200

    get_resp = client.get("/projects/1:0")
    assert get_resp.status_code == 200
    project = get_resp.json()["project"]
    assert project["role"] == "Backend Developer"
    assert project["thumbnail"] == "/images/alpha.png"
    assert project["resume_wording"] == "Custom resume bullet"


def test_get_skills_aggregates_across_projects(monkeypatch):
    client, _state = _client(monkeypatch)
    client.post("/projects/upload", json={"zip_path": "/tmp/sample.zip"})

    response = client.get("/skills")
    assert response.status_code == 200
    skills = response.json()["skills"]
    assert any(s["skill"] == "Python" for s in skills)


def test_resume_generate_get_and_edit(monkeypatch):
    client, _state = _client(monkeypatch)
    client.post("/projects/upload", json={"zip_path": "/tmp/sample.zip"})

    gen_resp = client.post("/resume/generate", json={"scan_id": 1, "title": "My Resume"})
    assert gen_resp.status_code == 200
    resume = gen_resp.json()["resume"]
    assert resume["resume_id"] == 1
    assert len(resume["data"]["items"]) == 2

    get_resp = client.get("/resume/1")
    assert get_resp.status_code == 200
    assert get_resp.json()["resume"]["title"] == "My Resume"

    edit_resp = client.post(
        "/resume/1/edit",
        json={
            "title": "Resume v2",
            "project_wording_edits": {"1:0": "Built and optimized backend API services."},
            "selected_project_ids": ["1:0"],
            "project_order": ["1:0"],
        },
    )
    assert edit_resp.status_code == 200
    edited = edit_resp.json()["resume"]
    assert edited["title"] == "Resume v2"
    assert len(edited["data"]["items"]) == 1
    assert edited["data"]["items"][0]["text"] == "Built and optimized backend API services."


def test_portfolio_generate_get_and_edit_with_project_customizations(monkeypatch):
    client, _state = _client(monkeypatch)
    client.post("/projects/upload", json={"zip_path": "/tmp/sample.zip"})

    gen_resp = client.post("/portfolio/generate", json={"scan_id": 1, "title": "My Portfolio"})
    assert gen_resp.status_code == 200
    portfolio = gen_resp.json()["portfolio"]
    assert portfolio["portfolio_id"] == 1
    assert len(portfolio["data"]["items"]) >= 1

    edit_resp = client.post(
        "/portfolio/1/edit",
        json={
            "title": "Portfolio v2",
            "project_edits": {
                "1:0": {
                    "role": "Lead Engineer",
                    "evidence_of_success": "Improved completion rate by 20%",
                    "thumbnail": "/thumbs/alpha.png",
                    "portfolio_showcase_text": "Feature-rich showcase text",
                    "comparison_attributes": {"difficulty": "high", "impact": "high"},
                }
            },
            "selected_project_ids": ["1:0"],
            "project_order": ["1:0"],
        },
    )
    assert edit_resp.status_code == 200
    updated = edit_resp.json()["portfolio"]
    assert updated["title"] == "Portfolio v2"
    assert len(updated["data"]["items"]) == 1
    item = updated["data"]["items"][0]
    assert item["role"] == "Lead Engineer"
    assert item["thumbnail"] == "/thumbs/alpha.png"
    assert item["text"] == "Feature-rich showcase text"

    get_resp = client.get("/portfolio/1")
    assert get_resp.status_code == 200
    assert get_resp.json()["portfolio"]["title"] == "Portfolio v2"


def test_legacy_scans_endpoints_still_work(monkeypatch):
    client, _state = _client(monkeypatch)

    create_resp = client.post(
        "/scans",
        json={"zip_path": "/tmp/sample.zip", "analysis_mode": "basic", "persist": True},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["summary_id"] == 1

    list_resp = client.get("/scans")
    assert list_resp.status_code == 200
    assert list_resp.json()["scans"][0]["summary_id"] == 1

    get_resp = client.get("/scans/1")
    assert get_resp.status_code == 200
    assert get_resp.json()["scan"]["summary_id"] == 1

    delete_resp = client.delete("/scans/1")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True


def test_invalid_upload_input_returns_400(monkeypatch):
    client, _state = _client(monkeypatch)
    response = client.post("/projects/upload", json={})
    assert response.status_code == 400
    assert response.json()["error"] == "zip file or zip_path is required"


def test_multipart_upload_supported(monkeypatch):
    client, _state = _client(monkeypatch)
    response = client.post(
        "/projects/upload",
        data={
            "analysis_mode": "advanced",
            "advanced_options": '{"framework_scan": false}',
            "persist": "true",
            "consent": "true",
        },
        files={"zip": ("demo.zip", io.BytesIO(b"fake zip bytes"), "application/zip")},
    )
    assert response.status_code == 201
    assert response.json()["analysis_mode"] == "advanced"
