# uat_tests.py

import requests
import json
import time

# ✅ Define the correct UAT base URL here
UAT_BASE_URL = "https://starapiuat.prostocks.com/NorenWClientTP"

def run_uat_test(ps_api=None):
    log_msgs = []

    def log(msg):
        log_msgs.append(msg)
        print(msg)

    jKey = "f85ea13ddac928a495f023afdfc4946bdb6dd4c369917e65bac1da8b3028705c"
    uid = "A0588"
    actid = "A0588"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    def place_order(trantype, tsym, qty, prctyp, prc, remarks):
        # ✅ Use correct UAT URL
        url = ps_api.url + "/placeorder" if ps_api else UAT_BASE_URL + "/placeorder"
        print(f"🔗 Using endpoint: {url}")  # 🔍 Confirm endpoint

        jdata_dict = {
            "uid": uid,
            "actid": actid,
            "exch": "NSE",
            "tsym": tsym,
            "qty": str(qty),
            "prc": str(prc),
            "prd": "C",
            "trantype": trantype,
            "prctyp": prctyp,
            "ret": "DAY",
            "ordersource": "API",
            "remarks": remarks
        }

        jdata_json = json.dumps(jdata_dict, separators=(',', ':'))
        payload = {
            "jData": jdata_json,
            "jKey": jKey
        }

        print("jData sent:", jdata_json)
        response = requests.post(url, headers=headers, data=payload)

        print("=== Debug: Raw HTTP Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        try:
            return response.json()
        except Exception as e:
            print(f"❌ Failed to parse JSON: {e}")
            return {"stat": "Not_Ok", "emsg": str(e)}

    # Run test orders
    log("🔁 Placing 2 test orders...")
    order1 = place_order("B", "SBIN-EQ", 1, "LMT", 780.0, "uat_order_1")
    log(f"Order 1: {order1}")

    order2 = place_order("S", "TATAMOTORS-EQ", 1, "LMT", 980.0, "uat_order_2")
    log(f"Order 2: {order2}")

    time.sleep(2)

    log("🟢 Placing 2 market orders for trade confirmation...")
    trade1 = place_order("B", "SBIN-EQ", 1, "MKT", 0.0, "uat_trade_1")
    log(f"Market Order 1: {trade1}")

    trade2 = place_order("S", "TATAMOTORS-EQ", 1, "MKT", 0.0, "uat_trade_2")
    log(f"Market Order 2: {trade2}")

    log("🔍 NOTE: Fetch trade book and order modification are not implemented in raw API yet.")
    return log_msgs

