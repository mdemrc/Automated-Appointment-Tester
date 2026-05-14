"""
OTP Dinleyici - Sunucudan OTP bekler
"""

import requests
import time
import winsound
from datetime import datetime


class OTPListener:
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
        self.last_otp = None
    
    def get_otp(self) -> dict:
        """Sunucudan OTP'yi al"""
        try:
            resp = requests.get(
                f"{self.server_url}/otp",
                headers=self.headers,
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def clear_otp(self) -> bool:
        """OTP'yi temizle"""
        try:
            resp = requests.post(
                f"{self.server_url}/otp/clear",
                headers=self.headers,
                timeout=10
            )
            return resp.status_code == 200
        except:
            return False
    
    def play_alert(self):
        """Sesli uyarı çal"""
        try:
            for _ in range(3):
                winsound.Beep(1000, 300)
                time.sleep(0.1)
        except:
            print("\a")  # Terminal beep
    
    def wait_for_otp(self, check_interval: int = 2) -> str:
        """
        Yeni OTP gelene kadar bekle
        Returns: OTP kodu
        """
        print(f"\n🔄 Eski OTP temizleniyor...")
        self.clear_otp()
        
        print(f"📱 OTP bekleniyor... (Ctrl+C ile iptal)")
        print(f"📡 Sunucu: {self.server_url}")
        print("-" * 40)
        
        start_time = time.time()
        last_status_time = 0
        
        while True:
            try:
                result = self.get_otp()
                
                if result.get("status") == "available":
                    otp = result.get("otp")
                    timestamp = result.get("timestamp", "")
                    
                    print(f"\n{'='*40}")
                    print(f"✅ OTP ALINDI: {otp}")
                    print(f"⏰ Zaman: {timestamp}")
                    print(f"{'='*40}\n")
                    
                    self.play_alert()
                    self.last_otp = otp
                    return otp
                
                # Her 10 saniyede durum göster
                elapsed = int(time.time() - start_time)
                if elapsed - last_status_time >= 10:
                    print(f"⏳ Bekleniyor... ({elapsed}s)")
                    last_status_time = elapsed
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n❌ İptal edildi")
                return None


if __name__ == "__main__":
    from config import OTP_SERVER
    
    listener = OTPListener(OTP_SERVER["url"], OTP_SERVER["api_key"])
    otp = listener.wait_for_otp(OTP_SERVER["check_interval"])
    
    if otp:
        print(f"Son OTP: {otp}")
