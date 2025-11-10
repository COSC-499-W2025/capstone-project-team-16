import mysql.connector
from mysql.connector import Error
import uuid

# ---------- CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",                 # your MySQL username
    "password": "password",  # your MySQL password
    "database": "project_insight"
}


# ---------- CONNECTION ----------
def create_connection():
    """Connect to MySQL and create the database if it doesn't exist."""
    try:
        # Step 1: connect to MySQL server (no database)
        server_connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        if server_connection.is_connected():
            cursor = server_connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.close()
            server_connection.close()

        # Step 2: connect to the target database
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Connected to MySQL database")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None


# ---------- INITIAL SETUP ----------
def init_db():
    """Create necessary tables if they don't exist."""
    connection = create_connection()
    if not connection:
        return
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id CHAR(36) PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            display_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id CHAR(36) PRIMARY KEY,
            user_id CHAR(36),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    connection.commit()
    print("✅ Tables initialized successfully.")

    # Show existing tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("📋 Existing tables:")
    for (table_name,) in tables:
        print(f" - {table_name}")

    cursor.close()
    connection.close()


# ---------- CRUD HELPERS ----------
def add_user(email, name):
    connection = create_connection()
    if not connection:
        return
    cursor = connection.cursor()
    user_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO users (id, email, display_name) VALUES (%s, %s, %s)",
        (user_id, email, name)
    )
    connection.commit()
    cursor.close()
    connection.close()
    print(f"✅ Added user {name} ({user_id})")
    return user_id


def add_project(user_id, name, description):
    connection = create_connection()
    if not connection:
        return
    cursor = connection.cursor()
    project_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO projects (id, user_id, name, description) VALUES (%s, %s, %s, %s)",
        (project_id, user_id, name, description)
    )
    connection.commit()
    cursor.close()
    connection.close()
    print(f"✅ Added project {name} ({project_id})")
    return project_id


def get_projects(user_id):
    connection = create_connection()
    if not connection:
        return []
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects WHERE user_id = %s", (user_id,))
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results


# ---------- MAIN TEST ----------
if __name__ == "__main__":
    init_db()

    user_id = add_user("amani@example.com", "Amani Lugalla")
    add_project(user_id, "Artifact Analyzer", "Analyze creative digital projects.")
    add_project(user_id, "Portfolio Generator", "Creates résumé and project summaries.")

    print("\n📁 User projects:")
    for project in get_projects(user_id):
        print(f"- {project['name']} | {project['description']}")
