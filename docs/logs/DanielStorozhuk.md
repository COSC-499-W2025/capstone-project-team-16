## 2025-NOV-02 to 2025-NOV-09


### Type of Tasks Worked On
Backend Development, System Architecture, Database Implementation
![Screenshot](<screenshots/Daniel/Week10.png>)

### Recap of Week's Goals
- Established the core application architecture by defining all service protocols and data contracts
- Build a mock-driven main.py entry point to test and validate the end-to-end (incomplete) pipeline.
- Create a concrete StorageManager to handle database persistence with SQLite.


### Features Assigned (Project Plan)
- Core Application Architecture (Contracts)

- Orchestrator (Initial Skeleton)

- Storage Layer (SQLite Implementation)

- Main Entry Point (Mocked)

### Tasks from Project Board
| Feature | Task | Status (Completed/In Progress) | Notes |
Feature,Task,Status (Completed/In Progress),Notes
Core Architecture,Define all service protocols (#89),Completed,contracts.py
Core Architecture,Define all DTOs (#90),Completed,contracts.py
Main Entry Point,Refactor entry point / workflow coordination (#91),Completed,main.py / orchestrator.py
Storage Layer,Implement StorageManager class for SQLite (#92),Completed,storage_manager.py
Main Entry Point,"Implement mock components (MockFileParser, MockMetadataExtractor) (#93)",Completed,For testing the pipeline in main.py



### Completed Tasks (Last 2 Weeks)
- Architecture: Defined the entire application's architecture in contracts.py, including all protocols and data structures.

- Orchestrator: Implemented the Orchestrator skeleton, which successfully coordinates the MetadataExtractor and Storage components.

- Storage: Fully implemented a StorageManager for SQLite, including table initialization, data saving (with a flaw), and data reading.

### In-Progress Tasks (Last 2 Weeks)
- Storage Fix: The StorageManager.save_extracted_data method is a placeholder and must be fixed. It currently deletes all data on every run, preventing the app from building a "scope." This needs to be replaced with an "upsert" (update or insert) strategy.

- Orchestrator Expansion: The Orchestrator is incomplete. It needs to be updated to also accept and run the AnalysisEngine and Exporter components.

### Additional Context (Optional)
- The project is at a "skeleton" stage. The core pipeline runs, but it's powered by mocks and has a destructive database implementation.

- These limitations are outlined as a comment in "main.py"


# Personal Log - Daniel Storozhuk
## 2025-OCT-26 to 2025-NOV-2


### Type of Tasks Worked On
![Screenshot](<screenshots/Daniel/Week9.png>)

### Recap of Week's Goals
- 


### Features Assigned (Project Plan)
- 

### Tasks from Project Board
| Feature | Task | Status (Completed/In Progress) | Notes |
|------|------|-------------------------------|-------|
| Orchestrator skeleton | create orchestrator skeleton | Completed | Basic template to continue other work |



### Completed Tasks (Last 2 Weeks)


### In-Progress Tasks (Last 2 Weeks)
- NA

### Additional Context (Optional)
- NA


# Personal Log - Daniel Storozhuk
## 2025-OCT-19 to 2025-OCT-26


### Type of Tasks Worked On
![Screenshot](<screenshots/Daniel/Week8.png>)

### Recap of Week's Goals
- Discussed which aspects to work on first
- Created orchestrator skeleton


### Features Assigned (Project Plan)
- Orchestrator skeleton

### Tasks from Project Board
| Feature | Task | Status (Completed/In Progress) | Notes |
|------|------|-------------------------------|-------|
| Orchestrator skeleton | create orchestrator skeleton | Completed | Basic template to continue other work |



### Completed Tasks (Last 2 Weeks)
- Discussion of implementation
- orchestrator skeleton completion

### In-Progress Tasks (Last 2 Weeks)
- NA

### Additional Context (Optional)
- NA