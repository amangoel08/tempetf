import yfinance as yf
import pandas as pd
import streamlit as st
import time

# MUST BE FIRST
st.set_page_config(page_title="Private ETF Dashboard", layout="wide")

# 🔐 LOGIN SYSTEM
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

st.title("📊 ETF Dashboard (Dip Buy Strategy)")

etfs = {
    "HDFCSML250": "HDFCSML250.NS",
    "SETNIFTY": "SETFNIF50.NS",
    "SILVERBEES": "SILVERBEES.NS",
    "MOM30": "MOM30IETF.NS",
    "GOLD": "GOLDBEES.NS",
    "NASDAQ100": "MON100.NS"
}

# 🔘 Controls
col1, col2 = st.columns(2)

with col1:
    period = st.selectbox("Time Range", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)

with col2:
    auto_refresh = st.toggle("Auto Refresh (10s)")

# 📊 Loop ETFs
for name, symbol in etfs.items():
    st.subheader(name)

    hist = yf.Ticker(symbol).history(period=period)

    if hist.empty or len(hist) < 2:
        st.warning("Not enough data")
        continue

    df = hist.copy()

    # 📈 Chart
    st.line_chart(df["Close"])

    # 🔍 Price logic
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = latest["Close"]
    prev_price = prev["Close"]

    change_pct = ((price - prev_price) / prev_price) * 100

    # 🎯 Signal Logic
    signal = "HOLD"

    if change_pct <= -1:
        signal = "BUY"
        st.success(f"🟢 BUY Signal for {name} (Drop: {round(change_pct, 2)}%)")

    elif change_pct >= 1:
        signal = "SELL"
        st.error(f"🔴 SELL Signal for {name} (Rise: {round(change_pct, 2)}%)")

    else:
        st.info(f"⚪ HOLD for {name} ({round(change_pct, 2)}%)")

    # 📌 Metrics
    st.metric("Price", round(price, 2), f"{round(change_pct, 2)}%")
    st.write(f"Signal: {signal}")

    st.divider()

# 🔄 Optional Auto Refresh
if auto_refresh:
    time.sleep(10)
    st.rerun()