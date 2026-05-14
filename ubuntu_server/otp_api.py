"""
OTP relay API - Ubuntu server
aapanel üzerinde çalışır

Kurulum:
1. aapanel → Python Project → Create
2. Bu dosyayı yükle
3. pip install flask gunicorn
4. Gunicorn ile çalıştır
"""

from flask import Flask, request, jsonify
from functools import wraps
import threading
import time
import re
import os
from datetime import datetime

app = Flask(__name__)

# ============== AYARLAR ==============
API_KEY = os.environ.get("OTP_API_KEY", "change-me-please")
OTP_EXPIRE_SECONDS = 300  # 5 dakika

# ============== OTP STORAGE ==============
otp_storage = {
    "code": None,
    "timestamp": None,
    "used": False,
    "raw_message": None
}
otp_lock = threading.Lock()


# ============== AUTH DECORATOR ==============
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if key != API_KEY:
            return jsonify({"error": "Unauthorized", "message": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated


# ============== ENDPOINTS ==============

@app.route('/', methods=['GET'])
def home():
    """Ana sayfa"""
    return jsonify({
        "service": "OTP Relay API",
        "status": "running",
        "endpoints": {
            "POST /otp": "OTP gönder (Tasker'dan)",
            "GET /otp": "OTP al (Bot için)",
            "POST /otp/clear": "OTP temizle",
            "GET /health": "Health check"
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check - API key gerektirmez"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/otp', methods=['POST'])
@require_api_key
def receive_otp():
    """
    Tasker'dan OTP al
    
    Body:
    {
        "sms_body": "123456 tek seferlik şifreniz...",
        "sender": "sms-sender"
    }
    """
    data = request.json or {}
    
    sms_body = data.get('sms_body', '')
    sender = data.get('sender', '')
    
    if not sms_body:
        return jsonify({"error": "sms_body required"}), 400
    
    # 6 haneli kodu çıkar
    otp_code = extract_otp(sms_body)
    
    if not otp_code:
        return jsonify({
            "error": "No OTP found",
            "message": "Could not extract 6-digit code from SMS"
        }), 400
    
    # Kaydet
    with otp_lock:
        otp_storage["code"] = otp_code
        otp_storage["timestamp"] = datetime.now().isoformat()
        otp_storage["used"] = False
        otp_storage["raw_message"] = sms_body[:200]
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ OTP alındı: {otp_code} (from: {sender})")
    
    return jsonify({
        "status": "success",
        "otp": otp_code,
        "message": "OTP received"
    })


@app.route('/otp', methods=['GET'])
@require_api_key
def get_otp():
    """
    Bot için OTP getir
    
    Returns:
    - status: "available" | "waiting" | "expired" | "used"
    - otp: kod (varsa)
    """
    with otp_lock:
        if not otp_storage["code"]:
            return jsonify({
                "status": "waiting",
                "message": "No OTP available"
            })
        
        if otp_storage["used"]:
            return jsonify({
                "status": "used",
                "message": "OTP already used"
            })
        
        # Expire kontrolü
        if otp_storage["timestamp"]:
            ts = datetime.fromisoformat(otp_storage["timestamp"])
            age = (datetime.now() - ts).total_seconds()
            
            if age > OTP_EXPIRE_SECONDS:
                return jsonify({
                    "status": "expired",
                    "message": f"OTP expired ({int(age)}s old)"
                })
        
        return jsonify({
            "status": "available",
            "otp": otp_storage["code"],
            "timestamp": otp_storage["timestamp"]
        })


@app.route('/otp/use', methods=['POST'])
@require_api_key
def mark_used():
    """OTP'yi kullanıldı olarak işaretle"""
    with otp_lock:
        otp_storage["used"] = True
    
    return jsonify({"status": "marked_used"})


@app.route('/otp/clear', methods=['POST'])
@require_api_key
def clear_otp():
    """OTP'yi temizle"""
    with otp_lock:
        otp_storage["code"] = None
        otp_storage["timestamp"] = None
        otp_storage["used"] = False
        otp_storage["raw_message"] = None
    
    return jsonify({"status": "cleared"})


# ============== HELPERS ==============

def extract_otp(text: str) -> str:
    """SMS'ten 6 haneli OTP kodunu çıkar"""
    matches = re.findall(r'\b(\d{6})\b', text)
    return matches[0] if matches else None


# ============== MAIN ==============

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    OTP Relay API Server                        ║
╠══════════════════════════════════════════════════════════════╣
║  Ubuntu sunucuda çalışır - Tasker'dan SMS alır               ║
║                                                              ║
║  POST /otp      - Tasker'dan OTP al                          ║
║  GET  /otp      - Bot için OTP getir                         ║
║  POST /otp/clear - OTP temizle                               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print(f"API Key: {API_KEY[:10]}...")
    print()
    
    # Development mode
    app.run(host='0.0.0.0', port=5000, debug=True)
