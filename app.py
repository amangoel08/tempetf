import yfinance as yf
import pandas as pd
import streamlit as st
import time

# MUST BE FIRST
st.set_page_config(page_title="ETF Signals", layout="wide")

# 🔐 LOGIN
PASSWORD = "mysecret123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("🔐 Login Required")
    pwd = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Wrong password")

if not st.session_state.authenticated:
    login()
    st.stop()

# ---------------- DASHBOARD ----------------

st.title("📊 ETF Signals (Yesterday vs Today)")

etfs = {
    "HDFCSML250": "HDFCSML250.NS",
    "SETNIFTY": "SETFNIF50.NS",
    "SILVERBEES": "SILVERBEES.NS",
    "MOM30": "MOM30IETF.NS",
    "GOLD": "GOLDBEES.NS",
    "NASDAQ100": "MON100.NS"
}

# 🔘 Auto-refresh toggle
auto_refresh = st.toggle("Auto Refresh (10s)")

data = []

for name, symbol in etfs.items():
    hist = yf.Ticker(symbol).history(period="2d")

    if len(hist) < 2:
        continue

    yesterday = hist["Close"].iloc[-2]
    today = hist["Close"].iloc[-1]

    change_pct = ((today - yesterday) / yesterday) * 100

    # 🎯 Signal
    if change_pct <= -1:
        signal = "BUY"
    elif change_pct >= 1:
        signal = "SELL"
    else:
        signal = "HOLD"

    data.append([
        name,
        round(yesterday, 2),
        round(today, 2),
        round(change_pct, 2),
        signal
    ])

# 📊 Table
df = pd.DataFrame(
    data,
    columns=["ETF", "Yesterday", "Today", "% Change", "Signal"]
)

st.dataframe(df, use_container_width=True)

# 🔄 Optional refresh
if auto_refresh:
    time.sleep(10)
    st.rerun()