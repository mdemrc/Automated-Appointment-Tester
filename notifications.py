"""
Notification service.
Sends Telegram messages and optional desktop sound alerts.
"""

import requests
from datetime import datetime
from config import config


class NotificationService:
    """Bildirim servisi"""
    
    def __init__(self):
        self.telegram_token = config.telegram.bot_token
        self.telegram_chat_id = config.telegram.chat_id
    
    def send_telegram(self, message: str) -> bool:
        """Telegram bildirimi gönder"""
        if not config.telegram.is_configured:
            print("[UYARI] Telegram yapılandırılmamış, bildirim gönderilmedi")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("[TELEGRAM] Bildirim gönderildi!")
                return True
            else:
                print(f"[TELEGRAM] Hata: {response.text}")
                return False
                
        except Exception as e:
            print(f"[TELEGRAM] Gönderim hatası: {e}")
            return False
    
    def notify_appointment_found(self, details: str):
        """Randevu bulundu bildirimi"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        target_url = config.urls.get("login", "")
        message = f"""
<b>Appointment slot available</b>

Time: {timestamp}
Details: {details}

Target: {target_url}
"""
        
        self.send_telegram(message)
        
        # Terminal'de de göster
        print("\n" + "="*50)
        print("🎉 RANDEVU BULUNDU! 🎉")
        print(f"Detaylar: {details}")
        print("="*50 + "\n")
    
    def notify_error(self, error: str):
        """Hata bildirimi"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
⚠️ <b>Appointment Tester - Error</b>

📅 Tarih: {timestamp}
❌ Hata: {error}

Bot kontrole devam ediyor...
"""
        
        self.send_telegram(message)
    
    def notify_status(self, status: str):
        """Durum bildirimi"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
📊 <b>Appointment Tester - Status</b>

📅 {timestamp}
ℹ️ {status}
"""
        
        self.send_telegram(message)


# Global instance
notifier = NotificationService()
