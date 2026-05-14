"""
Telegram OTP Receiver
SMS OTP kodlarını Telegram üzerinden alır
IP değişikliğinden etkilenmez!
"""

import os
import re
import time
import threading
import requests
from datetime import datetime

# OTP Storage (thread-safe)
otp_storage = {
    "code": None,
    "timestamp": None,
    "used": False
}
otp_lock = threading.Lock()


class TelegramOTPReceiver:
    """Telegram Bot ile OTP alma"""
    
    def __init__(self, bot_token: str, allowed_chat_ids: list = None):
        """
        Args:
            bot_token: Telegram Bot Token (@BotFather'dan alınır)
            allowed_chat_ids: İzin verilen chat ID'leri (güvenlik için)
        """
        self.bot_token = bot_token
        self.allowed_chat_ids = allowed_chat_ids or []
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        self.running = False
        self.poll_thread = None
        
    def start(self):
        """Polling başlat"""
        if self.running:
            return
            
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_updates, daemon=True)
        self.poll_thread.start()
        print(f"[Telegram OTP] 🚀 Bot başlatıldı - Mesaj bekleniyor...")
        
    def stop(self):
        """Polling durdur"""
        self.running = False
        
    def _poll_updates(self):
        """Telegram'dan mesajları çek"""
        while self.running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._process_update(update)
            except Exception as e:
                print(f"[Telegram OTP] ⚠️ Hata: {e}")
            time.sleep(1)
            
    def _get_updates(self):
        """Telegram API'den güncellemeleri al"""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 30,
            "allowed_updates": ["message"]
        }
        
        try:
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                return data.get("result", [])
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            print(f"[Telegram OTP] API Hatası: {e}")
            
        return []
        
    def _process_update(self, update):
        """Gelen mesajı işle"""
        self.last_update_id = update.get("update_id", self.last_update_id)
        
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        # Chat ID kontrolü (güvenlik)
        if self.allowed_chat_ids and chat_id not in self.allowed_chat_ids:
            print(f"[Telegram OTP] ⚠️ İzinsiz chat: {chat_id}")
            self._send_message(chat_id, f"⚠️ Bu chat izinli değil!\nChat ID: {chat_id}")
            return
            
        # /start komutu
        if text == "/start":
            self._send_message(chat_id, 
                f"✅ OTP Relay Bot aktif!\n\n"
                f"📱 Chat ID: `{chat_id}`\n\n"
                f"Bu ID'yi .env dosyasına ekleyin:\n"
                f"`TELEGRAM_ALLOWED_CHATS={chat_id}`\n\n"
                f"SMS içeriğini bu chata forward edin veya Tasker ile otomatik gönderin."
            )
            return
            
        # /chatid komutu
        if text == "/chatid":
            self._send_message(chat_id, f"📱 Chat ID: `{chat_id}`")
            return
            
        # OTP çıkar
        otp_code = self._extract_otp(text)
        
        if otp_code:
            with otp_lock:
                otp_storage["code"] = otp_code
                otp_storage["timestamp"] = datetime.now().isoformat()
                otp_storage["used"] = False
                
            print(f"[Telegram OTP] ✅ OTP alındı: {otp_code}")
            self._send_message(chat_id, f"✅ OTP alındı: `{otp_code}`")
        else:
            # Possible OTP message but no code was extracted
            if "sms-sender" in text.lower() or "şifre" in text.lower() or "code" in text.lower():
                self._send_message(chat_id, f"⚠️ OTP çıkarılamadı. Mesaj:\n{text[:100]}")
                
    def _extract_otp(self, text: str) -> str:
        """Metinden 6 haneli OTP kodunu çıkar"""
        # 6 haneli sayıları bul
        matches = re.findall(r'\b(\d{6})\b', text)
        if matches:
            return matches[0]
        return None
        
    def _send_message(self, chat_id: int, text: str):
        """Telegram mesajı gönder"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"[Telegram OTP] Mesaj gönderilemedi: {e}")
            
    def wait_for_otp(self, timeout: int = 300) -> str:
        """OTP gelene kadar bekle"""
        print(f"[Telegram OTP] ⏳ OTP bekleniyor... (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            with otp_lock:
                if otp_storage["code"] and not otp_storage["used"]:
                    code = otp_storage["code"]
                    otp_storage["used"] = True
                    return code
            time.sleep(1)
            
        print("[Telegram OTP] ⏰ Timeout!")
        return None
        
    def clear_otp(self):
        """OTP'yi temizle"""
        with otp_lock:
            otp_storage["code"] = None
            otp_storage["timestamp"] = None
            otp_storage["used"] = False


# Test
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║              Telegram OTP Receiver Test                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    bot_token = input("Bot Token girin: ").strip()
    
    if not bot_token:
        print("Token gerekli!")
        exit(1)
        
    receiver = TelegramOTPReceiver(bot_token)
    receiver.start()
    
    print("\n📱 Telegram'da bota /start yazın")
    print("📱 Then forward the OTP SMS to the bot")
    print("Çıkmak için Ctrl+C\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        receiver.stop()
        print("\nDurduruldu.")
