import streamlit as st
from database import init_db, add_expense, get_all_expenses

# Initialize database on app startup
init_db()

# App interface
st.title("Hisab Tracker")
# ... your inputs here ...

st.set_page_config(page_title="Hisab App", page_icon="🧮")

st.title("📊 Hisab (Expense & Accounts Tracker)")
st.write("Welcome to your personal ledger. Start tracking your inputs below.")

# Quick sample placeholder layout for your new app
amount = st.number_input("Enter Amount:", min_value=0.0, step=10.0)
category = st.selectbox("Category:", ["Food", "Rent", "Travel", "Utilities", "Other"])

if st.button("Add Record"):
    st.success(f"Added record: {category} - ₹{amount}")
