# main_app.py

import streamlit as st
import pandas as pd
from prostocks_connector import ProStocksAPI
from dashboard_logic import load_settings, save_settings, load_credentials
from datetime import datetime, time
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
    if st.button("💾 Update jKey"):
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

            if st.session_state["jKey"] != st.session_state["ps_api"].session_token:
                st.session_state["jKey"] = st.session_state["ps_api"].session_token

            st.write("📋 Order Response:", order)

            if "Not_Ok" in order.get("stat", ""):
                st.error(f"❌ Order failed: {order.get('emsg')}")
                if "Session Expired" in order.get("emsg", ""):
                    st.warning("🔁 Try refreshing jKey manually or re-login.")
            elif order.get("stat") == "Ok":
                st.success(f"✅ Order Placed! Order No: {order['norenordno']}")
                st.session_state["norenordno"] = order["norenordno"]
                st.session_state["order_status"] = "open"

    # ==== CANCEL / MODIFY ORDER SECTION ====
    st.markdown("### ❌ Cancel / 🛠 Modify Orders")

    if st.button("📘 Refresh Order Book"):
        orders = st.session_state["ps_api"].order_book()
        st.session_state["order_book"] = orders.get("data", [])

    if "order_book" in st.session_state:
        for order in st.session_state["order_book"]:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.write(f"🔸 {order['tsym']} | Qty: {order['qty']} | Type: {order['prctyp']}")
            with col2:
                if st.button("❌ Cancel", key="cancel_" + order["norenordno"]):
                    cancel_resp = st.session_state["ps_api"].cancel_order(order["norenordno"])
                    st.write(cancel_resp)
            with col3:
                if st.button("🛠 Modify", key="modify_" + order["norenordno"]):
                    st.session_state["modify_form"] = order
                    st.rerun()

    if "modify_form" in st.session_state:
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

    # ==== ORDER BOOK STATUS ====
    st.markdown("### 📒 Order Book Status")
    order_book_resp = st.session_state["ps_api"].order_book()
    if order_book_resp.get("stat") == "Ok" and "orders" in order_book_resp:
        orders = order_book_resp["orders"]
        for order in orders:
            st.json(order)
            status = order.get("status", "")
            st.markdown(f"### 🔎 Order Status: **{status}**")

            if status in ["PENDING", "OPEN"]:
                st.info("🔁 This order can still be modified or canceled.")
                with st.form(key=f"modify_cancel_{order['norenordno']}"):
                    action = st.radio("Action", ["Modify", "Cancel"], key=f"action_{order['norenordno']}")
                    new_qty = st.number_input("New Quantity", value=int(order["qty"]), key=f"qty_{order['norenordno']}")
                    new_price = st.number_input("New Price", value=float(order.get("prc", 0)), key=f"prc_{order['norenordno']}")
                    submit_action = st.form_submit_button("Submit")

                    if submit_action:
                        if action == "Cancel":
                            cancel_resp = st.session_state["ps_api"].cancel_order(order["norenordno"])
                            st.write("❌ Cancel Response:", cancel_resp)
                        elif action == "Modify":
                            cancel_resp = st.session_state["ps_api"].cancel_order(order["norenordno"])
                            st.write("🚫 Cancel (for modify):", cancel_resp)
                            time.sleep(1)
                            mod_resp = st.session_state["ps_api"].place_order(
                                buy_or_sell=order["trantype"],
                                product_type=order["prd"],
                                exchange=order["exch"],
                                tradingsymbol=order["tsym"],
                                quantity=new_qty,
                                discloseqty=0,
                                price_type=order["prctyp"],
                                price=new_price,
                                retention=order["ret"],
                                remarks="modified_order"
                            )
                            st.write("🆕 Modify Re-Place Response:", mod_resp)
            else:
                st.success("✅ Order is complete and cannot be modified or canceled.")
                st.markdown("> 🔁 Only **Pending** or **Open** orders can be modified or canceled.")
    else:
        st.error("⚠️ Failed to fetch order book.")
else:
    st.warning("🔒 Please log in to view your order book.")
