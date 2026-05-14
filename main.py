"""
Automated Appointment Tester - main runner.
Runs an undetected Chrome driver, drives the target form, and forwards
notifications through Telegram or a self-hosted OTP relay.
"""

import sys
import time
import threading
from datetime import datetime
from colorama import Fore, Style, init

from config import config
from appointment_bot import AppointmentBot
from notifications import notifier
from remote_otp_client import RemoteOTPClient

init(autoreset=True)


def print_banner():
    banner = f"""
{Fore.CYAN}=======================================================
  Automated Appointment Tester
  Browser automation harness (educational)
======================================================={Style.RESET_ALL}
"""
    print(banner)


def print_config_summary():
    """Config özetini göster"""
    print(f"\n{Fore.CYAN}📋 Yapılandırma:{Style.RESET_ALL}")
    print(f"   Email: {config.target_email}")
    print(f"   Başvuru Sahibi: {config.applicant.first_name} {config.applicant.last_name}")
    print(f"   Kategori: {config.appointment.category}")
    print(f"   Alt Kategori: {config.appointment.subcategory}")
    print(f"   Telegram: {'✅ Yapılandırılmış' if config.telegram.is_configured else '❌ Yapılandırılmamış'}")
    print(f"   Headless Mode: {'✅ Açık' if config.bot.headless else '❌ Kapalı'}")
    print(f"   Kontrol Aralığı: {config.bot.check_interval} saniye")
    
    # OTP durumu
    if config.remote_otp.enabled and config.remote_otp.server_url:
        print(f"   OTP: {Fore.GREEN}✅ Ubuntu Sunucu ({config.remote_otp.server_url}){Style.RESET_ALL}")
    else:
        print(f"   OTP: {Fore.YELLOW}⚠ Manuel giriş{Style.RESET_ALL}")
    print()


def setup_otp_client():
    """OTP Client'ı yapılandır"""
    
    # Remote OTP (Ubuntu sunucu) - Öncelikli
    if config.remote_otp.enabled and config.remote_otp.server_url:
        client = RemoteOTPClient(
            server_url=config.remote_otp.server_url,
            api_key=config.remote_otp.api_key
        )
        
        # Health check
        print(f"{Fore.CYAN}🔗 Ubuntu sunucuya bağlanılıyor...{Style.RESET_ALL}")
        if client.health_check():
            print(f"{Fore.GREEN}✓ Sunucu bağlantısı OK: {config.remote_otp.server_url}{Style.RESET_ALL}")
            return client
        else:
            print(f"{Fore.RED}✗ Sunucuya bağlanılamadı! Manuel OTP kullanılacak.{Style.RESET_ALL}")
            return None
    
    print(f"{Fore.YELLOW}⚠ Remote OTP yapılandırılmamış - Manuel OTP kullanılacak{Style.RESET_ALL}")
    return None
def single_check(otp_client=None):
    """Tek seferlik kontrol yap"""
    print(f"\n{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] Kontrol başlatılıyor...{Style.RESET_ALL}")
    
    bot = AppointmentBot()
    
    try:
        bot.start()
        
        # Login
        print(f"{Fore.YELLOW}➤ Login sayfasına gidiliyor...{Style.RESET_ALL}")
        if not bot.login():
            print(f"{Fore.RED}✗ Login başarısız!{Style.RESET_ALL}")
            return False, "Login başarısız"
        
        # OTP
        print(f"\n{Fore.GREEN}✓ Login başarılı! OTP bekleniyor...{Style.RESET_ALL}")
        
        # Remote OTP Server aktifse otomatik al
        if otp_client:
            timeout = config.remote_otp.timeout
            print(f"{Fore.CYAN}📱 Ubuntu sunucudan YENİ OTP bekleniyor... (Timeout: {timeout}s){Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Telefonunuza SMS geldiğinde Tasker otomatik iletecek{Style.RESET_ALL}")
            
            # Yeni OTP için bekle (eski OTP'yi temizler ve yeni gelene kadar bekler)
            otp_code = otp_client.wait_for_fresh_otp(timeout=timeout, initial_delay=5)
            
            if not otp_code:
                print(f"{Fore.RED}✗ OTP timeout! SMS alınamadı.{Style.RESET_ALL}")
                # Manuel girişe düş
                otp_code = input(f"{Fore.YELLOW}📱 Manuel OTP girin (veya 'q' çıkış): {Style.RESET_ALL}")
                if otp_code.lower() == 'q':
                    return False, "OTP iptal edildi"
            else:
                print(f"{Fore.GREEN}✓ OTP alındı: {otp_code}{Style.RESET_ALL}")
        else:
            otp_code = input(f"{Fore.YELLOW}📱 SMS'ten gelen OTP kodunu girin: {Style.RESET_ALL}")
        
        if not bot.enter_otp(otp_code):
            print(f"{Fore.RED}✗ OTP doğrulama başarısız!{Style.RESET_ALL}")
            return False, "OTP doğrulama başarısız"
        
        print(f"{Fore.GREEN}✓ OTP doğrulandı!{Style.RESET_ALL}")
        
        # Dashboard
        print(f"{Fore.YELLOW}➤ Dashboard işlemleri yapılıyor...{Style.RESET_ALL}")
        if not bot.complete_dashboard_checkboxes():
            print(f"{Fore.RED}✗ Dashboard adımı başarısız!{Style.RESET_ALL}")
            return False, "Dashboard adımı başarısız"
        
        print(f"{Fore.GREEN}✓ Dashboard tamamlandı!{Style.RESET_ALL}")
        
        # Form doldurma
        print(f"{Fore.YELLOW}➤ Başvuru formu dolduruluyor...{Style.RESET_ALL}")
        if not bot.fill_applicant_details():
            print(f"{Fore.RED}✗ Form doldurma başarısız!{Style.RESET_ALL}")
            return False, "Form doldurma başarısız"
        
        print(f"{Fore.GREEN}✓ Form dolduruldu!{Style.RESET_ALL}")
        
        # Kategori seçimi
        print(f"{Fore.YELLOW}➤ Randevu kategorisi seçiliyor...{Style.RESET_ALL}")
        if not bot.select_appointment_category():
            print(f"{Fore.RED}✗ Kategori seçimi başarısız!{Style.RESET_ALL}")
            return False, "Kategori seçimi başarısız"
        
        print(f"{Fore.GREEN}✓ Kategori seçildi!{Style.RESET_ALL}")
        
        # Müsaitlik kontrolü
        print(f"{Fore.YELLOW}➤ Randevu müsaitliği kontrol ediliyor...{Style.RESET_ALL}")
        available, message = bot.check_availability()
        
        return available, message
        
    except Exception as e:
        print(f"{Fore.RED}✗ Hata: {e}{Style.RESET_ALL}")
        return False, str(e)
    
    finally:
        bot.stop()


def continuous_check(otp_client=None):
    """Sürekli kontrol modu"""
    check_count = 0
    
    while True:
        check_count += 1
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"📍 Kontrol #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        available, message = single_check(otp_client)
        
        if available:
            print(f"\n{Fore.GREEN}{'='*60}")
            print(f"🎉🎉🎉 RANDEVU BULUNDU! 🎉🎉🎉")
            print(f"Mesaj: {message}")
            print(f"{'='*60}{Style.RESET_ALL}")
            
            # Telegram bildirimi gönder
            notifier.notify_appointment_found(message)
            
            # Ses çal (Windows)
            try:
                import winsound
                for _ in range(5):
                    winsound.Beep(1000, 500)
                    time.sleep(0.5)
            except:
                pass
            
            # Kullanıcıya sor
            continue_check = input(f"\n{Fore.YELLOW}Kontrole devam edilsin mi? (e/h): {Style.RESET_ALL}")
            if continue_check.lower() != 'e':
                break
        else:
            print(f"\n{Fore.YELLOW}❌ Randevu bulunamadı: {message}{Style.RESET_ALL}")
        
        # Sonraki kontrol için bekle
        print(f"\n{Fore.CYAN}⏳ {config.bot.check_interval} saniye sonra tekrar kontrol edilecek...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   (Çıkmak için Ctrl+C){Style.RESET_ALL}")
        
        try:
            time.sleep(config.bot.check_interval)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Bot durduruldu.{Style.RESET_ALL}")
            break


def main():
    """Ana fonksiyon"""
    print_banner()
    
    # Config doğrulama
    is_valid, errors = config.validate()
    if not is_valid:
        print(f"{Fore.RED}❌ Yapılandırma hataları:{Style.RESET_ALL}")
        for error in errors:
            print(f"   - {error}")
        print(f"\n{Fore.YELLOW}Lütfen .env dosyasını kontrol edin.{Style.RESET_ALL}")
        sys.exit(1)
    
    print_config_summary()
    
    # OTP Client kur (Ubuntu sunucu)
    otp_client = setup_otp_client()
    
    # Mod seçimi
    print(f"{Fore.CYAN}Mod seçin:{Style.RESET_ALL}")
    print("  1. Tek seferlik kontrol")
    print("  2. Sürekli kontrol (döngü)")
    print()
    
    mode = input(f"{Fore.YELLOW}Seçiminiz (1/2): {Style.RESET_ALL}")
    
    if mode == "1":
        available, message = single_check(otp_client)
        if available:
            notifier.notify_appointment_found(message)
            print(f"\n{Fore.GREEN}🎉 RANDEVU MEVCUT! {message}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}❌ {message}{Style.RESET_ALL}")
    
    elif mode == "2":
        continuous_check(otp_client)
    
    else:
        print(f"{Fore.RED}Geçersiz seçim!{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Çıkış yapıldı.{Style.RESET_ALL}")
