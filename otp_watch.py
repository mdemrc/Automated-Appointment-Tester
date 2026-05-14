"""
OTP Dinleyici - Sürekli çalışır, her saniye kontrol eder
Ctrl+C ile kapatılır
"""

import os
import requests
import time
import winsound
from datetime import datetime

SERVER_URL = os.environ.get("OTP_SERVER_URL", "http://localhost:5000")
API_KEY = os.environ.get("OTP_API_KEY", "")

def get_otp():
    """Sunucudan OTP al"""
    try:
        resp = requests.get(
            f"{SERVER_URL}/otp",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        return resp.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def play_alert():
    """Sesli uyarı"""
    try:
        for _ in range(5):
            winsound.Beep(1500, 200)
            time.sleep(0.1)
    except:
        print("\a\a\a")

def main():
    print("=" * 50)
    print("       OTP DİNLEYİCİ - SÜREKLI ÇALIŞIR")
    print("=" * 50)
    print(f"Sunucu: {SERVER_URL}")
    print(f"Kontrol: Her 1 saniye")
    print(f"Kapatmak için: Ctrl+C")
    print("=" * 50)
    print()
    
    check_count = 0
    
    while True:
        try:
            check_count += 1
            now = datetime.now().strftime("%H:%M:%S")
            
            result = get_otp()
            status = result.get("status", "error")
            
            if status == "available":
                otp = result.get("otp")
                timestamp = result.get("timestamp", "")
                
                print()
                print("!" * 50)
                print(f"!!! OTP ALINDI: {otp} !!!")
                print(f"!!! Zaman: {timestamp} !!!")
                print("!" * 50)
                print()
                
                play_alert()
                
                # OTP alındıktan sonra da dinlemeye devam et
                print(f"[{now}] ✅ OTP: {otp} - Dinlemeye devam ediliyor...")
                
            elif status == "waiting":
                # Her 10 kontrolde bir göster (ekranı kirletmemek için)
                if check_count % 10 == 0:
                    print(f"[{now}] ⏳ Bekleniyor... (#{check_count})")
                    
            elif status == "used":
                if check_count % 30 == 0:
                    print(f"[{now}] ℹ️ Son OTP kullanıldı, yeni bekleniyor...")
                    
            elif status == "error":
                print(f"[{now}] ❌ Hata: {result.get('message', 'Bilinmeyen')}")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n👋 Dinleyici kapatıldı.")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Hata: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
