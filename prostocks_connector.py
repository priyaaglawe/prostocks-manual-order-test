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

        # ✅ Add Noren API object for orders, etc.
        self.api = NorenApi()
        self.api.set_proxy(None)
        self.api.set_url(host=self.base_url, websocket=None)

    def sha256(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def login(self):
        url = f"{self.base_url}/QuickAuth"
        pwd_hash = self.sha256(self.password_plain)
        appkey_raw = f"{self.userid}|{self.api_key}"
        appkey_hash = self.sha256(appkey_raw)

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

            if response.status_code == 200:
                data = response.json()
                if data.get("stat") == "Ok":
                    self.session_token = data["susertoken"]
                    self.headers["Authorization"] = self.session_token
                    print("✅ Login Success!")

                    # 🔐 Also login to Noren API object
                    res = self.api.login(
                        userid=self.userid,
                        password=self.password_plain,
                        twoFA=self.factor2,
                        vendor_code=self.vc,
                        api_secret=self.api_key,
                        imei=self.imei
                    )
                    if res is None or res.get("stat") != "Ok":
                        return False, "Login failed (Noren API)"
                    return True, "Login successful"
                else:
                    return False, data.get("emsg", "Unknown login error")
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"RequestException: {e}"

    # ✅ Order API methods via Noren API
    def place_order(self, buy_or_sell, product_type, exchange, tradingsymbol, quantity,
                    discloseqty, price_type, price, trigger_price, retention, remarks):
        return self.api.place_order(
            buy_or_sell=buy_or_sell,
            product_type=product_type,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            quantity=quantity,
            discloseqty=discloseqty,
            price_type=price_type,
            price=price,
            trigger_price=trigger_price,
            retention=retention,
            remarks=remarks
        )

    def modify_order(self, exchange, tradingsymbol, orderno,
                     newquantity, newprice_type, newprice):
        return self.api.modify_order(
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            orderno=orderno,
            newquantity=newquantity,
            newprice_type=newprice_type,
            newprice=newprice
        )

    def cancel_order(self, orderno):
        return self.api.cancel_order(orderno=orderno)

    def get_trade_book(self):
        return self.api.get_trade_book()



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
