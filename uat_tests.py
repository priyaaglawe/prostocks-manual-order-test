# uat_tests.py

import requests
import json
import hashlib

# Login values
uid = "A0588"
actid = "A0588"
jKey = "610d923d8616a42165917c4142ceafe660885de6f71c0ec2dd74defd4bedbe83"

# Sample order (LMT Buy)
order_data = {
    "uid": uid,
    "actid": actid,
    "exch": "NSE",
    "tsym": "SBIN-EQ",
    "qty": "1",
    "prc": "780.0",
    "prd": "C",
    "trantype": "B",
    "prctyp": "LMT",
    "ret": "DAY",
    "ordersource": "API",
    "remarks": "uat_order_1"
}

# Proper URL encoding
jData_str = json.dumps(order_data)
payload = {
    "jData": jData_str,
    "jKey": jKey
}

# Headers must be set correctly
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

# POST to UAT endpoint
url = "https://staruat.prostocks.com/NorenWClientTP/placeorder"
response = requests.post(url, data=payload, headers=headers)

# Output
print("Status Code:", response.status_code)
print("Response:", response.text)
