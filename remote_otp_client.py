"""
Remote OTP Client
Ubuntu sunucudaki OTP API'ye bağlanır
"""

import requests
import time
from datetime import datetime


class RemoteOTPClient:
    """Ubuntu sunucudaki OTP API client"""
    
    def __init__(self, server_url: str, api_key: str):
        """
        Args:
            server_url: Ubuntu sunucu URL (örn: https://api.example.com)
            api_key: API anahtarı
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> bool:
        """Sunucu erişilebilir mi?"""
        try:
            resp = requests.get(f"{self.server_url}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def get_otp(self) -> dict:
        """OTP'yi getir"""
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
    
    def mark_used(self) -> bool:
        """OTP'yi kullanıldı işaretle"""
        try:
            resp = requests.post(
                f"{self.server_url}/otp/use",
                headers=self.headers,
                timeout=10
            )
            return resp.status_code == 200
        except:
            return False
    
    def wait_for_fresh_otp(self, timeout: int = 300, check_interval: int = 3, initial_delay: int = 5) -> str:
        """
        YENİ OTP gelene kadar bekle - eski OTP'yi yoksay
        
        Args:
            timeout: Maksimum bekleme süresi (saniye)
            check_interval: Kontrol aralığı (saniye)
            initial_delay: Login sonrası SMS için bekleme süresi (saniye)
        
        Returns:
            OTP kodu veya None
        """
        print(f"[OTP Client] 🔄 Eski OTP temizleniyor...")
        self.clear_otp()
        
        # Wait for the SMS to arrive
        print(f"[OTP Client] ⏳ SMS gönderilmesi için {initial_delay}s bekleniyor...")
        time.sleep(initial_delay)
        
        print(f"[OTP Client] 📱 Yeni OTP bekleniyor... (timeout: {timeout}s)")
        print(f"[OTP Client] 📡 Sunucu: {self.server_url}")
        
        start = time.time()
        last_log = 0
        
        while time.time() - start < timeout:
            result = self.get_otp()
            
            if result.get("status") == "available":
                otp = result.get("otp")
                timestamp = result.get("timestamp", "")
                print(f"[OTP Client] ✅ YENİ OTP alındı: {otp} (zaman: {timestamp})")
                self.mark_used()
                return otp
            
            elif result.get("status") == "error":
                print(f"[OTP Client] ⚠️ Bağlantı hatası: {result.get('message')}")
            
            # Her 10 saniyede bir durum göster
            elapsed = int(time.time() - start)
            if elapsed - last_log >= 10:
                remaining = timeout - elapsed
                print(f"[OTP Client] ⏳ Bekleniyor... ({remaining}s kaldı)")
                last_log = elapsed
            
            time.sleep(check_interval)
        
        print("[OTP Client] ⏰ Timeout! OTP alınamadı.")
        return None
    
    def wait_for_otp(self, timeout: int = 300, check_interval: int = 2) -> str:
        """
        OTP gelene kadar bekle
        
        Args:
            timeout: Maksimum bekleme süresi (saniye)
            check_interval: Kontrol aralığı (saniye)
        
        Returns:
            OTP kodu veya None
        """
        print(f"[OTP Client] ⏳ OTP bekleniyor... (timeout: {timeout}s)")
        print(f"[OTP Client] 📡 Sunucu: {self.server_url}")
        
        start = time.time()
        
        while time.time() - start < timeout:
            result = self.get_otp()
            
            if result.get("status") == "available":
                otp = result.get("otp")
                print(f"[OTP Client] ✅ OTP alındı: {otp}")
                self.mark_used()
                return otp
            
            elif result.get("status") == "error":
                print(f"[OTP Client] ⚠️ Bağlantı hatası: {result.get('message')}")
            
            # Kalan süre göster
            remaining = int(timeout - (time.time() - start))
            if remaining % 30 == 0 and remaining > 0:
                print(f"[OTP Client] ⏳ {remaining}s kaldı...")
            
            time.sleep(check_interval)
        
        print("[OTP Client] ⏰ Timeout!")
        return None


# Test
if __name__ == "__main__":
    print("Remote OTP Client Test")
    print("=" * 40)
    
    server = input("Server URL (örn: https://api.example.com): ").strip()
    api_key = input("API Key: ").strip()
    
    client = RemoteOTPClient(server, api_key)
    
    print("\nHealth check...", end=" ")
    if client.health_check():
        print("✅ OK")
    else:
        print("❌ FAILED")
        exit(1)
    
    print("\nOTP bekleniyor (60s timeout)...")
    otp = client.wait_for_otp(timeout=60)
    
    if otp:
        print(f"\n✅ OTP: {otp}")
    else:
        print("\n❌ OTP alınamadı")
