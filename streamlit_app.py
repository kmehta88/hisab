import streamlit as st
import re
from datetime import datetime
from google import genai
from sqlalchemy import text

# 1. Page Configurations
st.set_page_config(page_title="Hisab Monthly Budget Dashboard", page_icon="📊", layout="wide")

# 2. Initialize Gemini Client
client = genai.Client()

# 3. Secure Cloud Database Connection
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

init_db()

# --- UTILITY METHODS ---
def ai_production_categorizer(text: str) -> str:
    prompt = f"""
    Analyze the bank merchant context in this SMS and classify it into exactly ONE of these categories:
    Food, Transport, Shopping, Utilities, Medical, Entertainment, Others.
    Respond with ONLY the category name. Do not include extra text.
    Transaction Message: "{text}"
    """
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        category = response.text.strip()
        valid = ["Food", "Transport", "Shopping", "Utilities", "Medical", "Entertainment", "Others"]
        if category in valid: return category
    except Exception as e:
        st.error(f"AI Error: {e}")
    return "Others"

def extract_amount(text):
    match = re.search(r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    return float(match.group(1).replace(",", "")) if match else 0.0

def extract_message_datetime(text):
    match_colon_date = re.search(r"\d{4}-\d{2}-\d{2}:\d{2}:\d{2}:\d{2}", text)
    if match_colon_date: return match_colon_date.group(0).replace(":", " ", 1)
    match1 = re.search(r"\d{2}-\d{2}-\d{2,4}\s+\d{2}:\d{2}:\d{2}", text)
    if match1: return match1.group(0)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- SIDEBAR: MONTH SELECTION ---
# Fetch distinct available months dynamically from the database using SQL SUBSTRING
months_df = db_conn.query("""
    SELECT DISTINCT SUBSTRING(date FROM 1 FOR 7) as month_year 
    FROM expenses 
    ORDER BY month_year DESC;
""", ttl="0m")

# Fallback to current month if database is empty
if not months_df.empty:
    available_months = months_df['month_year'].tolist()
else:
    available_months = [datetime.now().strftime("%Y-%m")]

st.sidebar.header("🗓️ Filter Options")
selected_month = st.sidebar.selectbox("Select Month:", available_months)


# --- MAIN USER INTERFACE ---
st.title("📊 Hisab Budget Dashboard")
st.subheader(f"📅 View for Month: {selected_month}")

# Input SMS Form
with st.form("sms_form", clear_on_submit=True):
    sms_text = st.text_area("Paste Transaction SMS here:")
    submit_button = st.form_submit_button("Process and Save")

if submit_button and sms_text:
    amount = extract_amount(sms_text)
    msg_time = extract_message_datetime(sms_text)
    category = ai_production_categorizer(sms_text)
    
    try:
        with db_conn.session as session:
            session.execute(
                text("""
                    INSERT INTO expenses (date, description, amount, category) 
                    VALUES (:date, :description, :amount, :category);
                """),
                {"date": msg_time, "description": sms_text, "amount": amount, "category": category}
            )
            session.commit()
        st.success(f"✅ Saved to Supabase! Category: **{category}** | Amount: **₹{amount:.2f}**")
        st.rerun() # Rerun to refresh the selected month charts immediately
    except Exception as e:
        st.warning("⚠️ Skipped: Duplicate transaction message caught or database connection hiccup.")


# --- MONTH-SPECIFIC QUERIES ---
# 1. Fetch Summary filtered by the chosen month
summary_df = db_conn.query(f"""
    SELECT category, SUM(amount) as total_amount, COUNT(*) as transaction_count 
    FROM expenses 
    WHERE SUBSTRING(date FROM 1 FOR 7) = '{selected_month}'
    GROUP BY category;
""", ttl="0m")

# 2. Fetch Detailed Ledger filtered by the chosen month
tx_df = db_conn.query(f"""
    SELECT date as "Timestamp", description as "Message Text", amount as "Amount (₹)", category as "Category" 
    FROM expenses 
    WHERE SUBSTRING(date FROM 1 FOR 7) = '{selected_month}'
    ORDER BY id DESC;
""", ttl="0m")


# --- DISPLAY METRICS ---
st.write("---")
st.subheader("🧮 Monthly Category Summaries")
if not summary_df.empty:
    cols = st.columns(len(summary_df))
    for idx, row in summary_df.iterrows():
        with cols[idx]:
            st.metric(
                label=row['category'], 
                value=f"₹{row['total_amount']:,.2f}", 
                delta=f"{row['transaction_count']} txns",
                delta_color="off" # Keeps delta styling neutral
            )
    
    # Quick grand total highlight
    total_monthly_spend = summary_df['total_amount'].sum()
    st.info(f"💰 **Total Spend for {selected_month}:** ₹{total_monthly_spend:,.2f}")
else:
    st.info(f"No transaction data found for the month: {selected_month}")

# Display Data Table Logs for selected month
st.subheader("⏱️ Monthly Ledger Logs")
if not tx_df.empty:
    st.dataframe(tx_df, width="stretch")
else:
    st.text("No records found for this period.")
