# Team Log - Team 16

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

