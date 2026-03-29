import os
import json
import time
import requests
from flask import Flask, request, jsonify
from danger_ffjwt import guest_to_jwt

app = Flask(__name__)

# --- Configuration ---
DEV_CREDIT = "@TUFANFF"
DEV_TELEGRAM = "t.me/tufan95aura"

# અહીં તમારી મનગમતી API Key સેટ કરો (ટેલિગ્રામ બોટમાં આ જ કી હોવી જોઈએ)
# તમે Environment Variable માં પણ સેટ કરી શકો છો.
VALID_API_KEY = os.getenv('JWT_API_KEY', 'tufanff')

# ---------- Version fetching with simple TTL cache ----------
_versions_cache = {
    "ob_version": "OB52",
    "client_version": "1.120.1",
    "last_fetch": 0
}

def get_versions():
    global _versions_cache
    now = time.time()
    if now - _versions_cache["last_fetch"] > 3600:
        try:
            resp = requests.get(
                "https://raw.githubusercontent.com/dangerapix/danger-ffjwt/main/versions.json",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                _versions_cache["ob_version"] = data.get("ob_version", "OB52")
                _versions_cache["client_version"] = data.get("client_version", "1.120.1")
                _versions_cache["last_fetch"] = now
        except Exception:
            pass
    return _versions_cache["ob_version"], _versions_cache["client_version"]

def add_dev_headers(response):
    response.headers["X-Developer"] = DEV_CREDIT
    return response

# ---------- Routes ----------
@app.route('/token', methods=['GET'])
def token_converter():
    args = request.args
    
    # 1. API Key Check
    provided_key = args.get('key')
    if not provided_key or provided_key != VALID_API_KEY:
        return add_dev_headers(jsonify({
            "success": False,
            "error": "Invalid or missing API Key.",
            "credit": DEV_TELEGRAM
        })), 403

    # 2. Parameters Check
    if 'uid' not in args or 'password' not in args:
        return add_dev_headers(jsonify({
            "success": False,
            "error": "Missing parameters. Use ?uid=UID&password=PASSWORD&key=YOUR_KEY",
            "credit": DEV_TELEGRAM
        })), 400

    uid = args.get('uid').strip()
    pwd = args.get('password').strip()
    ob_ver, client_ver = get_versions()

    if not uid or not pwd:
        return add_dev_headers(jsonify({
            "success": False,
            "error": "UID and password cannot be empty",
            "credit": DEV_TELEGRAM
        })), 400

    try:
        # લાઈબ્રેરીમાંથી JWT ટોકન મેળવો
        result = guest_to_jwt(uid, pwd, ob_version=ob_ver, client_version=client_ver)
        
        if isinstance(result, dict):
            # --- FIX FOR BOT: Mapping Keys ---
            # લાઈબ્રેરી jwt_token આપે છે, બોટને token જોઈએ છે
            if "jwt_token" in result:
                result["token"] = result["jwt_token"]
            
            # રીજન મેપિંગ (lock_region ને region માં કન્વર્ટ કરો)
            if "decoded" in result and isinstance(result["decoded"], dict):
                if "lock_region" in result["decoded"]:
                    result["region"] = result["decoded"]["lock_region"]
            elif "lock_region" in result:
                result["region"] = result["lock_region"]
            
            # જો success કી ના હોય તો ઉમેરો
            if "success" not in result:
                result["success"] = True
                
            result["credit"] = DEV_TELEGRAM
        else:
            # જો લાઈબ્રેરી ડાયરેક્ટ ટોકન સ્ટ્રિંગ રિટર્ન કરે
            result = {"success": True, "token": result, "credit": DEV_TELEGRAM}
            
        return add_dev_headers(jsonify(result))

    except Exception as e:
        return add_dev_headers(jsonify({
            "success": False,
            "error": str(e),
            "credit": DEV_TELEGRAM
        })), 500

if __name__ == '__main__':
    # લોકલ ટેસ્ટિંગ માટે
    app.run(debug=True, host='0.0.0.0', port=5000)