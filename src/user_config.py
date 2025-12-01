class UserConfig:
    """
    Represents persistent user preferences.
    Only ONE row will ever exist in the database.
    """

    def __init__(self, consent=False):
        # Store consent as a boolean internally
        self.consent = consent

    # ---------------------------------------------------------
    # Save (insert or update) the config
    # ---------------------------------------------------------
    def save_to_db(self, conn=None):
        import sqlite3
        import db

        close_conn = False
        if conn is None:
            conn = sqlite3.connect(db.DB_NAME)
            close_conn = True
        conn.row_factory = sqlite3.Row
        db.ensure_db_initialized(conn)

        # Convert boolean to "Yes"/"No" for database storage
        consent_str = "Yes" if self.consent else "No"

        conn.execute(
            """
            INSERT INTO user_config (id, consent)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET
                consent=excluded.consent
            """,
            (consent_str,),
        )
        conn.commit()

        if close_conn:
            conn.close()

    # ---------------------------------------------------------
    # Load config (returns UserConfig or None)
    # ---------------------------------------------------------
    @classmethod
    def load_from_db(cls, conn=None):
        import sqlite3
        import db

        close_conn = False
        if conn is None:
            conn = sqlite3.connect(db.DB_NAME)
            close_conn = True
        conn.row_factory = sqlite3.Row
        db.ensure_db_initialized(conn)

        row = conn.execute("SELECT consent FROM user_config WHERE id = 1").fetchone()
        if close_conn:
            conn.close()

        if row is None:
            return None

        # Convert "Yes"/"No" back to boolean
        consent_bool = True if row["consent"] == "Yes" else False
        return cls(consent=consent_bool)

    # ---------------------------------------------------------
    # Delete config
    # ---------------------------------------------------------
    def delete_from_db(self, conn=None):
        import sqlite3
        import db

        close_conn = False
        if conn is None:
            conn = sqlite3.connect(db.DB_NAME)
            close_conn = True
        conn.row_factory = sqlite3.Row
        db.ensure_db_initialized(conn)

        conn.execute("DELETE FROM user_config WHERE id = 1")
        conn.commit()

        if close_conn:
            conn.close()
