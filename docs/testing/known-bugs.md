# Skill Scope Known Bugs

Date: 2026-03-29

## KB-001: Legacy portfolio generation crashes when languages or frameworks are lists

- Affected feature: legacy portfolio creation path built on `create_portfolios()`
- Reproduction:
  - Call `create_portfolios()` with a project summary where `languages` or `frameworks` is a list, such as `['Python', 'Go']`.
- Expected behavior:
  - The portfolio generator should accept the same project-summary shape produced elsewhere in the system.
- Actual behavior:
  - It crashes with `AttributeError: 'list' object has no attribute 'split'`.
- Root cause:
  - [`src/portfolio_generator.py`](/Users/amani/Documents/GitHub/capstone-project-team-16/src/portfolio_generator.py#L121) assumes both fields are comma-separated strings and calls `.split(",")`.
- Evidence:
  - Direct local repro on 2026-03-29 returned `AttributeError 'list' object has no attribute 'split'`.
- Impact:
  - Portfolio generation is brittle when fed current-style structured analysis output instead of string-normalized data.

## KB-002: Framework detection for Maven, Gradle, and Docker manifests returns placeholders instead of real dependencies

- Affected feature: framework/dependency extraction for Java and Docker projects
- Reproduction:
  - Run framework detection on `pom.xml`, `build.gradle`, `settings.gradle`, `Dockerfile`, or `docker-compose.yml`.
- Expected behavior:
  - The system should parse and return meaningful framework/dependency names.
- Actual behavior:
  - It returns placeholder labels such as `See pom.xml`, `See build.gradle`, and `Dockerfile dependencies`.
- Root cause:
  - [`src/metadata_extractor.py`](/Users/amani/Documents/GitHub/capstone-project-team-16/src/metadata_extractor.py#L211) contains TODO placeholders rather than real parsing logic.
- Evidence:
  - [`tests/test_framework_analysis.py`](/Users/amani/Documents/GitHub/capstone-project-team-16/tests/test_framework_analysis.py#L88) currently encodes those placeholder values as the expected result.
- Impact:
  - Java and Docker projects can appear under-analyzed in project summaries, portfolios, and resumes because real dependencies are not extracted.

## KB-003: Contributor-specific resume edits do not preserve contributor context

- Affected feature: `POST /resume/{resume_id}/edit` for contributor-targeted resumes
- Reproduction:
  - Generate a resume with `contributor_id`, then reorder or reselect projects through the edit endpoint.
- Expected behavior:
  - Resume items should keep contributor-specific wording and contributor-level skill selection.
- Actual behavior:
  - The edit flow rebuilds resume items without contributor stats or contributor ID.
- Root cause:
  - [`src/api.py`](/Users/amani/Documents/GitHub/capstone-project-team-16/src/api.py#L1255) does not store `contributor_id` in the saved artifact.
  - [`src/api.py`](/Users/amani/Documents/GitHub/capstone-project-team-16/src/api.py#L1305) rebuilds items by calling `_project_to_resume_item(project_map[pid])` without contributor context.
- Evidence:
  - Code-path review on 2026-03-29.
  - In local repro work, contributor-specific descriptions were present before edit and the edit path immediately dropped into the generic rebuild path.
- Impact:
  - Even after KB-001 is fixed, contributor resumes are likely to lose personalized descriptions or contributor-specific skill context after edits.
