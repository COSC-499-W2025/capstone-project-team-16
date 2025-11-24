# Team 16 - Secure Scan
## Project Overview (Milestone 1)

This project aims to extract and analyze various personal projects on a user's machine such as code, documents, notes, design sketches, and media files to identify meaningful insights into an individual’s work contributions, creative process, and project evolution.

By analyzing artifacts and their metadata, the system aims to help individuals reflect on their productivity, skill development, and creative direction. Additionally, it provides metrics and summaries that can be showcased through portfolios or résumés, highlighting the user's strengths and accomplishments.

## Target Users

The system is designed for a wide range of users who regularly create digital work on their computers, including:

- Graduating students and early professionals looking to showcase their projects and better understand their digital productivity, skill development, and project evolution

- Programmers who want to analyze their coding contributions and development history

- Creatives such as designers, artists, and media producers who wish to track their creative outputs

- Analysts who work with data, research, and technical documentation

These users can utilize the system to:

- Showcase their work through a portfolio or dashboard

- Reflect on their skills and productivity trends

- Improve in weaker areas and aquire new skills

## Technology Stack

Programming Language: Python

Future Additions: REST API and front-end (Term 2)

Output Format (Milestone 1): Text-based (CSV, JSON, or plain text)

## System Functionality — Milestone 1

The system must be able to:

1. Require the user to give consent for data access before proceeding

1. Parse an uploaded zipped folder containing nested files and folders

1. Return an error message if the uploaded file is in an incorrect format

1. Request user permission before using external services (e.g., LLMs) and inform users about data privacy implications

1. Provide alternative analyses if external services are not permitted

1. Store user configurations for future sessions

1. Distinguish between individual and collaborative projects

1. For coding projects, identify the programming language and framework used

1. Extrapolate individual contributions in collaborative projects

1. Extract contribution metrics, such as project duration and contribution frequency by activity type (e.g., code, test, design, documentation)

1. Extract key skills from each project

1. Output project information in structured text format

1. Store project information in a database

1. Retrieve previously generated portfolio information

1. Retrieve previously generated résumé items

1. Rank projects based on user contributions

1. Summarize top-ranked projects

1. Delete previously generated insights, ensuring shared files remain unaffected

1. Produce a chronological list of projects

1. Produce a chronological list of skills exercised

## Architecture and Design Documents
### System Architecture Diagram

#### [Architecture Diagram](docs/plan/Milestone%201%20Team%2016%20Architecture.jpg)

#### Description:

The system architecture diagram illustrates the structure and data flow of our system. The design follows a modular, layered approach to ensure scalability, maintainability, and clear data movement.

For Milestone 1, users interact with a simple text-based command-line interface. Currently, the API layer and image cache are not yet implemented but are planned for future milestones to enable richer interactions, cloud integration, and thumbnail handling.

The System Orchestrator coordinates operations among core modules:

- File Scanner: Identifies user-uploaded folders and compressed archives and validates file types.

- Metadata Extractor: Extracts metadata from files, including timestamps, file types, authorship, Git repository history and insights and other relevant information.

- Analysis Engine: Processes extracted metadata to generate insights such as contribution metrics, project timelines, and key skills exercised.

- Dashboard & Exporter: Outputs results in structured formats like JSON or CSV for portfolio or résumé use.

- A Privacy Manager enforces user-defined rules to protect sensitive data, and a Local Database stores processed results. A Logging System tracks operations for debugging and traceability.

#### Future Plans:

- Implement an API layer to enable modular access and integration with other tools.

- Integrate an image cache for handling thumbnails and temporary media files.

- Expand the UI beyond the command line to a graphical or web-based interface.

- **Potential** Include additional external service integration (LLM services) with privacy controls for deeper insights and image analysis.

Our modular architecture ensures that future features can be added without disrupting the core system.

### Data Flow Diagram (DFD) – Level 1

<img width="2504" height="1160" alt="DFD-Level 1 drawio (1)" src="https://github.com/user-attachments/assets/82e4c3c5-3508-4eab-9561-e1b689946ff7" />


Description:

This Level 1 DFD shows our main processes and data movements within the Digital Work Artifact Analysis System. It breaks the system into key functional components and shows how data flows between them, external entities, and data stores.

The user initiates the process by submitting privacy settings and scan requests, which are received and processed by the system. These requests pass through several stages, starting with privacy rule management to make sure sensitive data is handled correctly. Then it is followed by file scanning and metadata extraction from the file system.

The extracted metadata, along with file paths and thumbnail references, is then sent to the analysis engine, which creates insights and contribution metrics. These results are coordinated and logged through the workflow coordinator, which also updates the record activity and sends logs to the Log Data store.

Finally, the processed results are passed to the export dashboard where they are compiled and returned to the user. Additional data such as thumbnails are stored in the image cache to support visual outputs.

### Work Breakdown Structure (WBS)

<img width="710" height="524" alt="Screenshot 2025-10-12 at 11 10 32 PM" src="https://github.com/user-attachments/assets/780e35f9-1547-4909-b4a8-9f3de614c103" />

Description:

Our WBS outlines the main phases of our project and breaks them into manageable tasks. It includes project management, system design, backend development, output/export development, testing, and documentation. This structure helps organize the team’s work, clarify responsibilities, and plan the project timeline more effectively.

# Project Structure
Please use the provided folder structure for your project. You are free to organize any additional internal folder structure as required by the project. 

```
.
├── docs                    # Documentation files
│   ├── contract            # Team contract
│   ├── proposal            # Project proposal 
│   ├── design              # UI mocks
│   ├── minutes             # Minutes from team meetings
│   ├── logs                # Team and individual Logs
│   └── ...          
├── src                     # Source files (alternatively `app`)
├── tests                   # Automated tests 
├── utils                   # Utility files
└── README.md
```

Please use a branching workflow, and once an item is ready, do remember to issue a PR, review, and merge it into the master branch.
Be sure to keep your docs and README.md up-to-date.
