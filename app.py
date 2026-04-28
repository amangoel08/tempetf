import yfinance as yf
import pandas as pd
import streamlit as st
import sqlite3
import requests
from datetime import date, datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
import holidays
from dotenv import load_dotenv
import os
import pytz

# Load environment variables
load_dotenv()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ETF Tracker Pro", layout="wide")

PASSWORD = os.getenv("PASSWORD", "default_password")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Store last check time
last_check_time = None

# Market holidays
india_holidays = holidays.India(years=2026)

CUSTOM_HOLIDAYS = {
    date(2026, 5, 15),   # Eid ul-Fitr
}

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    """Send message via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Telegram message sent successfully")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Telegram send error: {e}")

def is_trading_day(check_date=None):
    """Check if market is open (weekday and not holiday)"""
    if check_date is None:
        check_date = date.today()
    
    is_weekday = check_date.weekday() < 5
    is_not_holiday = (check_date not in india_holidays) and (check_date not in CUSTOM_HOLIDAYS)
    
    return is_weekday and is_not_holiday

def is_check_time():
    """Check if current time is 14:30"""
    now = datetime.now().time()
    check_time = time(14, 30)
    # Allow 1 minute window (14:30 to 14:31)
    return check_time <= now < time(14, 31)

# ---------------- ETF LIST ----------------
ETFS = {
    "HDFCSML250": {"label": "🇮🇳 HDFCSML250", "symbol": "HDFCSML250.NS"},
    "NIFTY50": {"label": "🇮🇳 NIFTY50 ETF", "symbol": "SETFNIF50.NS"},
    "SILVER": {"label": "🥈 SILVER", "symbol": "SILVERBEES.NS"},
    "MOMENTUM": {"label": "📈 MOMENTUM", "symbol": "MOM30IETF.NS"},
    "GOLD": {"label": "🥇 GOLD", "symbol": "GOLDBEES.NS"},
    "NASDAQ100": {"label": "🇺🇸 NASDAQ100", "symbol": "MON100.NS"}
}

# ---------------- DB ----------------
conn = sqlite3.connect("portfolio.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id TEXT PRIMARY KEY,
    capital REAL,
    invested REAL,
    units REAL,
    last_update TEXT
)
""")
conn.commit()

# ---------------- INIT ----------------
def init_db():
    for etf in ETFS:
        cursor.execute("""
        INSERT OR IGNORE INTO portfolio VALUES (?, ?, ?, ?, ?)
        """, (etf, 200, 0, 0, ""))
    conn.commit()

init_db()

# ---------------- LOAD ----------------
def load_db():
    cursor.execute("SELECT * FROM portfolio")
    rows = cursor.fetchall()

    db = {}
    for r in rows:
        db[r[0]] = {
            "capital": r[1],
            "invested": r[2],
            "units": r[3],
            "last_update": r[4]
        }
    return db

# ---------------- SAVE ----------------
def save_db(etf, p):
    cursor.execute("""
    INSERT INTO portfolio VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        capital=excluded.capital,
        invested=excluded.invested,
        units=excluded.units,
        last_update=excluded.last_update
    """, (etf, p["capital"], p["invested"], p["units"], p["last_update"]))
    conn.commit()

# ---------------- LOGIN ----------------
if "auth" not in st.session_state:
    st.session_state.auth = False

def login():
    st.title("🔐 Login")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()

if not st.session_state.auth:
    login()
    st.stop()

# ---------------- STATE ----------------
if "db" not in st.session_state:
    st.session_state.db = load_db()

db = st.session_state.db

# Store last check time in session state
if "last_check" not in st.session_state:
    st.session_state.last_check = None

# Only proceed if it's 14:30 and trading day
current_time = datetime.now()
if is_trading_day() and is_check_time():
    if st.session_state.last_check != current_time.date():
        st.session_state.last_check = current_time.date()
        proceed_with_checks = True
    else:
        proceed_with_checks = False
else:
    proceed_with_checks = False

if not proceed_with_checks:
    st.warning(f"⏰ Price checks happen at 14:30 on trading days only. Current time: {current_time.strftime('%H:%M')}")
    st.stop()

# ---------------- UI ----------------
st.title("📊 ETF Tracker")

table = []
buy_cards = []

# ---------------- MAIN LOOP ----------------
for etf_id, meta in ETFS.items():

    label = meta["label"]
    symbol = meta["symbol"]

    hist = yf.Ticker(symbol).history(period="2d")
    if len(hist) < 2:
        continue

    prev = hist["Close"].iloc[-2]
    curr = hist["Close"].iloc[-1]

    # ✅ FIX 1: Proper difference display
    diff = curr - prev
    diff_pct = (diff / prev) * 100

    p = db[etf_id]

    signal = "HOLD"
    already_bought = p["units"] > 0

    # ---------------- BUY ----------------
    if diff_pct <= -1:
        signal = "BUY"
        invest = p["capital"]

        buy_cards.append((label, diff_pct, invest))

        if not already_bought:
            if st.button(f"Buy {label}", key=etf_id):

                units = invest / curr

                p["capital"] = 200
                p["invested"] += invest
                p["units"] += units
                p["last_update"] = str(date.today())

                db[etf_id] = p
                save_db(etf_id, p)

                send_telegram(
                    f"<b>📢 BUY ALERT</b>\n<b>{label}</b>\nInvest: ₹{invest}\nPrice: {round(curr,2)}"
                )

                st.success(f"Bought {label}")
                st.rerun()

    # ---------------- CALC ----------------
    value = p["units"] * curr
    pnl = value - p["invested"]
    pnl_pct = (pnl / p["invested"] * 100) if p["invested"] else 0

    table.append([
        label,
        round(curr, 2),

        # ✅ FIX 2: show correct daily diff
        round(diff, 2),
        round(diff_pct, 2),

        signal,
        p["capital"],
        p["invested"],
        round(value, 0),
        round(pnl, 0),
        round(pnl_pct, 2)
    ])

# ---------------- BUY CARDS ----------------
st.subheader("🟢 BUY Signals")

if buy_cards:
    for n, chg, amt in buy_cards:
        st.markdown(f"""
        <div style="background:#28a745;padding:10px;border-radius:8px;margin:5px;color:white">
        <b>{n}</b><br>
        Change: {round(chg,2)}%<br>
        💰 Invest: ₹{amt}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No BUY signals")

# ---------------- TABLE ----------------
df = pd.DataFrame(table, columns=[
    "ETF",
    "Price",
    "Diff ₹",
    "Diff %",
    "Signal",
    "Next Invest",
    "Invested",
    "Value",
    "PnL ₹",
    "PnL %"
])

st.subheader("📊 Portfolio Overview")
st.dataframe(df, use_container_width=True)

# ---------------- SUMMARY ----------------
st.subheader("💰 Summary")
st.metric("Invested", df["Invested"].sum())
st.metric("Value", df["Value"].sum())
st.metric("PnL", df["Value"].sum() - df["Invested"].sum())