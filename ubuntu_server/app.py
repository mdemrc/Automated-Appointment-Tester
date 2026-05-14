"""
OTP relay API - small Flask server that receives OTP codes from a mobile relay
and exposes them to the desktop automation client.
"""

from flask import Flask, request, jsonify
from functools import wraps
import threading
import re
import os
from datetime import datetime

app = Flask(__name__)

API_KEY = os.environ.get("OTP_API_KEY", "")
if not API_KEY:
    raise RuntimeError("OTP_API_KEY environment variable must be set before starting the server.")
OTP_EXPIRE_SECONDS = 300

# ============== OTP STORAGE ==============
otp_storage = {
    "code": None,
    "timestamp": None,
    "used": False
}
otp_lock = threading.Lock()


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "OTP relay API",
        "status": "running",
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route('/otp', methods=['POST'])
@require_api_key
def receive_otp():
    """Tasker'dan OTP al"""
    data = request.json or {}
    sms_body = data.get('sms_body', '')
    sender = data.get('sender', '')
    
    if not sms_body:
        return jsonify({"error": "sms_body required"}), 400
    
    # 6 haneli kodu çıkar
    matches = re.findall(r'\b(\d{6})\b', sms_body)
    otp_code = matches[0] if matches else None
    
    if not otp_code:
        return jsonify({"error": "No 6-digit OTP found"}), 400
    
    with otp_lock:
        otp_storage["code"] = otp_code
        otp_storage["timestamp"] = datetime.now().isoformat()
        otp_storage["used"] = False
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ OTP: {otp_code} (from: {sender})")
    
    return jsonify({"status": "success", "otp": otp_code})


@app.route('/otp', methods=['GET'])
@require_api_key
def get_otp():
    """Bot için OTP getir"""
    with otp_lock:
        if not otp_storage["code"]:
            return jsonify({"status": "waiting"})
        
        if otp_storage["used"]:
            return jsonify({"status": "used"})
        
        if otp_storage["timestamp"]:
            ts = datetime.fromisoformat(otp_storage["timestamp"])
            age = (datetime.now() - ts).total_seconds()
            if age > OTP_EXPIRE_SECONDS:
                return jsonify({"status": "expired"})
        
        return jsonify({
            "status": "available",
            "otp": otp_storage["code"],
            "timestamp": otp_storage["timestamp"]
        })


@app.route('/otp/use', methods=['POST'])
@require_api_key
def mark_used():
    with otp_lock:
        otp_storage["used"] = True
    return jsonify({"status": "marked_used"})


@app.route('/otp/clear', methods=['POST'])
@require_api_key
def clear_otp():
    with otp_lock:
        otp_storage["code"] = None
        otp_storage["timestamp"] = None
        otp_storage["used"] = False
    return jsonify({"status": "cleared"})


if __name__ == '__main__':
    print(f"API Key: {API_KEY}")
    app.run(host='127.0.0.1', port=5000, debug=True)
