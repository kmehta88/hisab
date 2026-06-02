import streamlit as st
from sqlalchemy import text

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
    # Passing the raw string directly into query() bypasses the UnhashableParamError completely
    return db_conn.query("""
        SELECT category, SUM(amount) as total_amount, COUNT(*) as transaction_count 
        FROM expenses 
        GROUP BY category;
    """, ttl="0m")

def fetch_all_transactions():
    return db_conn.query("""
        SELECT date as "Timestamp", description as "Message Text", amount as "Amount (₹)", category as "Category" 
        FROM expenses 
        ORDER BY id DESC;
    """, ttl="0m")
    
