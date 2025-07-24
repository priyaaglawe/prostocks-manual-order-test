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

# MAIN DASHBOARD
if "ps_api" in st.session_state:
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

    if st.button("📘 Refresh Order Book"):
        orders = st.session_state["ps_api"].order_book()
        if isinstance(orders, dict) and orders.get("stat") == "Ok":
            st.session_state["order_book"] = orders.get("data", [])
        else:
            st.error(f"⚠️ Order Book Error: {orders.get('emsg', 'Unknown error')}")

    if "order_book" in st.session_state:
        for order in st.session_state["order_book"]:
            st.subheader(f"🔖 Order: {order['norenordno']}")
            st.json(order)
            status = order.get("status", "")
            st.markdown(f"### 🔎 Order Status: **{status}**")

            if status in ["PENDING", "OPEN"]:
                st.info("🔁 This order can still be modified or canceled.")

                if st.button("❌ Cancel Order", key=f"cancel_{order['norenordno']}"):
                    cancel_resp = st.session_state["ps_api"].cancel_order(norenordno=order["norenordno"])
                    st.write("🚫 Cancel Response:", cancel_resp)

                with st.expander("🛠 Modify Order", expanded=False):
                    new_qty = st.number_input("New Quantity", value=int(order["qty"]), key=f"mod_qty_{order['norenordno']}")
                    new_prc = st.number_input("New Price", value=float(order["prc"]), key=f"mod_prc_{order['norenordno']}")
                    if st.button("Submit Modification", key=f"mod_submit_{order['norenordno']}"):
                        cancel_resp = st.session_state["ps_api"].cancel_order(norenordno=order["norenordno"])
                        st.write("🛑 Cancel Response (for modify):", cancel_resp)

                        mod_resp = st.session_state["ps_api"].place_order(
                            exch=order["exch"],
                            tsym=order["tsym"],
                            qty=new_qty,
                            prc=new_prc,
                            prctyp=order["prctyp"],
                            trantype=order["trantype"],
                            remarks="Modified via dashboard"
                        )
                        st.write("🆕 Modify (New Order) Response:", mod_resp)
            else:
                st.success("✅ Order is complete and cannot be modified or canceled.")
                st.markdown("> 🔁 Only **Pending** or **Open** orders can be modified or canceled.")

    st.markdown("### 📒 Order Book Status")
    order_book = st.session_state["ps_api"].order_book()

    if isinstance(order_book, list):
        st.subheader("📒 Order Book")
        st.table(order_book)
    elif isinstance(order_book, dict) and order_book.get("stat") == "Ok":
        orders = order_book.get("data") or order_book.get("orders") or []
        if orders:
            for order in orders:
                st.json(order)
        else:
            st.info("ℹ️ No orders found.")
    elif isinstance(order_book, dict) and order_book.get("stat") == "Not_Ok":
        st.warning(f"⚠️ Order Book Error: {order_book.get('emsg')}")
    else:
        st.warning("⚠️ Unexpected response from order book.")
else:
    st.warning("🔒 Please log in to view your order book.")

