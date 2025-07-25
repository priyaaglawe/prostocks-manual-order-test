# prostocks_connector.py

import hashlib
import requests
import json
import os

class ProStocksAPI:
    def __init__(self, userid, password_plain, factor2, vc, api_key, imei, base_url, apkversion="1.0.0"):
        self.userid = userid
        self.uid = userid
        self.actid = userid
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
                    print("🔑 Session Token set:", self.session_token)
                    return True, self.session_token
                else:
                    return False, data.get("emsg", "Unknown login error")
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"RequestException: {e}"

    def _post(self, url, data):
        try:
            response = self.session.post(url, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": self.session_token
            }, data=data)

            json_resp = response.json()

            if json_resp.get("stat") == "Not_Ok" and "Session Expired" in json_resp.get("emsg", ""):
                print("🔁 Session expired. Attempting re-login...")
                success, _ = self.login()
                if success:
                    self.headers["Authorization"] = self.session_token
                    new_data = data.replace(f"jKey=", f"jKey={self.session_token}")
                    response = self.session.post(url, headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": self.session_token
                    }, data=new_data)
                    return response.json()
                else:
                    return {"stat": "Not_Ok", "emsg": "Session expired and auto re-login failed."}

            return json_resp

        except Exception as e:
            return {"stat": "Not_Ok", "emsg": str(e)}

    def place_order(self, buy_or_sell, product_type, exchange, tradingsymbol,
                    quantity, discloseqty, price_type, price=None, trigger_price=None,
                    retention='DAY', remarks=''):

        url = f"{self.base_url}/PlaceOrder"

        order_data = {
            "uid": self.userid,
            "actid": self.userid,
            "exch": exchange,
            "tsym": tradingsymbol,
            "qty": str(quantity),
            "dscqty": str(discloseqty),
            "prd": product_type,
            "trantype": buy_or_sell,
            "prctyp": price_type,
            "ret": retention,
            "ordersource": "API",
            "remarks": remarks
        }

        if price_type.upper() == "MKT":
            order_data["prc"] = "0"
        elif price is not None:
            order_data["prc"] = str(price)
        else:
            raise ValueError("Price is required for non-MKT orders.")

        if trigger_price is not None:
            order_data["trgprc"] = str(trigger_price)

        print("📦 Order Payload:", order_data)

        jdata_str = json.dumps(order_data, separators=(",", ":"))
        payload = f"jData={jdata_str}&jKey={self.session_token}"
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            response = self.session.post(url, data=payload, headers=self.headers, timeout=10)
            print("📨 Place Order Response:", response.text)
            return response.json()
        except requests.exceptions.RequestException as e:
            print("❌ Place order exception:", e)
            return {"stat": "Not_Ok", "emsg": str(e)}
    def modify_order(self, norenordno, tsym, qty, prctyp, prc="0"):
    url = f"{self.base_url}/ModifyOrder"
    jdata = {
        "uid": self.userid,
        "norenordno": norenordno,
        "tsym": tsym,
        "qty": str(qty),
        "prctyp": prctyp,
        "prc": str(prc)
    }

    payload = f"jData={json.dumps(jdata)}&jKey={self.session_token}"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {"stat": "Not_Ok", "emsg": f"ModifyOrder Exception: {str(e)}"}

    def order_book(self):
        url = f"{self.base_url}/OrderBook"
        jdata = {"uid": self.userid}
        payload = f"jData={json.dumps(jdata)}&jKey={self.session_token}"

        try:
            response = self.session.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            data = response.json()

            if isinstance(data, list) and data and data[0].get("stat") == "Ok":
                return {"stat": "Ok", "orders": data}
            elif isinstance(data, dict) and data.get("stat") == "Not_Ok":
                return {"stat": "Not_Ok", "emsg": data.get("emsg", "Unknown Error")}
            else:
                return {"stat": "Not_Ok", "emsg": "Unexpected format from API"}
        except Exception as e:
            return {"stat": "Not_Ok", "emsg": str(e)}

    def trade_book(self):
        url = f"{self.base_url}/TradeBook"
        payload = f"jData={{\"uid\":\"{self.userid}\"}}&jKey={self.session_token}"
        return self._post(url, payload)

# ✅ Helper function to log in with environment support
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
