import sqlite3


def init_db():
    conn = sqlite3.connect("hisab.db")
    cursor = conn.cursor()

    # Added UNIQUE constraint on date and description to prevent duplicates
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            UNIQUE(date, description)
        )
    """
    )

    conn.commit()
    conn.close()
    print("Database initialized with Unique Constraints.")


if __name__ == "__main__":
    init_db()
