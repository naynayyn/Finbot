import sqlite3
from datetime import datetime

DB_PATH = "finbot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL, category TEXT, description TEXT,
        date TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY,
        monthly_limit REAL
    )""")
    conn.commit()
    conn.close()

def log_expense(amount: float, category: str, description: str = ""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO expenses (amount, category, description, date, created_at) VALUES (?,?,?,?,?)",
        (amount, category, description, datetime.now().strftime("%Y-%m-%d"), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_monthly_summary() -> dict:
    conn = sqlite3.connect(DB_PATH)
    month = datetime.now().strftime("%Y-%m")
    rows = conn.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category",
        (f"{month}%",)
    ).fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def set_budget(category: str, limit: float):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO budgets (category, monthly_limit) VALUES (?,?)",
        (category, limit)
    )
    conn.commit()
    conn.close()

def get_budget_status() -> list:
    conn = sqlite3.connect(DB_PATH)
    month = datetime.now().strftime("%Y-%m")
    rows = conn.execute("""
        SELECT b.category, COALESCE(SUM(e.amount),0) as spent, b.monthly_limit
        FROM budgets b
        LEFT JOIN expenses e ON b.category=e.category AND e.date LIKE ?
        GROUP BY b.category
    """, (f"{month}%",)).fetchall()
    conn.close()
    return [{"category": r[0], "spent": r[1], "limit": r[2],
             "percent": round(r[1]/r[2]*100)} for r in rows]
