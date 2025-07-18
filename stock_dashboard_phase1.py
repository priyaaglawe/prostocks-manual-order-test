# main_app.py

import streamlit as st
import pandas as pd
from prostocks_connector import ProStocksAPI
from dashboard_logic import load_settings, save_settings, load_credentials
from datetime import datetime, time

# 🧱 Page Layout
st.set_page_config(page_title="Auto Intraday Trading", layout="wide")
st.title("📈 Automated Intraday Trading System")

# === Load and Apply Settings (only once)
if "settings_loaded" not in st.session_state:
    st.session_state.update(load_settings())
    st.session_state["settings_loaded"] = True

# === Load Credentials from .env
creds = load_credentials()

# ✅ Approved stock list
APPROVED_STOCK_LIST = [
    "LTFOODS", "HSCL", "REDINGTON", "FIRSTCRY", "GSPL", "ATGL", "HEG", "RAYMOND", "GUJGASLTD",
    "TRITURBINE", "ADANIPOWER", "ELECON", "JIOFIN", "USHAMART", "INDIACEM", "HINDPETRO", "SONATSOFTW"
]

# 🔐 Sidebar Login
with st.sidebar:
    st.header("🔐 ProStocks Login")
    with st.form("ProStocksLoginForm"):
        uid = st.text_input("User ID", value=creds["uid"])
        pwd = st.text_input("Password", type="password", value=creds["pwd"])
        factor2 = st.text_input("PAN / DOB", value=creds["factor2"])
        vc = st.text_input("Vendor Code", value=creds["vc"] or uid)
        api_key = st.text_input("API Key", type="password", value=creds["api_key"])
        imei = st.text_input("MAC Address", value=creds["imei"])
        base_url = st.text_input("Base URL", value=creds["base_url"])
        apkversion = st.text_input("APK Version", value=creds["apkversion"])

        submitted = st.form_submit_button("🔐 Login")

        if submitted:
            try:
                ps_api = ProStocksAPI(uid, pwd, factor2, vc, api_key, imei, base_url, apkversion)
                success, msg = ps_api.login()
                if success:
                    st.session_state["ps_api"] = ps_api
                    st.success("✅ Login Successful")
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {msg}")
            except Exception as e:
                st.error(f"❌ Exception: {e}")

# 🔓 Logout button if already logged in
if "ps_api" in st.session_state:
    st.markdown("---")
    if st.button("🔓 Logout"):
        del st.session_state["ps_api"]
        st.success("✅ Logged out successfully")
        st.rerun()

# === Tabs Layout
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ Trade Controls", 
    "📊 Dashboard", 
    "📈 Market Data",
    "📐 Indicator Settings & View"
])


# === Tab 1: Trade Control Panel ===
with tab1:
    st.subheader("⚙️ Step 0: Trading Control Panel")

    # ✅ Unique keys for toggles
    master = st.toggle("✅ Master Auto Buy + Sell", value=st.session_state.get("master_auto", True), key="master_toggle")
    auto_buy = st.toggle("▶️ Auto Buy Enabled", value=st.session_state.get("auto_buy", True), key="auto_buy_toggle")
    auto_sell = st.toggle("🔽 Auto Sell Enabled", value=st.session_state.get("auto_sell", True), key="auto_sell_toggle")

    st.markdown("#### ⏱️ Trading Timings")

    def time_state(key, default_str):
        if key not in st.session_state:
            st.session_state[key] = datetime.strptime(default_str, "%H:%M").time()
        return st.time_input(key.replace("_", " ").title(), value=st.session_state[key], key=key)

    trading_start = time_state("trading_start", "09:15")
    trading_end = time_state("trading_end", "15:15")
    cutoff_time = time_state("cutoff_time", "14:50")
    auto_exit_time = time_state("auto_exit_time", "15:12")

    # Save to file (Streamlit already has correct session state due to widget keys)
    save_settings({
        "master_auto": master,
        "auto_buy": auto_buy,
        "auto_sell": auto_sell,
        "trading_start": trading_start.strftime("%H:%M"),
        "trading_end": trading_end.strftime("%H:%M"),
        "cutoff_time": cutoff_time.strftime("%H:%M"),
        "auto_exit_time": auto_exit_time.strftime("%H:%M")
    })



# === Tab 3: Market Data ===
with tab3:
    st.subheader("📈 Live Market Table – Approved Stocks")
    market_data = []

    for symbol in APPROVED_STOCK_LIST:
        try:
            full_symbol = f"{symbol}-EQ"
            if "ps_api" in st.session_state:
                ps_api = st.session_state["ps_api"]
                ltp = ps_api.get_ltp("NSE", full_symbol)
                candles = ps_api.get_time_price_series("NSE", full_symbol, "5minute", "1")
                latest = candles[-1] if candles else {}
            else:
                ltp = "🔒 Login required"
                latest = {}

            market_data.append({
                "Symbol": symbol,
                "LTP (₹)": ltp,
                "Open": latest.get("open"),
                "High": latest.get("high"),
                "Low": latest.get("low"),
                "Close": latest.get("close"),
                "Volume": latest.get("volume")
            })

        except Exception:
            market_data.append({
                "Symbol": symbol,
                "LTP (₹)": "⚠️ Error",
                "Open": None, "High": None, "Low": None,
                "Close": None, "Volume": None
            })

    df_market = pd.DataFrame(market_data)
    st.dataframe(df_market, use_container_width=True)



import os
import json
from dotenv import load_dotenv
from datetime import datetime, time

SETTINGS_FILE = "dashboard_settings.json"

# === Load settings from file
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "master_auto": True,
        "auto_buy": True,
        "auto_sell": True
    }

# === Save settings to file
def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

# === Load ProStocks credentials from environment
def load_credentials():
    load_dotenv()
    return {
        "uid": os.getenv("PROSTOCKS_USER_ID", ""),
        "pwd": os.getenv("PROSTOCKS_PASSWORD", ""),
        "factor2": os.getenv("PROSTOCKS_FACTOR2", ""),
        "vc": os.getenv("PROSTOCKS_VENDOR_CODE", ""),
        "api_key": os.getenv("PROSTOCKS_API_KEY", ""),
        "imei": os.getenv("PROSTOCKS_MAC", "MAC123456"),
        "base_url": os.getenv("PROSTOCKS_BASE_URL", "https://starapi.prostocks.com/NorenWClientTP"),
        "apkversion": os.getenv("PROSTOCKS_APK_VERSION", "1.0.0"),
    }

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Convert string times to datetime.time
            for k in ["trading_start", "trading_end", "cutoff_time", "auto_exit_time"]:
                if k in data:
                    data[k] = datetime.strptime(data[k], "%H:%M").time()
            return data
    return {
        "master_auto": True,
        "auto_buy": True,
        "auto_sell": True,
        "trading_start": time(9, 15),
        "trading_end": time(15, 15),
        "cutoff_time": time(14, 50),
        "auto_exit_time": time(15, 12)
    }

