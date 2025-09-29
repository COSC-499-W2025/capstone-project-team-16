## **Features Proposal for Project Option XX**
Team Number: 16
Team Members: Ethan Sturek 21282611, La Wunn Soe 69493971

## **1 Project Scope and Usage Scenario**
The basic usage scenario for this project is to provide people, specifically programmers, creatives (such as artists, designers, and photographers), and data analysts with a way to mine and analyze their own digital works and to better understand and present their contributions. A programmer might scan their repositories to generate a timeline of commits and code growth for use in interviews, while a creative could collect images, sketches, and media drafts into an automatically organized portfolio. Similarly, a data analyst could trace the evolution of datasets, notebooks, and reports to demonstrate methodology and reproducibility. In all cases, the system will allow users to scan selected files, extract meaningful metadata, and generate visual dashboards or exportable reports, helping them showcase their productivity, reflect on their processes, and organize their work histories while respecting privacy.

## **2 Proposed Solution**
Our solution is a system for mining and analyzing personal digital works including code repositories, documents, notes, design files, and media. The system scans user-selected locations, extracts meaningful data, and organizes results into a structured database. An analysis engine then generates insights such as timelines, productivity trends, and project evolution, which are presented back to the user through an interactive dashboard. Users can also export professional-looking portfolios or reports directly from there. Privacy rules will also be applied at every step to make sure that sensitive files are never exposed.

What makes our approach unique is the combination of automation, visualization, and privacy control. Unlike a simple file organizer, our system not only collects and classifies files but also transforms them into interpretable insights and exportable outputs that highlight a user’s contributions. Key features include an integrated Privacy Manager, visual dashboards, and a flexible exporter that can produce shareable reports. Our value proposition is to give users a tool that helps them showcase their work, reflect on their growth, and stay in control of their data. Compared to other teams, we believe our strength lies in balancing technical depth (data extraction, analysis, visualization) with usability and ethical awareness, making the system both practical and trustworthy.

## **3 Use Cases**
### **For Programmers**

#### Use Case: Generate Commit Timeline

* **Primary actor:** Programmer
* **Description:** The process of scanning repositories to build a timeline of commits.
* **Precondition:** Programmer has selected one or more repositories.
* **Postcondition:** A commit timeline is displayed on the dashboard.
* **Main Scenario:**

  1. Programmer selects a repository
  2. The system scans commits and metadata (dates, lines added/removed)
  3. The analysis engine generates a commit timeline
  4. The dashboard displays the timeline
* **Extensions:**

  1. Repository is private/inaccessible → system alerts the user
  2. Very large repo → system paginates results and shows partial progress

### **For Creatives**

#### Use Case: Build a Portfolio of Images

* **Primary actor:** Creative (Artist, Designer, Photographer)
* **Description:** The process of scanning design/media files and automatically building a portfolio.
* **Precondition:** Creative selects folders with images or media files.
* **Postcondition:** A structured portfolio (with thumbnails, categories, and metadata) is generated.
* **Main Scenario:**

  1. Creative selects folders containing works
  2. The system extracts thumbnails and file metadata (dates, dimensions, tags)
  3. The system organizes works by project or timeline
  4. The dashboard displays portfolio view
  5. User can export the portfolio in PDF or website format
* **Extensions:**

  1. Unsupported media type is found → system skips and notifies user
  2. User applies filters (e.g., only show images from last 6 months)

### **For Data Analysts**

#### Use Case: Trace Dataset Evolution

* **Primary actor:** Data Analyst
* **Description:** The process of tracking the evolution of datasets, notebooks, and reports.
* **Precondition:** Analyst selects relevant files (datasets, Jupyter notebooks, CSVs).
* **Postcondition:** A timeline of dataset and notebook updates is shown.
* **Main Scenario:**

  1. Data analyst selects datasets and notebooks
  2. The system scans metadata (timestamps, version differences)
  3. The analysis engine correlates datasets with notebooks/reports
  4. The dashboard displays an evolution timeline with dependencies
* **Extensions:**

  1. Corrupted dataset file → system logs error and continues with remaining files
  2. User requests export of reproducibility report (dataset + notebook timeline)

### **General Use Cases**

#### Use Case: Select Location for Scanning

* **Primary actor:** User (any role)
* **Description:** The process of selecting files or folders for analysis.
* **Precondition:** User is logged in and has granted the system access to storage.
* **Postcondition:** Selected file paths are stored for scanning.
* **Main Scenario:**

  1. User opens the file selection interface
  2. User browses local folders or repositories
  3. User selects one or more files/folders
  4. The system validates the file types and access permissions
  5. Selected paths are saved to the system for scanning
* **Extensions:**

  1. Invalid or unsupported file type is selected → system skips and notifies the user
  2. User cancels the selection → no files are added

#### Use Case: Run Scan

* **Primary actor:** User (any role)
* **Description:** The process of scanning selected files and extracting metadata.
* **Precondition:** User has selected at least one valid file/folder.
* **Postcondition:** Metadata is extracted and stored for analysis.
* **Main Scenario:**

  1. User clicks “Run Scan”
  2. The system scans the selected files
  3. The metadata extractor processes attributes (timestamps, file type, size, etc.)
  4. Extracted data is saved in the database
  5. The system logs progress and completion
* **Extensions:**

  1. File access error → system logs the error and skips file
  2. Scan is interrupted → system resumes from last successful file

#### Use Case: View Dashboard

* **Primary actor:** User (any role)
* **Description:** The process of viewing scan results and analytics.
* **Precondition:** User has run at least one scan.
* **Postcondition:** Dashboard displays graphs, summaries, and insights.
* **Main Scenario:**

  1. User navigates to the dashboard view
  2. The system retrieves processed data from the database
  3. The analysis engine generates visualizations (timelines, trends, etc.)
  4. The dashboard displays the results
* **Extensions:**

  1. No scans exist → system prompts the user to run a scan first
  2. User applies filters or sorting options → dashboard updates dynamically

#### Use Case: Export Report

* **Primary actor:** User (any role)
* **Description:** The process of exporting results into a portfolio or report format.
* **Precondition:** User has completed a scan and results are available.
* **Postcondition:** A report is generated in the selected format (PDF, HTML, etc.).
* **Main Scenario:**

  1. User selects “Export Report” from the dashboard
  2. User chooses export format and options
  3. The system compiles results into a report
  4. The report is saved locally or shared externally
* **Extensions:**

  1. User cancels export → no report is generated
  2. Storage error → system notifies the user and retries saving

#### Use Case: Apply Privacy Rules

* **Primary actor:** User (any role)
* **Description:** The process of defining and applying privacy preferences to scans.
* **Precondition:** User is logged in and has configured at least one privacy rule.
* **Postcondition:** Scans exclude or anonymize sensitive files according to rules.
* **Main Scenario:**

  1. User navigates to the Privacy Manager
  2. User defines privacy rules (e.g., ignore certain folders, file types, or keywords)
  3. The system validates and saves the rules
  4. During scans, the system enforces these rules to filter results
* **Extensions:**

  1. Invalid rule definition → system prompts user to correct it
  2. User disables privacy rules → system scans all files normally


## 4 Requirements, Testing, Requirement Verification

## Technology Stack and Testing Framework

The app uses **Electron** for the desktop shell and **React.js** with **TailwindCSS** for the UI. The backend is in **Python**, handling file scanning, metadata extraction, and analysis, with storage in **SQLite**. Libraries include **Pandas**, **OpenCV**, and **GitPython**, while visualizations use **Plotly.js** and **Recharts**.  

Testing is done with **pytest** (Python backend) and **Jest/Mocha** (React frontend). **Manual testing** covers usability, privacy, and other non-functional requirements.

| Requirement | Description | Test Cases | Who | H/M/E |
| ----- | ----- | ----- | ----- | ----- |
| File/Repo selection | User selects files/folders/repos for scanning | - Select valid folder → stored in system<br>- Select invalid path → error shown<br>- Cancel selection → no files added | La | Easy |
| Run Scan | System scans selected files, extracts metadata | - Scan folder with mixed files → metadata stored<br>- Resume after interruption<br>- Access denied file → logged & skipped | Ethan | Medium |
| Generate commit timeline | For repos, system extracts commit history & visualizes timeline | - Timeline generated for repo with commits<br>- Private/inaccessible repo → alert shown<br>- Large repo → progress updates, partial results | Dan | Hard |
| Build image portfolio | System extracts thumbnails/metadata & organizes portfolio | - Generate thumbnails for .jpg/.png<br>- Unsupported format → skipped & notify<br>- Export portfolio to PDF | Amani | Hard |
| Trace dataset evolution | Track datasets, notebooks, reports across versions | - Timeline shows dataset + linked notebooks<br>- Corrupted dataset → error logged, continue<br>- Export reproducibility report | Ethan | Hard |
| Dashboard visualization | Display timelines, stats, filters in React dashboard | - Results display after scan<br>- No data → prompt user to scan<br>- Filters update charts dynamically | La | Medium |
| Export report | Generate report in PDF/HTML/portfolio format | - PDF generated correctly<br>- Storage error → retry or fail gracefully<br>- User cancels export → nothing generated | Amani | Medium |
| Apply privacy rules | Users define & enforce privacy filters | - Define valid rule → applied in scans<br>- Invalid rule → error prompt<br>- Disable privacy → scans all files | Dan | Medium |
| Data persistence | SQLite stores metadata, history, rules | - Restart app → history preserved<br>- Corrupt DB → new DB created<br>- Query returns correct metadata | Ethan | Medium |
| Performance (non-functional) | Handle large repos/folders without major slowdown | - Scan 10k files under X minutes<br>- System doesn’t hang indefinitely<br>- Memory usage within threshold | La | Hard |
| Usability (non-functional) | UI must be intuitive, styled, and responsive | - Manual: user completes scan → view results<br>- Resizes gracefully on different screens<br>- Component error handled gracefully | Dan | Easy |
| Privacy (non-functional) | No file content stored, only metadata | - DB only contains metadata<br>- User can clear data on request<br>- Manual: verify logs contain no sensitive data | Amani | Medium |
