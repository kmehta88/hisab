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
from sqlalchemy import text # <-- Crucial import for modern Streamlit SQL connections

db_conn = st.connection("postgresql", type="sql")

def init_db():
    with db_conn.session as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount NUMERIC,
                category TEXT,
                UNIQUE(date, description)
            );
        """))
        session.commit()

def add_expense(msg_time, sms_text, amount, category):
    with db_conn.session as session:
        session.execute(
            text("""
                INSERT INTO expenses (date, description, amount, category) 
                VALUES (:date, :description, :amount, :category);
            """),
            {"date": msg_time, "description": sms_text, "amount": amount, "category": category}
        )
        session.commit()

def fetch_summary():
    # ttl="0m" tells Streamlit NEVER to cache this read, so a page reload shows fresh data instantly
    return db_conn.query(text("""
        SELECT category, SUM(amount) as total_amount, COUNT(*) as transaction_count 
        FROM expenses 
        GROUP BY category;
    """), ttl="0m")

def fetch_all_transactions():
    return db_conn.query(text("""
        SELECT date as "Timestamp", description as "Message Text", amount as "Amount (₹)", category as "Category" 
        FROM expenses 
        ORDER BY id DESC;
    """), ttl="0m")
