# prostocks_login_only.py

import hashlib
import requests
import json
import os

class ProStocksAPI:
    def __init__(self, userid, password_plain, factor2, vc, api_key, imei, base_url, apkversion="1.0.0"):
        self.userid = userid
        self.password_plain = password_plain
        self.factor2 = factor2
        self.vc = vc
        self.api_key = api_key
        self.imei = imei
        self.base_url = base_url.rstrip("/")
        self.apkversion = apkversion
        self.session_token = None
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "text/plain"
        }

    def sha256(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def login(self):
        url = f"{self.base_url}/QuickAuth"
        pwd_hash = self.sha256(self.password_plain)
        appkey_raw = f"{self.userid}|{self.api_key}"
        appkey_hash = self.sha256(appkey_raw)

        print("📎 App Key Raw:", appkey_raw)
        print("🔐 Hashed App Key:", appkey_hash)

        payload = {
            "uid": self.userid,
            "pwd": pwd_hash,
            "factor2": self.factor2,
            "vc": self.vc,
            "appkey": appkey_hash,
            "imei": self.imei,
            "apkversion": self.apkversion,
            "source": "API"
        }

        try:
            jdata = json.dumps(payload, separators=(",", ":"))
            raw_data = f"jData={jdata}"
            response = self.session.post(
                url,
                data=raw_data,
                headers=self.headers,
                timeout=10
            )
            print("🔁 Response Code:", response.status_code)
            print("📨 Response Body:", response.text)

            if response.status_code == 200:
                data = response.json()
                if data.get("stat") == "Ok":
                    self.session_token = data["susertoken"]
                    self.headers["Authorization"] = self.session_token
                    print("✅ Login Success!")
                    return True, self.session_token
                else:
                    return False, data.get("emsg", "Unknown login error")
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"RequestException: {e}"


        # Placeholder stubs if needed later
    def place_order(self, buy_or_sell, product_type, exchange, tradingsymbol,
                quantity, discloseqty, price_type, price=None, trigger_price=None,
                retention='DAY', remarks=''):

    url = f"{self.base_url}/PlaceOrder"

    order_data = {
        "uid": self.userid,
        "actid": self.userid,
        "exch": exchange,
        "tsym": tradingsymbol,
        "qty": quantity,
        "dscqty": discloseqty,
        "prd": product_type,
        "trantype": buy_or_sell,
        "prctyp": price_type,
        "ret": retention,
        "ordersource": "API",  # or MOB/WEB
        "remarks": remarks
    }

    # Optional fields
    if price is not None:
        order_data["prc"] = price
    if trigger_price is not None:
        order_data["trgprc"] = trigger_price

    payload = {
        "jData": json.dumps(order_data, separators=(",", ":")),  # 🔧 Must be string
        "jKey": self.session_token
    }

    try:
        response = self.session.post(url, data=payload, headers=self.headers, timeout=10)
        print("📨 Place Order Response:", response.text)
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Place order exception:", e)
        return {"stat": "Not_Ok", "emsg": str(e)}




# ✅ Helper wrapper function for easy login
def login_ps(user_id=None, password=None, factor2=None, app_key=None):
    user_id = user_id or os.getenv("PROSTOCKS_USER_ID")
    password = password or os.getenv("PROSTOCKS_PASSWORD")
    factor2 = factor2 or os.getenv("PROSTOCKS_FACTOR2")
    vc = os.getenv("PROSTOCKS_VENDOR_CODE", user_id)
    imei = os.getenv("PROSTOCKS_MAC", "MAC123456")
    app_key = app_key or os.getenv("PROSTOCKS_API_KEY")
    base_url = os.getenv("PROSTOCKS_BASE_URL", "https://starapiuat.prostocks.com/NorenWClientTP")
    apkversion = os.getenv("PROSTOCKS_APKVERSION", "1.0.0")

    if not all([user_id, password, factor2, app_key]):
        print("❌ Missing login credentials.")
        return None

    try:
        print("📶 Logging into ProStocks API...")
        api = ProStocksAPI(user_id, password, factor2, vc, app_key, imei, base_url, apkversion)
        success, token = api.login()
        if success:
            print("✅ Login successful!")
            return api
        else:
            print("❌ Login failed:", token)
            return None
    except Exception as e:
        print("❌ Login Exception:", e)
        return None
