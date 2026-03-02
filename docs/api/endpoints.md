# Skill Scope API Endpoints (Milestone API)

This document describes the FastAPI endpoints in `src/api.py`.

## Base Notes

- Framework: `FastAPI`
- Auto docs (when running the API): `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- Error format: `{"error": "..."}`
- Legacy scan endpoints (`/scans*`) are kept for compatibility

## Project Upload and Scan Ingestion

### `POST /projects/upload`

Uploads a zip file (multipart) or references a local zip path (JSON), runs analysis, optionally persists results, supports duplicate detection and incremental merge.

Accepted input (JSON or multipart form):

- `zip` (multipart file, optional if `zip_path` provided)
- `zip_path` (string, optional if `zip` provided)
- `analysis_mode` (`basic` or `advanced`, default `basic`)
- `advanced_options` (JSON object or JSON string in multipart)
- `consent` (bool-like, optional)
- `persist` (bool-like, default `true`)
- `allow_duplicate` (bool-like, default `false`)
- `incremental` (bool-like, default `false`)
- `existing_scan_id` (int, used when `incremental=true`)
- `portfolio_id` (int, optional incremental target via saved portfolio)
- `resume_id` (int, optional incremental target via saved resume)

Behavior:

- Recognizes duplicate uploads using zip hash and avoids duplicate persistence by default
- Supports incremental merge into an existing saved scan (`existing_scan_id`, `portfolio_id`, or `resume_id`)
- Returns project summaries with synthetic project IDs in `<scan_id>:<index>` format

Example JSON:

```json
{
  "zip_path": "input/test-data/multi_project_test_data.zip",
  "analysis_mode": "advanced",
  "advanced_options": {"framework_scan": true},
  "consent": true,
  "persist": true
}
```

Example response (201 / 200):

```json
{
  "analysis_mode": "advanced",
  "persisted": true,
  "duplicate": false,
  "incremental": false,
  "merged": false,
  "summary_id": 12,
  "projects": [
    {"project_id": "12:0", "project_name": "code_collab_proj", "...": "..."}
  ],
  "results": {"project_summaries": []}
}
```

### Legacy `POST /scans`

Compatibility endpoint for existing scan flow. Same ingest behavior as `POST /projects/upload`, returns legacy-style fields plus `summary_id` and duplicate flags.

### `GET /scans`

Returns saved scan summaries:

```json
{"scans": [{"summary_id": 1, "timestamp": "...", "analysis_mode": "basic"}]}
```

### `GET /scans/{summary_id}`

Returns a full saved scan payload (including parsed `scan_data` JSON).

### `DELETE /scans/{summary_id}`

Deletes a saved scan record.

## Privacy

### `POST /privacy-consent`

Stores API-level privacy/consent settings.

Request:

```json
{
  "consent": true,
  "external_services_allowed": false,
  "notes": "Local analysis only"
}
```

Response:

```json
{"privacy": {"consent": true, "external_services_allowed": false, "notes": "Local analysis only", "updated_at": "..."}}
```

### `GET /privacy-consent`

Returns the saved privacy settings.

## Projects and Skills

### `GET /projects`

Lists all discovered projects across saved scans (or filtered by `scan_id` query parameter).

Query params:

- `scan_id` (optional int)

Returns project entries with:

- `project_id` (`<scan_id>:<index>`)
- `project_name`
- `skills`, `frameworks`, `languages`
- `score`, `project_type`
- `customization` (saved user edits)
- flattened customization fields (e.g., `role`, `thumbnail`, `resume_wording`)

### `GET /projects/{project_id}`

Returns one project record (with customizations applied).

Example `project_id`: `3:0`

### `POST /projects/{project_id}/edit` (additional endpoint)

Saves project-level customization fields used by resume and portfolio generation/editing.

Supported fields:

- `ranking`
- `chronology_correction`
- `comparison_attributes`
- `highlighted_skills`
- `selected_for_showcase`
- `role`
- `evidence_of_success`
- `thumbnail`
- `portfolio_showcase_text`
- `resume_wording`

This endpoint enables:

- choosing which info is represented
- re-ranking/reordering hints
- chronology corrections
- role/evidence capture
- thumbnail association
- saved wording for portfolio/resume uses

### `GET /skills`

Aggregates skills from saved projects (uses highlighted skills when present).

Query params:

- `scan_id` (optional int)

Response:

```json
{"skills": [{"skill": "Python", "project_count": 3}]}
```

## Resume Endpoints

### `POST /resume/generate`

Generates and saves a résumé artifact from selected projects or a scan.

Request fields:

- `scan_id` (optional)
- `project_ids` (optional list of `<scan_id>:<index>`)
- `title`
- `selected_project_ids` (optional filter)
- `project_order` (optional explicit ordering)

The saved artifact contains textual résumé items, which can be edited later.

### `GET /resume/{resume_id}`

Returns the saved résumé artifact and its textual items.

### `POST /resume/{resume_id}/edit`

Edits a saved résumé artifact and/or saves project-specific wording overrides.

Supported fields:

- `title`
- `items` (replace item list directly)
- `selected_project_ids`
- `project_order`
- `project_wording_edits` (map of `project_id -> text`)

`project_wording_edits` also persists project-level `resume_wording`.

## Portfolio Endpoints

### `POST /portfolio/generate`

Generates and saves a portfolio artifact from selected projects or a scan.

Request fields:

- `scan_id` (optional)
- `project_ids` (optional list)
- `title`
- `selected_project_ids`
- `project_order`

Portfolio items include textual showcase content plus role/evidence/thumbnail fields when available.

### `GET /portfolio/{portfolio_id}`

Returns the saved portfolio artifact and textual showcase items.

### `POST /portfolio/{portfolio_id}/edit`

Edits a saved portfolio artifact and/or applies project customization changes.

Supported fields:

- `title`
- `items` (replace item list directly)
- `selected_project_ids`
- `project_order`
- `project_edits` (map of `project_id -> project customization payload`)

`project_edits` can persist:

- `role`
- `evidence_of_success`
- `thumbnail`
- `portfolio_showcase_text`
- `comparison_attributes`
- and other project customization fields

## Required Test Data ZIP Files

The repository now includes the milestone-style test zip fixtures:

- `input/test-data/code_collab_proj_snapshot_earlier.zip`
- `input/test-data/code_collab_proj_snapshot_later.zip`
- `input/test-data/multi_project_test_data.zip`

Expected structures include:

- `code_collab_proj/app/`
- `code_collab_proj/test/`
- `code_collab_proj/doc/`
- multiple top-level projects in `multi_project_test_data.zip` (code, text, image)
