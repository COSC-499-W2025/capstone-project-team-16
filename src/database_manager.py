import sqlite3
from datetime import datetime

# The database file will appear in the project folder
DB_NAME = "skillscope.db"

def save_scan_results(results_list):
    """
    Receives the list of dictionaries from analyze_projects()
    and commits them to the SQLite database.
    """
    if not results_list:
        print("No project data to save.")
        return

    conn = None
    try:
        # 1. Connect (Auto-creates file if missing)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 2. Ensure Table Exists
        # Match the columns to the keys provided by alternative_analysis.py
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date TEXT,
                project_name TEXT,
                total_files INTEGER,
                duration_days INTEGER,
                code_files INTEGER,
                test_files INTEGER,
                doc_files INTEGER,
                design_files INTEGER,
                languages TEXT,
                frameworks TEXT,
                skills TEXT,
                is_collaborative TEXT,
                score INTEGER
            )
        ''')

        # 3. Prepare Data
        # Use .get() here. 
        # If code breaks and stops sending a 'score', default to 0.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        
        for p in results_list:
            rows.append((
                timestamp,
                p.get("project", "Unknown"), 
                p.get("total_files", 0),
                p.get("duration_days", 0),
                p.get("code_files", 0),
                p.get("test_files", 0),
                p.get("doc_files", 0),
                p.get("design_files", 0),
                p.get("languages", ""),
                p.get("frameworks", ""),
                p.get("skills", ""),
                p.get("is_collaborative", "No"),
                p.get("score", 0)
            ))

        # 4. Insert Data
        cursor.executemany('''
            INSERT INTO project_summaries (
                scan_date, project_name, total_files, duration_days, 
                code_files, test_files, doc_files, design_files, 
                languages, frameworks, skills, is_collaborative, score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', rows)

        conn.commit()
        print(f"Successfully saved {len(rows)} record(s) to database '{DB_NAME}'.")
    
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        if conn:
            conn.close()