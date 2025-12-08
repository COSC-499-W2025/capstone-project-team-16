# Team Log - Team 16
## Milestone: 2025-NOV-30 to 2025-DEC-07


### Milestone Goals Recap
- Finish up milestone 1 requirements
- Integrate other people's work
<<<<<<< HEAD
- Clean up code
- Fully integrate metadata extractor and analysis

### Features in Project Plan
- For coding projects, identify the programming language
- Fully integrate Meta Data extractor and Analysis Engine
- Meta Data Extractor
- Extract contribution metrics, such as project duration and contribution frequency
- Extrapolate individual contributions in collaborative projects
=======
- Package program

### Features in Project Plan
- Integrate Scan Variables into Analysis
- Dockerize project
- Fix framework detection not being extracted from projects in analyzer
>>>>>>> 42bf0ee (Added Ethan portion to week 14 team log and screenshots for burnup and completed)


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

<<<<<<< HEAD
![Screenshot](<screenshots/Team16/BurnupW12.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW12.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/TasksW12.png>)
=======
![Screenshot](<screenshots/Team16/BurnupW14.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW14.png>)

### In Progress Tasks Table

>>>>>>> 42bf0ee (Added Ethan portion to week 14 team log and screenshots for burnup and completed)

### Test Report
![Screenshot](<screenshots/Team16/Test1W14.png>)

### Tests
- Unit Tests All Pass
  - Updated tests: Framework detection and detailed analysis tests were rewritten to reflect the new behavior, including list-based dependency returns and handling of ecosystem-specific files. Tests now cover Python, Node, Rust, Go, Java, Ruby, and Docker framework files
  - Reworked test_parser to align with the new input/output structure and improved test reliability.
- Extensive manual testing
## Running Tests

1.  Run `python -m venv venv` to create a virtual environment.
2. On Windows run `venv/Scripts/activate`.
3. On Mac run `venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. In the root of the repositiory, enter `pytest` to run all tests.

<<<<<<< HEAD



=======
>>>>>>> 42bf0ee (Added Ethan portion to week 14 team log and screenshots for burnup and completed)
## Milestone: 2025-NOV-23 to 2025-NOV-30


### Milestone Goals Recap
- Finish up milestone 1 requirements
- Integrate other people's work
- Clean up code
- Fully integrate metadata extractor and analysis
- Resume document generator
- Ranking system
- Resume summaries

### Features in Project Plan
- For coding projects, identify the programming language
- Fully integrate Meta Data extractor and Analysis Engine
- Meta Data Extractor
- Extract contribution metrics, such as project duration and contribution frequency
- Extrapolate individual contributions in collaborative projects
- Output project information in structured text format
- Rank projects based on user contributions
- Summarize top-ranked projects
- Produce a chronological list of projects
- Produce a chronological list of skills exercised
- Resume document file


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW12.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW12.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/TasksW12.png>)

### Test Report
![Screenshot](<screenshots/Team16/Test1W12.png>)

### Tests
- Unit tests added to DB
- Extensive manual testing
## Running Tests

1.  Run `python -m venv venv` to create a virtual environment.
2. On Windows run `venv/Scripts/activate`.
3. On Mac run `venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. In the root of the repositiory, enter `pytest` to run all tests.


## Milestone: 2025-NOV-9 to 2025-NOV-23


### Milestone Goals Recap
- Process programming language 
- Identify individual projects and collaborative
- Extract repo data on a individual basis
- Fully integrate metadata extractor and analysis

### Features in Project Plan
- For coding projects, identify the programming language
- Fully integrate Meta Data extractor and Analysis Engine
- Meta Data Extractor
- Extract contribution metrics, such as project duration and contribution frequency
- Extrapolate individual contributions in collaborative projects
- Provide alternative analyses if external services are not permitted
- Distinguish between individual and collaborative projects
- For coding projects, identify the programming language and framework used
- Extrapolate individual contributions in collaborative projects
- Extract contribution metrics, such as project duration and contribution frequency by activity type (e.g., code, test, design, documentation)


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW11.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW10.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/TasksW11.png>)

### Test Report
![Screenshot](<screenshots/Team16/Test1W10.png>)
![Screenshot](<screenshots/Team16/Test2W11.png>)

### Tests
- No new unit tests added. All have been run and pass.
- Extensive manual testing with zip files
## Running Tests

1.  Run `python -m venv venv` to create a virtual environment.
2. On Windows run `venv/Scripts/activate`.
3. On Mac run `venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. In the root of the repositiory, enter `pytest` to run all tests.


## Milestone: 2025-NOV-2 to 2025-NOV-9


### Milestone Goals Recap
- Scrape repository information
- Clarify milestone 1 requirements for group
- Test repository scraping

### Features in Project Plan
- Repository Extraction
- Test repository_extraction
- Meta Data Extractor
- Fully define and refine Milestone requirements for our system
- - Distinguish between individual and collaborative projects
- For coding projects, identify the programming language and framework used
- Extrapolate individual contributions in collaborative projects
- Extract contribution metrics, such as project duration and contribution frequency by activity type (e.g., code, test, design, documentation)



### Burnup Chart
| Name | Username |
| Daniel Storozhuk | DanielKelowna|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW10.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW10.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/TasksW10.png>)

### Test Report
![Screenshot](<screenshots/Team16/Test1W10.png>)
### Tests for analyze_repo_type

**test_valid_git_repo_single_author_single_branch**

Description: Checks that a .git folder with only one author, one branch, and no merges is correctly identified as an individual project.

Checks: is_valid=True, project type is "individual", correct author, branch count, and no merges.

**test_valid_git_repo_collaborative**

Description: Tests a .git folder with multiple authors, multiple branches, and at least one merge commit.

Checks: Project type is "collaborative", multiple authors and branches, merges detected.

**test_non_git_folder_returns_none**

Description: Verifies that a folder that is not a .git directory is ignored.

Checks: Function returns None.

**test_git_repo_raises_exception**

Description: Ensures the function gracefully handles exceptions when trying to open a repository.

Checks: Returns None and does not crash.

### Tests for detailed_extraction

**test_detailed_extraction_valid_repo**

Description: Confirms that a valid repository entry is updated with the information returned by analyze_repo_type.

Checks: Entry is updated with repo name, root, authors, branch count, merges, and project type; success messages printed.

**test_detailed_extraction_invalid_repo**

Description: Ensures that if analyze_repo_type fails (returns None), the entry is not modified.

Checks: No new keys added, and skipping message is printed.

**test_detailed_extraction_non_repo**

Description: Tests that non-repository entries are left untouched.

Checks: Entry data unchanged, no repo analysis output printed.

## Running Tests

1.  Run `python -m venv venv` to create a virtual environment.
2. On Windows run `venv/Scripts/activate`.
3. On Mac run `venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. In the root of the repositiory, enter `pytest` to run all tests.

### Additional Context (Optional)
- Notes or blockers

## Milestone: 2025-OCT-26 to 2025-NOV-2

### Milestone Goals Recap
- Create a basic metadata extractor to handle all file types.

### Features in Project Plan
- Scrape Base Level Metadata
- Test base_extraction
- Meta Data Extractor
- Alternative Analyses


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani Lugalla |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW9.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW9.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/TasksW9.png>)

### Test Report
![Screenshot](<screenshots/Team16/Test1W9.png>)
Unit tests for two functions in metadata_extraction have been added using Pytest.

## load_filters Tests
### test_load_filters_returns_dict
Scenario: JSON file exists and is valid.
Expected: Returns a dictionary mapping extensions (e.g. .py) to categories ("source_code").

### test_load_filters_handles_missing_file
Scenario: JSON file is missing.
Expected: Prints a warning (“Filter file not found”) and returns an empty {} instead of crashing.

### test_load_filters_invalid_json
Scenario: JSON file is corrupted or not properly formatted.
Expected: Prints a warning (“Error decoding JSON”) and returns {}.

### test_load_filters_unexpected_error
Scenario: Unexpected exception occurs (e.g. permission denied).
Expected: Prints a general error message (“Unexpected error loading filters”) and returns {}.

## base_extraction Tests
### test_base_extraction_categorizes_files
Scenario: Files have extensions that match filters.
Expected: Returns a list of extracted metadata with correct categories ("source_code", "documentation"), and sets "isFile": True.

### test_base_extraction_handles_folders
Scenario: Input includes a folder name (ending with /).
Expected: "isFile" is False, and category is "repository" (if matched) or "uncategorized".

### test_base_extraction_uncategorized
Scenario: File extension not present in filter map.
Expected: Category defaults to "uncategorized" and "isFile" is True.

### test_base_extraction_no_filters
Scenario: load_filters() returns None.
Expected: Function handles gracefully. Prints an error and doesn’t crash.

## Running Tests

1.  Run `python -m venv venv` to create a virtual environment.
2. On Windows run `venv/Scripts/activate`.
3. On Mac run `venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. In the root of the repositiory, enter `pytest` to run all tests.

### Additional Context (Optional)
- Notes or blockers

## Milestone: 2025-OCT-19 to 2025-OCT-26


### Milestone Goals Recap
- Create larger tasks in backlog
- Add unit tests to zip parsing
- Generate and return file tree for meta data extractor
- Add consent prompt for external service usage

### Features in Project Plan
- Add work items from WSB to backlog
- Parse uploaded zipped folder containing nested files and folders
- Add consent prompt for external service usage
- Provide alternative analyses if external services are not permitted


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW5.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW5.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW5.png>)

### Test Report
![Screenshot](<screenshots/Team16/Test1W8.png>)
Unit tests for two functions in file_parser have been added using Pytest.

### get_input_file_path

1. User enters a valid zip path immediately.
2. User presses Enter without typing anything, then enters a valid path.
3. User enters an invalid path first, then a valid one.
4. User enters multiple invalid paths (including empty input) before finally entering a valid one.
5. User enters a valid zip file containing multiple files.
6. User enters an empty or invalid zip first, then a valid one

### check_file_validity

1. User provides a path that doesn’t exist.
2. User provides a path to a directory instead of a file.
3. User provides a file that doesn’t end with .zip.
4. User provides a .ZIP (uppercase or mixed case) file and should still be accepted.
5. User provides a valid zip file containing multiple files.
6. User provides a corrupted zip file (detected by testzip()).
7. User provides a valid but empty zip file.
8. User provides a file with a .zip extension that isn’t actually a zip (raises BadZipFile).
9. User provides a very large zip file using ZIP64 format (raises LargeZipFile).
10. An unexpected error occurs while opening or reading the zip file.

## Running Tests

1.  Run `python -m venv venv` to create a virtual environment.
2. On Windows run `venv/Scripts/activate`.
3. On Mac run `venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. In the root of the repositiory, enter `pytest` to run all tests.

### Additional Context (Optional)
- Notes or blockers


## Milestone: 2025-OCT-12 to 2025-OCT-19


### Milestone Goals Recap
- Populate backlog with tasks
- Add parsing of zip file to be analyzed
- Add Pytest to allow testing
- Add consent prompt for external service usage

### Features in Project Plan
- Add work items from WSB to backlog
- Integrate testing framework
- Parse uploaded zipped folder containing nested files and folders
- Request user permission before using external services (e.g., LLMs) and inform users about data privacy implications


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW5.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW5.png>)

### In Progress Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW5.png>)

### Test Report
- Summary of tests run this milestone

### Additional Context (Optional)
- Notes or blockers


## Milestone: 2025-OCT-5 to 2025-OCT-12


### Milestone Goals Recap
- Update README
- Update Documentation
- Get started coding

### Features in Project Plan
- Update System Architecture to Milestone 1 Reqs
- Setup README
- Add consent prompt for user input


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW4.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW4.png>)

### In Progress Tasks Table


### Test Report
- Summary of tests run this milestone

### Additional Context (Optional)
- Notes or blockers

## Milestone: 2025-SEP-28 to 2025-OCT-5


### Milestone Goals Recap
- Clean up repo
- DFD Level 0
- DFD Level 1

### Features in Project Plan
- Clean up repo
- DFD Level 0
- DFD Level 1


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW3.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/DoneTasksW3.png>)

### In Progress Tasks Table
| Task | Assigned To (Username) |
|------|----------------------|

### Test Report
- Summary of tests run this milestone

### Additional Context (Optional)
- Notes or blockers

## Milestone: 2025-SEP-21 to 2025-SEP-28


### Milestone Goals Recap
- Create system architecture
- Project proposal

### Features in Project Plan
- System Architecture
- Project Plan


### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
| La Wunn| LaWunn|
| Amani |lugger33 |

![Screenshot](<screenshots/Team16/BurnupW2.png>)

### Completed Tasks Table
![Screenshot](<screenshots/Team16/TasksW2.png>)

### In Progress Tasks Table
| Task | Assigned To (Username) |
|------|----------------------|

### Test Report
- Summary of tests run this milestone

### Additional Context (Optional)
- Notes or blockers

## Milestone: 2025-SEP-15 to 2025-SEP-21


### Milestone Goals Recap
- Create functional and non-functional requirements for project
- Organize repo branches and file structure

### Features in Project Plan
- Requirments sheet 
- Repo organization 

### Tasks from Project Board
| Feature | Task | Assigned To (Username) | Notes |
| --------- | ------ | ---------------------- | ------ |
| Requirments sheet | Functional requirements | ethansturek | … |
| Requirments sheet | Non-functional requirements | ethansturek | … |
| Requirments sheet | In-class discussion notes | ethansturek | … |
| Repo organization | File structure | ethansturek | … |
| Repo organization | Branch creation | ethansturek | … |
| Repo organization | Git project creation | ethansturek | … |

### Burnup Chart
| Name | Username |
|----------------|----------------|
| Ethan Sturek | ethansturek |
|  La Wunn| LaWunn|
| Amani |lugger33 |



### Completed Tasks Table
| Task | Assigned To (Username) | 
|------|----------------------|
| Functional requirements | ethansturek |
| Non-functional requirements | ethansturek | 
| In-class discussion notes | ethansturek |
| File structure | ethansturek |
| Branch creation | ethansturek |
| Git project creation | ethansturek |

### In Progress Tasks Table
| Task | Assigned To (Username) |
|------|----------------------|

### Test Report
- Summary of tests run this milestone

### Additional Context (Optional)
- Notes or blockers

