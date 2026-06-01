import sqlite3
import re
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Hisab Live Engine")

# Define what a single incoming message looks like
class IncomingSMS(BaseModel):
    text: str

# Helper Parsing Functions
def automatic_categorizer(text):
    text = text.lower()
    if any(w in text for w in ["swiggy", "zomato", "restaurant", "dine", "food"]):
        return "Food"
    if any(w in text for w in ["uber", "ola", "metro", "fuel", "petrol", "auto"]):
        return "Transport"
    if any(w in text for w in ["amazon", "flipkart", "blinkit", "myntra", "shop"]):
        return "Shopping"
    if any(w in text for w in ["electricity", "power", "bill", "utilities", "recharge"]):
        return "Utilities"
    return "Others"

def extract_amount(text):
    match = re.search(r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0

def extract_message_datetime(text):
    match1 = re.search(r"\d{2}-\d{2}-\d{2,4}\s+\d{2}:\d{2}:\d{2}", text)
    if match1: return match1.group(0)
    match2 = re.search(r"\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}", text)
    if match2: return match2.group(0)
    match3 = re.search(r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}", text)
    if match3: return match3.group(0)
    match4 = re.search(r"\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}", text)
    if match4: return match4.group(0)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_db_summary():
    conn = sqlite3.connect("hisab.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount), COUNT(*) FROM expenses GROUP BY category")
    rows = cursor.fetchall()
    conn.close()
    return [{"category": r[0], "total_amount": r[1], "transaction_count": r[2]} for r in rows]

# NEW ENDPOINT: Process a single live message
@app.post("/process-sms")
def process_single_sms(sms: IncomingSMS):
    amount = extract_amount(sms.text)
    category = automatic_categorizer(sms.text)
    msg_time = extract_message_datetime(sms.text)
    
    conn = sqlite3.connect("hisab.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO expenses (date, description, amount, category) VALUES (?, ?, ?, ?)",
            (msg_time, sms.text, amount, category)
        )
        conn.commit()
        status = "Saved successfully"
    except sqlite3.IntegrityError:
        status = "Skipped (Duplicate transaction)"
    finally:
        conn.close()
        
    return {
        "status": status,
        "parsed_data": {
            "time": msg_time,
            "amount": amount,
            "category": category,
            "text": sms.text
        }
    }

@app.get("/summary")
def read_summary():
    return {"expenses_summary": get_db_summary()}

@app.get("/", response_class=HTMLResponse)
def home_dashboard():
    summary_data = get_db_summary()
    tx_conn = sqlite3.connect("hisab.db")
    tx_cursor = tx_conn.cursor()
    tx_cursor.execute("SELECT date, description, amount, category FROM expenses ORDER BY id DESC")
    all_tx = tx_cursor.fetchall()
    tx_conn.close()

    summary_rows = "".join(f"<tr><td><b>{s['category']}</b></td><td>₹{s['total_amount']:.2f}</td><td>{s['transaction_count']}</td></tr>" for s in summary_data)
    tx_rows = "".join(f"<tr><td>{t[0]}</td><td>{t[1]}</td><td>₹{t[2]:.2f}</td><td><span class='badge'>{t[3]}</span></td></tr>" for t in all_tx)

    return f"""
    <html>
        <head>
            <title>Hisab Manager Dashboard</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; margin: 40px; background-color: #f5f7fb; color: #333; }}
                h1 {{ color: #1e293b; }} h2 {{ margin-top: 30px; color: #475569; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
                th {{ background-color: #0f172a; color: white; }}
                .badge {{ background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
                .container {{ max-width: 1000px; margin: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Hisab Budget Dashboard</h1>
                <h2>Category Summaries</h2>
                <table><tr><th>Category</th><th>Total Amount</th><th>Txn Count</th></tr>{summary_rows}</table>
                <h2>Recent Transactions</h2>
                <table><tr><th>Timestamp</th><th>Message Text</th><th>Amount</th><th>Category</th></tr>{tx_rows}</table>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
