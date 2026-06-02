import sqlite3
import streamlit as st

# 1. Cache the connection function so Streamlit doesn't recreate it on every click
@st.cache_resource
def get_connection():
    # check_same_thread=False is REQUIRED for SQLite in multi-threaded web apps like Streamlit
    return sqlite3.connect("hisab.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
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

# 2. Function to insert data (with try/except to handle your UNIQUE constraint safely)
def add_expense(date, description, amount, category):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (date, description, amount, category) VALUES (?, ?, ?, ?)",
            (date, description, amount, category)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This catches your UNIQUE(date, description) constraint if a duplicate is entered
        return False

# 3. Function to view data
def get_all_expenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    return cursor.fetchall()
