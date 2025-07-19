# uat_tests.py

import requests
import json
import time
import urllib.parse

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
    url = "https://staruat.prostocks.com/NorenWClientTP/PlaceOrder"

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
        "ordersource": "WEB",
        "remarks": remarks
    }

    jdata_json = json.dumps(jdata_dict, separators=(',', ':'))
    encoded_jdata = urllib.parse.quote(jdata_json, safe='')

    payload = f"jData={encoded_jdata}&jKey={jKey}"

    response = requests.post(url, headers=headers, data=payload)

    try:
        return response.json()
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": str(e)}

    # Run tests
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
