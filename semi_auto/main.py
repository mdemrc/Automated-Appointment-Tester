"""
Semi-Automatic Assistant
Basit akış: Bağlan → OTP Bekle → F ile Form Doldur
"""

import os
import sys
import time
from datetime import datetime
from colorama import Fore, Style, init

from config import USER_INFO, APPOINTMENT_INFO, OTP_SERVER
from otp_listener import OTPListener
from form_filler import FormFiller

init(autoreset=True)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║          {Fore.YELLOW}Semi-Automatic Form Assistant{Fore.CYAN}                   ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}"""
    print(banner)


def print_user_info():
    print(f"{Fore.CYAN}{'═'*60}")
    print(f"📋 KAYITLI BİLGİLER")
    print(f"{'═'*60}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Ad:{Style.RESET_ALL}           {Fore.GREEN}{USER_INFO['first_name']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Soyad:{Style.RESET_ALL}        {Fore.GREEN}{USER_INFO['last_name']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Cinsiyet:{Style.RESET_ALL}     {Fore.GREEN}{USER_INFO['gender']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Uyruk:{Style.RESET_ALL}        {Fore.GREEN}{USER_INFO['nationality']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Pasaport No:{Style.RESET_ALL}  {Fore.GREEN}{USER_INFO['passport_no']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Geçerlilik:{Style.RESET_ALL}   {Fore.GREEN}{USER_INFO['passport_expiry']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Tel Kodu:{Style.RESET_ALL}     {Fore.GREEN}+{USER_INFO['phone_code']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Telefon:{Style.RESET_ALL}      {Fore.GREEN}{USER_INFO['phone_number']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Email:{Style.RESET_ALL}        {Fore.GREEN}{USER_INFO['email']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Kategori:{Style.RESET_ALL}     {Fore.YELLOW}{APPOINTMENT_INFO['category']}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}Alt Kategori:{Style.RESET_ALL} {Fore.YELLOW}{APPOINTMENT_INFO['subcategory']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")


def main():
    clear_screen()
    print_banner()
    print_user_info()
    
    # Form Filler
    form_filler = FormFiller()
    
    # OTP Listener
    otp_listener = OTPListener(OTP_SERVER["url"], OTP_SERVER["api_key"])
    last_otp = None
    
    # 1. TARAYICI BAŞLAT
    print(f"\n{Fore.CYAN}[1/3] Tarayıcı başlatılıyor...{Style.RESET_ALL}")
    input(f"{Fore.GREEN}Enter'a bas...{Style.RESET_ALL}")
    
    if not form_filler.start_browser():
        print(f"{Fore.RED}Tarayıcı başlatılamadı!{Style.RESET_ALL}")
        return
    
    # target site'a git
    print(f"\n{Fore.CYAN}target login page is being opened...{Style.RESET_ALL}")
    form_filler.go_to_target()
    
    print(f"\n{Fore.YELLOW}👆 Şimdi tarayıcıda LOGIN yap!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   Email ve şifre gir, sonra OTP beklenecek...{Style.RESET_ALL}")
    
    # 2. OTP BEKLE
    print(f"\n{Fore.CYAN}[2/3] OTP bekleniyor...{Style.RESET_ALL}")
    
    last_otp = otp_listener.wait_for_otp(OTP_SERVER["check_interval"])
    
    if last_otp:
        print(f"\n{Fore.GREEN}{'='*50}")
        print(f"   ✅ OTP: {last_otp}")
        print(f"{'='*50}{Style.RESET_ALL}")
        
        # OTP'yi otomatik gir
        print(f"\n{Fore.CYAN}OTP sayfasındaysan otomatik girilsin mi? (e/h): {Style.RESET_ALL}", end="")
        if input().lower() == 'e':
            form_filler.enter_otp(last_otp)
    
    # 3. FORM DOLDUR
    print(f"\n{Fore.CYAN}[3/3] Form doldurma{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   'your-details' sayfasına gelince 'f' yaz{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   Çıkmak için 'q'{Style.RESET_ALL}")
    
    while True:
        try:
            cmd = input(f"\n{Fore.GREEN}Komut (f=form, q=çıkış): {Style.RESET_ALL}").strip().lower()
            
            if cmd == "f":
                print(f"\n{Fore.CYAN}📝 Form dolduruluyor...{Style.RESET_ALL}")
                
                # Sayfayı kontrol et
                current_url = form_filler.driver.current_url
                
                if "your-details" in current_url:
                    form_filler.fill_your_details(USER_INFO)
                    print(f"\n{Fore.GREEN}✅ Form dolduruldu!{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}   Kontrol et ve 'Kaydet' butonuna bas.{Style.RESET_ALL}")
                    print(f"\n{Fore.CYAN}İşim bitti! Gerisini sen halledersin 👋{Style.RESET_ALL}")
                    break
                    
                elif "applicationdetails" in current_url:
                    form_filler.fill_application_details(APPOINTMENT_INFO)
                    print(f"\n{Fore.GREEN}✅ Kategori seçildi!{Style.RESET_ALL}")
                    
                else:
                    print(f"{Fore.YELLOW}⚠️ Bilinmeyen sayfa: {current_url}{Style.RESET_ALL}")
                    print(f"   'your-details' veya 'applicationdetails' sayfasında olmalısın")
            
            elif cmd == "q":
                print(f"\n{Fore.YELLOW}Çıkış! 👋{Style.RESET_ALL}")
                break
            
            elif cmd == "":
                continue
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Çıkış!{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}Hata: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
