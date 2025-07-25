# main_app.py

import streamlit as st
import pandas as pd
import time
from prostocks_connector import ProStocksAPI
from dashboard_logic import load_settings, save_settings, load_credentials
from datetime import datetime
from uat_tests import run_uat_test

# === Load and Apply Settings (only once)
if "settings_loaded" not in st.session_state:
    st.session_state.update(load_settings())
    st.session_state["settings_loaded"] = True

# === Load Credentials from .env
creds = load_credentials()

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
                    st.session_state["jKey"] = ps_api.session_token
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

# 🔑 Manual jKey update UI
with st.expander("🔑 Advanced: Update jKey Manually"):
    new_jkey = st.text_input("Paste New jKey", value=st.session_state.get("jKey", ""))
    if st.button("📂 Update jKey"):
        st.session_state["jKey"] = new_jkey
        st.session_state["ps_api"].session_token = new_jkey
        st.success("✅ jKey updated in session.")

# === MAIN DASHBOARD AREA
if "ps_api" in st.session_state or "jKey" in st.session_state:

    # ✅ Ensure ps_api is always accessible when jKey/session exists
    if "ps_api" not in st.session_state:
        if "jKey" in st.session_state:
            st.session_state["ps_api"] = ProStocksAPI(
                userid=creds["uid"],
                password_plain=creds["pwd"],
                factor2=creds["factor2"],
                vc=creds["vc"],
                api_key=creds["api_key"],
                imei=creds["imei"],
                base_url=creds["base_url"],
                apkversion=creds["apkversion"]
            )
            st.session_state["ps_api"].set_session_token(st.session_state["jKey"])
        else:
            st.warning("⚠️ Login or enter jKey first.")
            st.stop()

    # ✅ Now safe to use ps_api
    ps_api = st.session_state["ps_api"]

    st.markdown("### 🔍 UAT Testing Section")
    if st.button("▶️ Run Full UAT Test"):
        logs = run_uat_test(ps_api=st.session_state["ps_api"])
        st.success("✅ UAT Test Completed")
        st.text_area("📋 Test Log", "\n".join(logs), height=400)

    st.markdown("### 📝 Manual Order Placement")

    symbols = [
        "SBIN-EQ", "RELIANCE-EQ", "TATAMOTORS-EQ", "INFY-EQ", "ITC-EQ",
        "HDFCBANK-EQ", "ICICIBANK-EQ", "HCLTECH-EQ", "AXISBANK-EQ", "WIPRO-EQ"
    ]

    with st.form("manual_order_form"):
        tsym = st.selectbox("📈 Choose Trading Symbol", symbols)
        qty = st.number_input("Quantity", min_value=1, step=1)
        price_type = st.selectbox("Order Type", ["LMT", "MKT"])
        price = st.number_input("Price (0 for MKT)", min_value=0.0, step=0.05)
        trantype = st.selectbox("Buy or Sell", ["B", "S"])
        remarks = st.text_input("Remarks", value="manual_order")

        submit_order = st.form_submit_button("📤 Place Order")

        if submit_order:
            order = st.session_state["ps_api"].place_order(
                buy_or_sell=trantype,
                product_type="C",
                exchange="NSE",
                tradingsymbol=tsym,
                quantity=qty,
                discloseqty=0,
                price_type=price_type,
                price=price if price_type == "LMT" else None,
                remarks=remarks
            )

            st.write("📋 Order Response:", order)

            if "Not_Ok" in order.get("stat", ""):
                st.error(f"❌ Order failed: {order.get('emsg')}")
                if "Session Expired" in order.get("emsg", ""):
                    st.warning("🔁 Try refreshing jKey manually or re-login.")
            elif order.get("stat") == "Ok":
                st.success(f"✅ Order Placed! Order No: {order['norenordno']}")
                st.session_state["norenordno"] = order["norenordno"]

    st.markdown("### ❌ Cancel / 🛠 Modify Orders")

# Optional: Add refresh button
if st.button("📘 Refresh Order Book"):
    order_book = ps_api.order_book()

   # Normalize to a list of orders
orders = []

if isinstance(order_book, dict):
    if "data" in order_book and isinstance(order_book["data"], list):
        orders = order_book["data"]
    elif "norenordno" in order_book:  # Single order dict
        orders = [order_book]
elif isinstance(order_book, list):
    orders = order_book

st.session_state["order_book"] = orders


# Show orders if available
if "order_book" in st.session_state and st.session_state["order_book"]:
    st.markdown("#### 📒 Order Book Status")
    
    for order in st.session_state["order_book"]:
        # ✅ Print full order for debug
        st.json(order)

        # ✅ Check status and allow cancel/modify
        if order.get("status", "").upper() in ["OPEN", "PENDING"]:
            col1, col2, col3 = st.columns([5, 2, 2])

            with col1:
                st.write(
                    f"🔹 {order['tsym']} | Qty: {order['qty']} | Type: {order['prctyp']} | Price: {order['prc']} | Status: {order['status']}"
                )

            with col2:
                if st.button("❌ Cancel", key="cancel_" + order["norenordno"]):
                    cancel_resp = ps_api.cancel_order(order["norenordno"])
                    st.success(f"✅ Cancelled: {cancel_resp}")
                    st.rerun()

            with col3:
                if st.button("🛠 Modify", key="modify_" + order["norenordno"]):
                    st.session_state["modify_form"] = order
                    st.rerun()
        else:
            st.write(f"ℹ️ Skipping order {order['norenordno']} (Status: {order['status']})")

else:
    st.info("ℹ️ No Pending or Open orders found.")

    if "modify_form" in st.session_state:
        if st.button("🧹 Cancel Modify Mode"):
            del st.session_state["modify_form"]
            st.rerun()

        order = st.session_state["modify_form"]
        st.markdown("### 🛠 Modify Order Form")
        with st.form("modify_order_form"):
            tsym = st.text_input("Symbol", value=order["tsym"])
            qty = st.number_input("Quantity", value=int(order["qty"]))
            price_type = st.selectbox("Order Type", ["LMT", "MKT"], index=0 if order["prctyp"] == "LMT" else 1)
            price = st.number_input("Price", value=float(order.get("prc", 0)))
            trantype = st.selectbox("Buy/Sell", ["B", "S"], index=0 if order["trantype"] == "B" else 1)

            submit_mod = st.form_submit_button("🔁 Submit Modification")
            if submit_mod:
                st.session_state["ps_api"].cancel_order(order["norenordno"])
                new_order = st.session_state["ps_api"].place_order(
                    buy_or_sell=trantype,
                    product_type="C",
                    exchange="NSE",
                    tradingsymbol=tsym,
                    quantity=qty,
                    discloseqty=0,
                    price_type=price_type,
                    price=price if price_type == "LMT" else None,
                    remarks="modified_order"
                )
                st.success("✅ Order Modified")
                st.write("Response:", new_order)
                del st.session_state["modify_form"]

    if "modify_form" not in st.session_state and st.button("📒 View Full Order Book"):
        order_book = st.session_state["ps_api"].order_book()
        st.session_state["latest_order_book"] = order_book

if "latest_order_book" in st.session_state and "modify_form" not in st.session_state:
    order_book = st.session_state["latest_order_book"]
    st.markdown("### 📒 Order Book Status")

    if isinstance(order_book, list):
        st.subheader("📒 Order Book")
        st.table(order_book)
    elif isinstance(order_book, dict) and order_book.get("stat") == "Ok":
        orders = order_book.get("data") or order_book.get("orders") or []
        if orders:
            for order in orders:
                st.json(order)
                status = order.get("status", "")
                st.markdown(f"### 🔎 Order Status: **{status}**")
                if status in ["PENDING", "OPEN"]:
                    st.info("🔁 This order can still be modified or canceled.")
                else:
                    st.success("✅ Order is complete and cannot be modified or canceled.")
                    st.markdown("> 🔁 Only **Pending** or **Open** orders can be modified or canceled.")
        else:
            st.info("ℹ️ No orders found.")
    elif isinstance(order_book, dict) and order_book.get("stat") == "Not_Ok":
        st.warning(f"⚠️ Order Book Error: {order_book.get('emsg')}")
    else:
        st.warning("⚠️ Unexpected response from order book.")
else:
    st.warning("🔒 Please log in to view your order book")
