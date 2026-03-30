# Skill Scope

Skill Scope analyzes zipped project archives and turns them into structured insights about languages, frameworks, timelines, collaboration patterns, and contributor activity. It supports local scanning through a CLI, a FastAPI backend for programmatic access, and generated outputs that can be reused for portfolio and resume workflows.

## What Skill Scope Provides

- ZIP-based project ingestion with validation and duplicate detection
- Project analysis for languages, frameworks, timelines, and repository metadata
- Support for individual and collaborative project summaries
- Saved scan history backed by SQLite
- Resume and portfolio artifact generation and editing through the API
- A standalone CLI and an API-backed CLI client

## Video Demo

Project demo: [Watch the video demo](https://drive.google.com/file/d/1Dp4hVczJzV1xmCK-5Sp2-MyDS67Xzi3J/view?usp=sharing)

## Prerequisites

Before setting up the project, make sure you have:

- Python `3.12+` recommended
- `pip`
- `git` installed on your system
- Docker and Docker Compose, if you plan to use the containerized workflow

## Requirements

The Python dependencies are defined in [`requirements.txt`](requirements.txt). Key runtime libraries include:

- FastAPI and Uvicorn for the API server
- GitPython for repository inspection
- `python-docx` for resume export
- `python-multipart` and `httpx` for API uploads and testing
- `pytest` for the test suite

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd capstone-project-team-16
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running Skill Scope

### Option 1: Standalone CLI

Use this mode if you want to run scans and manage saved scans locally without starting the API yourself.

```bash
python src/main.py
```

### Option 2: FastAPI Server

Use this mode if you want REST endpoints, generated API docs, or integration with the API-backed client.

```bash
python src/api.py
```

Once running, the API is available at:

- Interactive docs: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

Detailed endpoint documentation is available in [`docs/api/endpoints.md`](docs/api/endpoints.md).

### Option 3: API-Backed CLI Client

This client talks to the FastAPI backend and will attempt to start the API automatically if it is not already running.

```bash
python src/api_main.py
```

By default, it connects to `http://127.0.0.1:8000`. To point it at another API instance:

```bash
export SKILLSCOPE_API_URL=http://127.0.0.1:8000
python src/api_main.py
```

### Option 4: Docker

The Docker workflow runs the standalone CLI in a container and mounts your local `input/`, `output/`, and `data/` directories.

```bash
docker compose build
docker compose run --rm -it skillscope
```

## Input, Output, and Persistence

### Input

- Place ZIP files you want to scan in the project-level `input/` directory.
- The CLI will prompt you to select from available ZIP files.
- The API accepts either multipart uploads or a local `zip_path` value.

### Output

Generated artifacts and exports are written under `output/`, including:

- thumbnails
- generated resumes
- generated portfolios
- API server logs when started by the API-backed client

### Database

Saved scans and related records are stored in:

- default path: `data/skillscope.db`

You can override the database directory with:

```bash
export SKILLSCOPE_DB_DIR=/path/to/custom/data
```

## Testing

Run the automated test suite from the repository root:

```bash
venv/bin/python -m pytest
```

Additional testing documentation:

- Test report: [`docs/testing/test-report.md`](docs/testing/test-report.md)
- Known bugs: [`docs/testing/known-bugs.md`](docs/testing/known-bugs.md)

## Important Notes

- Scans are performed on ZIP archives, not arbitrary loose folders.
- Duplicate ZIP uploads are detected using file hashes.
- Legacy `/scans*` endpoints are still present for compatibility.
- Some framework extraction paths are intentionally limited and are documented in the known-bugs list.
- The repository includes committed ZIP fixtures in `input/test-data/` for automated testing; extra manual-validation fixture directories are ignored locally.

## Documentation

- API endpoints: [`docs/api/endpoints.md`](docs/api/endpoints.md)
- Test report: [`docs/testing/test-report.md`](docs/testing/test-report.md)
- Known bugs: [`docs/testing/known-bugs.md`](docs/testing/known-bugs.md)
- Architecture artifact: [`docs/plan/Milestone 1 Team 16 Architecture.jpg`](docs/plan/Milestone%201%20Team%2016%20Architecture.jpg)

## DFD Diagram Level 0

<img width="1124" height="850" alt="dfd lvl 0 of milestone 3 updated of DFD-Level 1 drawio" src="https://github.com/user-attachments/assets/9bb5f5d2-5666-4fea-b082-2bac82c33c04" />

The Level 0 Data Flow Diagram presents Skill Scope as a single high-level system. Users interact with the system through either the CLI interface or the API client. Requests such as project scans or output generation are sent to the system, which processes them and returns results.

The system communicates with a local database to store and retrieve scan data, configurations, and generated outputs. This diagram focuses on the overall flow of data without showing internal processing details.

## DFD Diagram Level 1

<img width="1974" height="1160" alt="final milestone 3 updated of DFD-Level 1 drawio (1)" src="https://github.com/user-attachments/assets/b67bd7ec-507b-40f9-aaba-baf6d24bb7a8" />

The Level 1 Data Flow Diagram expands on the internal structure of Skill Scope. The system is coordinated by the Orchestrator, which manages the flow between different components.

User requests from the CLI or API are processed through the FastAPI server and passed into the system. The Metadata Extractor and Analysis Engine handle project analysis, generating structured insights such as languages, frameworks, and contribution data.

The Customization Manager allows user preferences to influence output generation, while the Resume and Portfolio Generators produce final artifacts. All results, configurations, and scan history are stored in the local database for future access.

This diagram highlights how different modules collaborate to transform raw project data into meaningful outputs.
