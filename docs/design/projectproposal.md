## **Features Proposal for Project Option XX**
Team Number: 16
Team Members: Ethan Sturek 21282611, Lastname SN1234567, Firstname Lastname SN1234567, Firstname Lastname SN1234567,
Firstname Lastname SN1234567, Firstname Lastname SN1234567

## **1 Project Scope and Usage Scenario**
**Explain in one paragraph the basic usage scenario you intend to cover. This scenario may involve
multiple user groups – be sure to clearly identify them (for example, an educational app may have
students, instructors, and administrators as three different user groups.**

## **2 Proposed Solution**
**Explain in one to two paragraphs what your solution is. Highlight special features, or special
technologies, that you are using. What is your value proposition? What do you think you will do
better in comparison to other teams? State your main points here clearly. Be concise and catch
your reader’s attention immediately.**

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
