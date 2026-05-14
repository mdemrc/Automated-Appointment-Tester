"""
OTP API Server
Android'den gelen SMS OTP kodlarını alır ve bot ile paylaşır
"""

from flask import Flask, request, jsonify
import threading
import time
import os
import json
from datetime import datetime

app = Flask(__name__)

# OTP verisi için global storage
otp_storage = {
    "code": None,
    "timestamp": None,
    "used": False
}

# Thread-safe lock
otp_lock = threading.Lock()

API_KEY = os.getenv("OTP_API_KEY", "")

@app.route('/api/otp', methods=['POST'])
def receive_otp():
    """Android'den OTP kodunu al"""
    
    # API Key kontrolü
    auth_key = request.headers.get('X-API-Key') or request.json.get('api_key')
    if auth_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    # SMS içeriğinden OTP çıkar
    sms_body = data.get('sms_body', '')
    sender = data.get('sender', '')
    
    # from configured sender kontrol et
    if len(sender) == 0 or len(sms_body) == 0:
        return jsonify({"error": "Not a relevant sender", "status": "ignored"}), 200
    
    # İlk 6 haneyi al (OTP kodu)
    otp_code = ''.join(filter(str.isdigit, sms_body))[:6]
    
    if len(otp_code) != 6:
        return jsonify({"error": "Invalid OTP format"}), 400
    
    with otp_lock:
        otp_storage["code"] = otp_code
        otp_storage["timestamp"] = datetime.now().isoformat()
        otp_storage["used"] = False
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📱 OTP alındı: {otp_code}")
    
    return jsonify({
        "status": "success",
        "otp": otp_code,
        "message": "OTP received successfully"
    }), 200


@app.route('/api/otp', methods=['GET'])
def get_otp():
    """Bot için OTP kodunu getir"""
    
    # API Key kontrolü
    auth_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if auth_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    with otp_lock:
        if otp_storage["code"] and not otp_storage["used"]:
            return jsonify({
                "status": "available",
                "otp": otp_storage["code"],
                "timestamp": otp_storage["timestamp"]
            }), 200
        else:
            return jsonify({
                "status": "waiting",
                "message": "No OTP available"
            }), 200


@app.route('/api/otp/mark-used', methods=['POST'])
def mark_otp_used():
    """OTP'yi kullanıldı olarak işaretle"""
    
    auth_key = request.headers.get('X-API-Key') or request.json.get('api_key')
    if auth_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    with otp_lock:
        otp_storage["used"] = True
    
    return jsonify({"status": "marked_used"}), 200


@app.route('/api/otp/clear', methods=['POST'])
def clear_otp():
    """OTP'yi temizle"""
    
    auth_key = request.headers.get('X-API-Key') or request.json.get('api_key')
    if auth_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    with otp_lock:
        otp_storage["code"] = None
        otp_storage["timestamp"] = None
        otp_storage["used"] = False
    
    return jsonify({"status": "cleared"}), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "service": "OTP Server"}), 200


def create_otp_app(api_key=None):
    """Flask app'i oluştur ve döndür"""
    global API_KEY
    if api_key:
        API_KEY = api_key
    return app


class OTPServer:
    """OTP Server wrapper for bot integration"""
    
    def __init__(self, host='0.0.0.0', port=5000, api_key=None):
        self.host = host
        self.port = port
        self.api_key = api_key or API_KEY
        self.server_thread = None
        self.running = False
    
    def start(self):
        """Server'ı background thread'de başlat"""
        if self.running:
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"[OTP Server] 🚀 Started on http://{self.host}:{self.port}")
    
    def _run_server(self):
        """Flask server'ı çalıştır"""
        app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
    
    def wait_for_otp(self, timeout=300):
        """OTP gelene kadar bekle (max timeout saniye)"""
        print(f"[OTP Server] ⏳ OTP bekleniyor... (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            with otp_lock:
                if otp_storage["code"] and not otp_storage["used"]:
                    code = otp_storage["code"]
                    otp_storage["used"] = True
                    print(f"[OTP Server] ✅ OTP alındı: {code}")
                    return code
            time.sleep(1)
        
        print("[OTP Server] ⏰ OTP timeout!")
        return None
    
    def clear(self):
        """OTP'yi temizle"""
        with otp_lock:
            otp_storage["code"] = None
            otp_storage["timestamp"] = None
            otp_storage["used"] = False
    
    def clear_otp(self):
        """OTP'yi temizle (alias)"""
        self.clear()


# Standalone çalıştırma
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║                     OTP SMS Server                          ║
╠══════════════════════════════════════════════════════════════╣
║  Android'den SMS OTP kodlarını almak için API server        ║
║                                                              ║
║  Endpoints:                                                  ║
║    POST /api/otp     - OTP gönder (Android'den)             ║
║    GET  /api/otp     - OTP al (Bot için)                    ║
║    POST /api/otp/clear - OTP temizle                        ║
║                                                              ║
║  API Key: configured via OTP_API_KEY env var                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
