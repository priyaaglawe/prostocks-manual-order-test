# uat_tests.py

import requests
import json
import urllib.parse
import time

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

        # Properly construct the inner JSON (all values must be strings)
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

        # Step 1: JSON-stringify jData
        jdata_json = json.dumps(jdata_dict, separators=(',', ':'))

        # Step 2: URL encode the stringified JSON
        encoded_jdata = urllib.parse.quote(jdata_json, safe='')

        # Step 3: Construct the final payload string
        payload = f"jData={encoded_jdata}&jKey={jKey}"

        # Step 4: Send as x-www-form-urlencoded
        response = requests.post(url, headers=headers, data=payload)

        try:
            return response.json()
        except Exception as e:
            return {"stat": "Not_Ok", "emsg": str(e)}

    log("\U0001F501 Placing 2 test orders...")

    order1 = place_order("B", "SBIN-EQ", 1, "LMT", 780.0, "uat_order_1")
    log(f"Order 1: {order1}")

    order2 = place_order("S", "TATAMOTORS-EQ", 1, "LMT", 980.0, "uat_order_2")
    log(f"Order 2: {order2}")

    time.sleep(2)

    log("\U0001F7E2 Placing 2 market orders for trade confirmation...")

    trade1 = place_order("B", "SBIN-EQ", 1, "MKT", 0.0, "uat_trade_1")
    log(f"Market Order 1: {trade1}")

    trade2 = place_order("S", "TATAMOTORS-EQ", 1, "MKT", 0.0, "uat_trade_2")
    log(f"Market Order 2: {trade2}")

    log("\U0001F50D NOTE: Fetch trade book and order modification are not implemented in raw API yet.")
    return log_msgs
