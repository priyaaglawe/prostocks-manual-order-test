# uat_tests.py

import time
from datetime import datetime
import logging

def run_uat_test(ps_api):
    log_msgs = []
    def log(msg):
        log_msgs.append(msg)
        print(msg)

    order_ids = []

    log("🔁 Placing 2 test orders...")

    order1 = ps_api.place_order('B', 'C', 'NSE', 'INFY-EQ', 1, 0, 'LMT', 1500.0, None, 'DAY', 'uat_order_1')
    log(f"Order 1: {order1}")
    order_ids.append(order1.get('norenordno'))

    order2 = ps_api.place_order('S', 'C', 'NSE', 'TCS-EQ', 1, 0, 'LMT', 3800.0, None, 'DAY', 'uat_order_2')
    log(f"Order 2: {order2}")
    order_ids.append(order2.get('norenordno'))

    time.sleep(2)

    log("✏️ Modifying 2 orders...")
    mod1 = ps_api.modify_order('NSE', 'INFY-EQ', order_ids[0], 2, 'LMT', 1505.00)
    log(f"Modified Order 1: {mod1}")
    mod2 = ps_api.modify_order('NSE', 'TCS-EQ', order_ids[1], 2, 'LMT', 3795.00)
    log(f"Modified Order 2: {mod2}")

    log("❌ Cancelling both orders...")
    cancel1 = ps_api.cancel_order(order_ids[0])
    log(f"Cancelled Order 1: {cancel1}")
    cancel2 = ps_api.cancel_order(order_ids[1])
    log(f"Cancelled Order 2: {cancel2}")

    log("🟢 Placing 2 market orders for trade confirmation...")
    trade1 = ps_api.place_order('B', 'C', 'NSE', 'INFY-EQ', 1, 0, 'MKT', 0, None, 'DAY', 'uat_trade_1')
    trade1_id = trade1.get('norenordno')
    log(f"Market Order 1: {trade1}")

    trade2 = ps_api.place_order('S', 'C', 'NSE', 'TCS-EQ', 1, 0, 'MKT', 0, None, 'DAY', 'uat_trade_2')
    trade2_id = trade2.get('norenordno')
    log(f"Market Order 2: {trade2}")

    time.sleep(5)
    log("🔍 Fetching trade confirmations...")

    trades = ps_api.get_trade_book()
    trade_ids = [t['norenordno'] for t in trades]

    if trade1_id in trade_ids:
        log(f"✅ Trade 1 Confirmed: {trade1_id}")
    else:
        log(f"❌ Trade 1 Not Found")

    if trade2_id in trade_ids:
        log(f"✅ Trade 2 Confirmed: {trade2_id}")
    else:
        log(f"❌ Trade 2 Not Found")

    return log_msgs
