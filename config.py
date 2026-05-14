"""
Automated Appointment Tester - Config Module
Loads all settings from environment variables / .env file.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ApplicantInfo:
    """Başvuru sahibi bilgileri"""
    first_name: str
    last_name: str
    gender: str
    nationality: str
    passport_no: str
    phone_code: str
    phone_number: str
    email: str


@dataclass
class AppointmentConfig:
    """Randevu kategorisi ayarları"""
    category: str
    subcategory: str
    center: str = ""  # Uygulama merkezi (opsiyonel - boşsa ilk müsait merkez seçilir)


@dataclass
class TelegramConfig:
    """Telegram bildirim ayarları"""
    bot_token: str
    chat_id: str
    
    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)


@dataclass
class BotConfig:
    """Bot genel ayarları"""
    check_interval: int
    headless: bool


@dataclass
class RemoteOTPConfig:
    """Ubuntu sunucu OTP API ayarları (ÖNERİLEN)"""
    enabled: bool
    server_url: str  # https://api.senindomain.com
    api_key: str
    timeout: int  # OTP bekleme süresi (saniye)


@dataclass  
class OTPServerConfig:
    """Lokal OTP Server ayarları (IP değişince sorunlu)"""
    enabled: bool
    host: str
    port: int
    api_key: str
    timeout: int  # OTP bekleme süresi (saniye)


@dataclass
class TelegramOTPConfig:
    """Telegram OTP ayarları (IP değişikliğinden etkilenmez!)"""
    enabled: bool
    bot_token: str
    allowed_chat_ids: list  # İzinli chat ID'leri


class Config:
    """Ana config sınıfı"""
    
    def __init__(self):
        self.target_email = os.getenv("TARGET_EMAIL", "")
        self.target_password = os.getenv("TARGET_PASSWORD", "")
        
        # Başvuru sahibi bilgileri
        self.applicant = ApplicantInfo(
            first_name=os.getenv("APPLICANT_FIRST_NAME", ""),
            last_name=os.getenv("APPLICANT_LAST_NAME", ""),
            gender=os.getenv("APPLICANT_GENDER", "Male"),
            nationality=os.getenv("APPLICANT_NATIONALITY", "Türkiye"),
            passport_no=os.getenv("APPLICANT_PASSPORT_NO", ""),
            phone_code=os.getenv("APPLICANT_PHONE_CODE", "90"),
            phone_number=os.getenv("APPLICANT_PHONE_NUMBER", ""),
            email=os.getenv("APPLICANT_EMAIL", "")
        )
        
        # Randevu kategorisi
        self.appointment = AppointmentConfig(
            category=os.getenv("APPOINTMENT_CATEGORY", "1 - Uzun Donem"),
            subcategory=os.getenv("APPOINTMENT_SUBCATEGORY", "5-ERASMUS/NAWA/ECS")
        )
        
        # Telegram
        self.telegram = TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", "")
        )
        
        # Bot ayarları
        self.bot = BotConfig(
            check_interval=int(os.getenv("CHECK_INTERVAL_SECONDS", "60")),
            headless=os.getenv("HEADLESS_MODE", "true").lower() == "true"
        )
        
        # Ubuntu Sunucu OTP API (ÖNERİLEN - Sabit IP/Domain)
        self.remote_otp = RemoteOTPConfig(
            enabled=os.getenv("OTP_REMOTE_ENABLED", "true").lower() == "true",
            server_url=os.getenv("OTP_REMOTE_URL", ""),
            api_key=os.getenv("OTP_REMOTE_API_KEY", ""),
            timeout=int(os.getenv("OTP_TIMEOUT_SECONDS", "300"))
        )
        
        # Lokal OTP Server ayarları (Tasker SMS entegrasyonu için - Lokal ağ)
        self.otp_server = OTPServerConfig(
            enabled=os.getenv("OTP_SERVER_ENABLED", "false").lower() == "true",
            host=os.getenv("OTP_SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("OTP_SERVER_PORT", "5000")),
            api_key=os.getenv("OTP_API_KEY", ""),
            timeout=int(os.getenv("OTP_TIMEOUT_SECONDS", "300"))
        )
        
        # Telegram OTP ayarları (alternatif)
        chat_ids_str = os.getenv("TELEGRAM_OTP_ALLOWED_CHATS", "")
        chat_ids = [int(x.strip()) for x in chat_ids_str.split(",") if x.strip()]
        self.telegram_otp = TelegramOTPConfig(
            enabled=os.getenv("TELEGRAM_OTP_ENABLED", "false").lower() == "true",
            bot_token=os.getenv("TELEGRAM_OTP_BOT_TOKEN", ""),
            allowed_chat_ids=chat_ids
        )
        
        target_base = os.getenv("TARGET_BASE_URL", "https://example.com")
        self.urls = {
            "book_appointment": f"{target_base}/book-your-appointment",
            "login": f"{target_base}/login",
            "dashboard": f"{target_base}/dashboard",
            "your_details": f"{target_base}/your-details",
            "application_details": f"{target_base}/applicationdetails",
        }
    
    def validate(self) -> tuple[bool, list[str]]:
        """Config değerlerini doğrula"""
        errors = []
        
        if not self.target_email:
            errors.append("TARGET_EMAIL is required")
        if not self.target_password:
            errors.append("TARGET_PASSWORD is required")
        if not self.applicant.first_name:
            errors.append("APPLICANT_FIRST_NAME boş olamaz")
        if not self.applicant.last_name:
            errors.append("APPLICANT_LAST_NAME boş olamaz")
        if not self.applicant.passport_no:
            errors.append("APPLICANT_PASSPORT_NO boş olamaz")
        if not self.applicant.phone_number:
            errors.append("APPLICANT_PHONE_NUMBER boş olamaz")
        if not self.applicant.email:
            errors.append("APPLICANT_EMAIL boş olamaz")
            
        return len(errors) == 0, errors


# Global config instance
config = Config()
