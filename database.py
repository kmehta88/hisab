# import sqlite3
# import streamlit as st

# # 1. Cache the connection function so Streamlit doesn't recreate it on every click
# @st.cache_resource
# def get_connection():
#     # check_same_thread=False is REQUIRED for SQLite in multi-threaded web apps like Streamlit
#     return sqlite3.connect("hisab.db", check_same_thread=False)

# def init_db():
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         """
#         CREATE TABLE IF NOT EXISTS expenses (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             date TEXT,
#             description TEXT,
#             amount REAL,
#             category TEXT,
#             UNIQUE(date, description)
#         )
#         """
#     )
#     conn.commit()

# # 2. Function to insert data (with try/except to handle your UNIQUE constraint safely)
# def add_expense(date, description, amount, category):
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute(
#             "INSERT INTO expenses (date, description, amount, category) VALUES (?, ?, ?, ?)",
#             (date, description, amount, category)
#         )
#         conn.commit()
#         return True
#     except sqlite3.IntegrityError:
#         # This catches your UNIQUE(date, description) constraint if a duplicate is entered
#         return False

# # 3. Function to view data
# def get_all_expenses():
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
#     return cursor.fetchall()


import streamlit as st

# 1. Initialize the Secure Cloud Database Connection
# This automatically reads from the [connections.postgresql] secret you saved
db_conn = st.connection("postgresql", type="sql")

def init_db():
    # PostgreSQL syntax uses SERIAL instead of AUTOINCREMENT
    with db_conn.session as session:
        session.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount NUMERIC,
                category TEXT,
                UNIQUE(date, description)
            );
        """)
        session.commit()

def add_expense(date, description, amount, category):
    try:
        with db_conn.session as session:
            session.execute(
                """
                INSERT INTO expenses (date, description, amount, category) 
                VALUES (:date, :description, :amount, :category)
                """,
                {"date": date, "description": description, "amount": amount, "category": category}
            )
            session.commit()
        return True
    except Exception as e:
        # Handles duplicate entries safely (PostgreSQL throws UniqueViolation errors)
        return False

def get_summary_data():
    # Streamlit sql connection allows direct querying into a clean pandas DataFrame
    query = """
        SELECT category, SUM(amount) as total_amount, COUNT(*) as transaction_count 
        FROM expenses 
        GROUP BY category
    """
    return db_conn.query(query, ttl="0m") # ttl="0m" forces fresh data fetch every time

def get_all_transactions():
    query = "SELECT date, description, amount, category FROM expenses ORDER BY id DESC"
    return db_conn.query(query, ttl="0m")
