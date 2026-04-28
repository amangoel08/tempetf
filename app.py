import yfinance as yf
import pandas as pd
import streamlit as st
import time
import streamlit as st

st.set_page_config(page_title="Private ETF Dashboard")

# 🔐 Simple login system
PASSWORD = "mysecret123"  # change this

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.success("Access granted")
        else:
            st.error("Wrong password")

if not st.session_state.authenticated:
    login()
    st.stop()
st.set_page_config(page_title="ETF Live Dashboard", layout="wide")

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

# 🔄 Auto refresh every 10 seconds
time.sleep(10)
st.rerun()