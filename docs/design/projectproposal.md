## **Features Proposal for Project Option XX**
Team Number: 16
Team Members: Ethan Sturek 21282611, La Wunn Soe 69493971, Firstname Lastname SN1234567, Firstname Lastname SN1234567,
Firstname Lastname SN1234567, Firstname Lastname SN1234567

## **1 Project Scope and Usage Scenario**
**Explain in one paragraph the basic usage scenario you intend to cover. This scenario may involve
multiple user groups – be sure to clearly identify them (for example, an educational app may have
students, instructors, and administrators as three different user groups.**

The basic usage scenario for this project is to provide people, specifically programmers, creatives (such as artists, designers, and photographers), and data analysts with a way to mine and analyze their own digital works and to better understand and present their contributions. A programmer might scan their repositories to generate a timeline of commits and code growth for use in interviews, while a creative could collect images, sketches, and media drafts into an automatically organized portfolio. Similarly, a data analyst could trace the evolution of datasets, notebooks, and reports to demonstrate methodology and reproducibility. In all cases, the system will allow users to scan selected files, extract meaningful metadata, and generate visual dashboards or exportable reports, helping them showcase their productivity, reflect on their processes, and organize their work histories while respecting privacy.

## **2 Proposed Solution**
**Explain in one to two paragraphs what your solution is. Highlight special features, or special
technologies, that you are using. What is your value proposition? What do you think you will do
better in comparison to other teams? State your main points here clearly. Be concise and catch
your reader’s attention immediately.**

Our solution is a system for mining and analyzing personal digital works including code repositories, documents, notes, design files, and media. The system scans user-selected locations, extracts meaningful data, and organizes results into a structured database. An analysis engine then generates insights such as timelines, productivity trends, and project evolution, which are presented back to the user through an interactive dashboard. Users can also export professional-looking portfolios or reports directly from there. Privacy rules will also be applied at every step to make sure that sensitive files are never exposed.

What makes our approach unique is the combination of automation, visualization, and privacy control. Unlike a simple file organizer, our system not only collects and classifies files but also transforms them into interpretable insights and exportable outputs that highlight a user’s contributions. Key features include an integrated Privacy Manager, visual dashboards, and a flexible exporter that can produce shareable reports. Our value proposition is to give users a tool that helps them showcase their work, reflect on their growth, and stay in control of their data. Compared to other teams, we believe our strength lies in balancing technical depth (data extraction, analysis, visualization) with usability and ethical awareness, making the system both practical and trustworthy.

## **3 Use Cases**
**Based on the usage scenario, describe all the use cases in detail. Do this by providing a UML use
case diagram. Then for each use case in your diagram, identify: the name of the use case, the
primary actor, a general description, the precondition, the postcondition, the main scenario, and
possible extensions to consider. Below is an example of a use case description.**

**Use Case 1: Create a Semester [Example]**
- **Primary actor:** Administrator
- **Description:** The process of creating a new semester.
- **Precondition:** The user must have an administrator role and be logged into the system.
- **Postcondition:** A new semester is created and saved in the database.
- **Main Scenario:**
    <ol>
    <li>Administrator clicks on the “Add semester” button </li>
    <li>Administrator enters the semester details (e.g., name, start date, and end date)</li>
    <li>Administrator submits the form</li>
    <li>The system validates the input data</li>
    <li>If the data is valid, the new semester is created</li>
    <li>Semester object and information is saved to the database</li>
    <li>The system notifies the administrator about the creation of the semester</li>
    </ol>
- **Extensions:** 
    <ol>
    <li>Invalid data is entered in Step 2. System notifies the user that invalid data was entered and repopulates the form with the data that the user previously tried to enter. </li>
    <li>etc.</li>
    </ol>
## 4 Requirements, Testing, Requirement Verification
**Start by mentioning your technology stack and test framework. Then use the example table below
to identify the requirements, test cases, and people assigned to work on those requirements.**
- Based on your use cases above, flush out the necessary requirements. These use cases will only identify
functional requirements. You will want to think about the usage scenario and the client’s needs to identify
non-functional requirements also.
- For each requirement, develop test cases - positive and negative cases - that can be written in the code base
and automated. While non-functional requirements such as “usability” will require manual testing (not by
your team), most of the requirements should have automatable test cases.
- Discuss with your teams the difficulty of each requirement and who wants to be assigned to them. Choose
one of: hard, medium, or easy and put it in the column for “H/D/E”.

| Requirement | Description | Test Cases | Who | H/M/E |
| ----- | ----- | ----- | ----- | ----- |
| Short phrase or sentence | Description of the feature, the steps involved, the complexity of it, potential difficulties | <ul> <li>test case 1</li> <li>test case 2 </li> <li> · · · </li></ul> | Bob | Hard |
| ... | | | | |
| etc. | | | | |
