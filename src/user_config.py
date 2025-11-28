class UserConfig:
    """
    Represents persistent user preferences.
    Only ONE row will ever exist in the database.
    """

    def __init__(self, consent=False):
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

        conn.execute(
            """
            INSERT INTO user_config (id, consent)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET
                consent=excluded.consent
            """,
            (1 if self.consent else 0,),
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
        return cls(consent=bool(row[0]))

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
