from datetime import datetime
import re
import sqlite3


def automatic_categorizer(text):
    text = text.lower()
    if any(w in text for w in ["swiggy", "zomato", "restaurant", "dine"]):
        return "Food"
    if any(w in text for w in ["uber", "ola", "metro", "fuel", "petrol"]):
        return "Transport"
    if any(w in text for w in ["amazon", "flipkart", "blinkit", "myntra"]):
        return "Shopping"
    if any(w in text for w in ["electricity", "power", "bill", "utilities"]):
        return "Utilities"
    return "Others"


def extract_amount(text):
    match = re.search(r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0


def process_mock_sms_file(file_path):
    conn = sqlite3.connect("hisab.db")
    cursor = conn.cursor()

    # Using a fixed date string for mock data so testing duplicates is easier
    mock_date = "2026-06-02 12:00:00"

    print(f"--- Processing {file_path} ---")

    try:
        with open(file_path, "r") as file:
            for line in file:
                sms_text = line.strip()
                if not sms_text:
                    continue

                amount = extract_amount(sms_text)
                category = automatic_categorizer(sms_text)

                # INSERT OR IGNORE automatically skips duplicates safely
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO expenses (date, description, amount, category) 
                    VALUES (?, ?, ?, ?)
                """,
                    (mock_date, sms_text, amount, category),
                )

                if cursor.rowcount > 0:
                    print(f"Saved: Rs.{amount} -> [{category}]")
                else:
                    print(f"Skipped (Duplicate): '{sms_text[:20]}...'")

        conn.commit()
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
    finally:
        conn.close()
    print("--- Processing Complete ---")


if __name__ == "__main__":
    process_mock_sms_file("mock_sms.txt")
