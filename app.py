import yfinance as yf
import pandas as pd
import streamlit as st

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
            st.success("Access granted. Reloading...")
            st.rerun()
        else:
            st.error("Wrong password")

# If not logged in → stop here
if not st.session_state.authenticated:
    login()
    st.stop()

# ---------------- DASHBOARD ----------------

st.title("📊 Live ETF Trading Dashboard")

etfs = {
    "HDFCSML250": "HDFCSML250.NS",
    "SETNIFTY": "SETFNIF50.NS",
    "SILVERBEES": "SILVERBEES.NS",
    "MOM30": "MOM30IETF.NS",
    "GOLD": "GOLDBEES.NS",
    "NASDAQ100": "MON100.NS"
}

data = []

for name, symbol in etfs.items():
    hist = yf.Ticker(symbol).history(period="2d")

    if len(hist) < 2:
        continue

    prev = hist["Close"].iloc[-2]
    curr = hist["Close"].iloc[-1]
    change = ((curr - prev) / prev) * 100

    data.append([name, round(curr, 2), round(change, 2)])

df = pd.DataFrame(data, columns=["ETF", "Price", "% Change"])

st.dataframe(df, use_container_width=True)

# 🔄 Proper Streamlit auto refresh
st.write("Auto-refresh every 10 seconds")
st.rerun()