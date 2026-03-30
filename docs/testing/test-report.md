# Skill Scope Test Report

Date: 2026-03-29

## Test Execution Summary

- Repository root: `/Users/amani/Documents/GitHub/capstone-project-team-16`
- Command used: `venv/bin/python -m pytest`
- Result: `110` tests collected, `110` passed
- Runtime: about `2.60s`
- Current blocking failure: none

## Test Files That Currently Work With This System

The files below are active and currently execute against the repository in its present state.

| Test file | Status | What it covers |
| --- | --- | --- |
| `tests/test_api.py` | Passing | FastAPI health, privacy, upload, incremental merge, project edits, skills aggregation, resume generation/editing, portfolio generation, legacy scan endpoints, invalid input handling, multipart upload. |
| `tests/test_api_fixtures.py` | Passing | Validates shipped ZIP fixtures used for API and incremental-scan tests. |
| `tests/test_check_file_validity.py` | Passing | ZIP-path validation, extension checks, empty archives, corrupted archives, bad ZIP handling, large ZIP handling, generic error handling. |
| `tests/test_db.py` | Passing | SQLite schema creation, scan persistence, listing, retrieval, ordering, update, deletion, hash storage. |
| `tests/test_deduplication.py` | Passing | File hashing, ZIP hash return values, duplicate scan detection in the DB layer. |
| `tests/test_detailed_analysis.py` | Passing | Repository enrichment during detailed extraction and non-repository passthrough behavior. |
| `tests/test_extractor.py` | Passing | Filter loading, bad/missing filter files, base extraction, categorization, folder handling, uncategorized-file behavior. |
| `tests/test_framework_analysis.py` | Passing | Framework/dependency detection from Python, Node, Go, Java, Ruby, and Docker-related manifests, including read/parse error handling. |
| `tests/test_orchestrator.py` | Passing | Basic vs. advanced analysis-mode orchestration and persistence flow. |
| `tests/test_parser.py` | Passing | Interactive ZIP selection, retry/cancel behavior, valid/invalid ZIP handling, empty input folder behavior. |
| `tests/test_portfolio_generator.py` | Passing | Portfolio object creation, project insertion, default tech-stack filtering, portfolio factory logic. |
| `tests/test_repo_extraction.py` | Passing | Git repository classification for individual, collaborative, non-repo, and repo-open failure cases. |
| `tests/test_resume_editing.py` | Passing | Contributor portfolio generation, edit/reset flows, project description updates, skill customization, full reset behavior. |
| `tests/test_scan_service.py` | Passing | Scan analysis orchestration, persistence calls, and incremental merge semantics. |
| `tests/test_spoof_advanced.py` | Passing | Content-based language detection against spoofed extensions, shebangs, false positives, SQL edge cases, and polyglot-style inputs. |
| `tests/test_thumbnail.py` | Passing | Thumbnail upload endpoint, filename sanitization, and on-disk output creation. |

## Test Files Present But Not Currently Providing Coverage

These files exist in `tests/`, but they are empty and did not contribute to the run above.

| Test file | Status | Notes |
| --- | --- | --- |
| `tests/test_classification.py` | Empty | Placeholder file, no test cases collected. |
| `tests/test_language_detector.py` | Empty | Placeholder file, no test cases collected. |
| `tests/test_resume_generator.py` | Passing | Unit coverage for generic resume text and contributor-resume text when project metadata uses list-shaped languages/frameworks. |

## Test Strategies Used

The current suite uses several complementary strategies:

1. Unit isolation with mocks and monkeypatching
   - Core services are isolated from the filesystem, Git, and persistence layers using `monkeypatch`, `patch`, and `MagicMock`.
   - Examples: `tests/test_scan_service.py`, `tests/test_orchestrator.py`, `tests/test_repo_extraction.py`.

2. API contract and behavior testing
   - FastAPI routes are exercised through `fastapi.testclient.TestClient`.
   - These tests verify request parsing, JSON and multipart input handling, status codes, and response payload shape.
   - Example: `tests/test_api.py`.

3. Temporary filesystem and database testing
   - `tmp_path`, `tempfile`, and temporary SQLite databases are used to verify behavior without mutating real user data.
   - Examples: `tests/test_db.py`, `tests/test_parser.py`, `tests/test_deduplication.py`, `tests/test_spoof_advanced.py`.

4. Negative-path and error-handling validation
   - The suite intentionally checks invalid files, unreadable manifests, bad ZIPs, missing resources, and malformed inputs.
   - Examples: `tests/test_check_file_validity.py`, `tests/test_extractor.py`, `tests/test_framework_analysis.py`.

5. Regression checks for merge and persistence logic
   - Merge behavior is tested explicitly for empty inputs, one-sided inputs, contributor profile merging, duplicate skills, and hash tracking.
   - Examples: `tests/test_scan_service.py`, `tests/test_db.py`.

6. Fixture validation for realistic archives
   - ZIP fixtures used for multi-project and incremental-scan behavior are validated before higher-level tests depend on them.
   - Example: `tests/test_api_fixtures.py`.

7. Adversarial classification checks
   - Language detection is tested with spoofed extensions, misleading filenames, weak signals, and false-positive cases.
   - Example: `tests/test_spoof_advanced.py`.

## Coverage Notes

- The strongest automated coverage is around API behavior, ZIP validation, SQLite persistence, merge logic, and repository metadata extraction.
- Resume generation now has direct unit coverage for list-shaped metadata in addition to API coverage.
- Two expected coverage areas currently still have no direct tests because their test files are empty: classification and language-detector module tests.

## Recommendation

The current suite is usable as a release gate for the covered Python paths. The next gaps to close are direct tests for the classification and language-detector modules if those modules remain part of the maintained surface area.
