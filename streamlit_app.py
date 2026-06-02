import streamlit as st
import sqlite3
import re
from datetime import datetime
from google import genai

# Page config
st.set_page_config(page_title="Hisab Budget Dashboard", page_icon="📊", layout="wide")

# Initialize Gemini Client (Streamlit picks up GEMINI_API_KEY from environment variables/secrets)
client = genai.Client()

# --- HELPER FUNCTIONS ---
def ai_production_categorizer(text: str) -> str:
    prompt = f"""
    Analyze the bank merchant context in this SMS and classify it into exactly ONE of these categories:
    Food, Transport, Shopping, Utilities, Medical, Entertainment, Others.
    Respond with ONLY the category name. Do not include extra text.
    Transaction Message: "{text}"
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        category = response.text.strip()
        valid = ["Food", "Transport", "Shopping", "Utilities", "Medical", "Entertainment", "Others"]
        if category in valid:
            return category
    except Exception as e:
        st.error(f"AI Error: {e}")
    return "Others"

def extract_amount(text):
    match = re.search(r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def extract_message_datetime(text):
    match_colon_date = re.search(r"\d{4}-\d{2}-\d{2}:\d{2}:\d{2}:\d{2}", text)
    if match_colon_date:
        return match_colon_date.group(0).replace(":", " ", 1)
    match1 = re.search(r"\d{2}-\d{2}-\d{2,4}\s+\d{2}:\d{2}:\d{2}", text)
    if match1: return match1.group(0)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- DATABASE ENGINE ---
@st.cache_resource
def get_connection():
    return sqlite3.connect("hisab.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            UNIQUE(date, description)
        )
    """)
    conn.commit()

# Initialize DB on start
init_db()

# --- STREAMLIT USER INTERFACE ---
st.title("📊 Hisab Budget Dashboard")

# Section 1: Add/Process manual transaction or SMS text simulation
st.subheader("📥 Process Transaction Text")
with st.form("sms_form", clear_on_submit=True):
    sms_text = st.text_area("Paste Transaction SMS here:", placeholder="Debited Rs.1,500 for shopping at Myntra on 2026-06-02...")
    submit_button = st.form_submit_button("Process and Save")

if submit_button and sms_text:
    amount = extract_amount(sms_text)
    msg_time = extract_message_datetime(sms_text)
    category = ai_production_categorizer(sms_text)
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (date, description, amount, category) VALUES (?, ?, ?, ?)",
            (msg_time, sms_text, amount, category)
        )
        conn.commit()
        st.success(f"✅ Saved! Category: **{category}** | Amount: **₹{amount:.2f}**")
    except sqlite3.IntegrityError:
        st.warning("⚠️ Skipped: Duplicate transaction message caught.")

# Fetch Data for Dashboard Layout
conn = get_connection()
cursor = conn.cursor()

# Get summary metrics
cursor.execute("SELECT category, SUM(amount), COUNT(*) FROM expenses GROUP BY category")
summary_data = cursor.fetchall()

# Get recent logs
cursor.execute("SELECT date, description, amount, category FROM expenses ORDER BY id DESC")
all_tx = cursor.fetchall()

# Section 2: Visual Metrics Dashboard
st.write("---")
st.subheader("🧮 Category Summaries")
if summary_data:
    cols = st.columns(len(summary_data))
    for idx, row in enumerate(summary_data):
        with cols[idx]:
            st.metric(label=row[0], value=f"₹{row[1]:,.2f}", delta=f"{row[2]} txns")
else:
    st.info("No transaction data available yet.")

# Section 3: Recent Transaction Log
st.subheader("⏱️ Recent Transactions")
if all_tx:
    import pandas as pd
    df = pd.DataFrame(all_tx, columns=["Timestamp", "Message Text", "Amount (₹)", "Category"])
    st.dataframe(df, use_container_width=True)
else:
    st.text("No records found.")
