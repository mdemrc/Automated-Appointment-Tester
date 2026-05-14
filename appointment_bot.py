"""
Browser driver using undetected-chromedriver.
Encapsulates the Selenium session, retry/wait helpers, and high-level
actions for the appointment form.
"""

import time
import os
from datetime import datetime
from typing import Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from colorama import Fore, Style, init

from config import config, Config

init(autoreset=True)


class AppointmentBot:
    """Undetected Chrome session that drives the appointment form."""
    
    def __init__(self, cfg: Config = config):
        self.config = cfg
        self.driver: Optional[uc.Chrome] = None
        
    def log(self, message: str, level: str = "info"):
        """Renkli log mesajı"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colors = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "debug": Fore.MAGENTA
        }
        color = colors.get(level, Fore.WHITE)
        print(f"{color}[{timestamp}] [{level.upper()}] {message}{Style.RESET_ALL}")
    
    def start(self):
        """Browser'ı başlat"""
        self.log("Undetected Chrome başlatılıyor...", "info")
        
        options = uc.ChromeOptions()
        
        # Headless mod
        if self.config.bot.headless:
            options.add_argument("--headless=new")
        
        # Türkçe dil
        options.add_argument("--lang=tr-TR")
        options.add_argument("--accept-lang=tr-TR,tr,en-US,en")
        
        # Pencere boyutu
        options.add_argument("--window-size=1366,768")
        
        # Diğer ayarlar
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        
        # Profile dizini (cookie'ler kalıcı olsun)
        profile_dir = os.path.join(os.path.dirname(__file__), "chrome_profile")
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Undetected Chrome başlat
        self.driver = uc.Chrome(options=options, use_subprocess=True)
        self.driver.implicitly_wait(10)
        
        self.log("Browser başlatıldı!", "success")
    
    def stop(self):
        """Browser'ı kapat"""
        if self.driver:
            self.driver.quit()
        self.log("Browser kapatıldı", "info")
    
    def wait_and_click(self, by, value, timeout=15):
        """Element görünene kadar bekle ve tıkla"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return element
    
    def wait_and_type(self, by, value, text, timeout=15):
        """Element görünene kadar bekle ve yaz"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        element.clear()
        element.send_keys(text)
        return element
    
    def handle_cookie_popup(self):
        """Cookie popup'ını kapat (varsa) - hızlı kontrol"""
        try:
            # Hemen kontrol et, bekleme yok
            buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Tüm Tanımlama Bilgilerini Kabul Et')] | "
                "//button[contains(text(), 'Kabul Et')] | "
                "//button[contains(text(), 'Accept')]"
            )
            for btn in buttons:
                if btn.is_displayed():
                    btn.click()
                    self.log("Cookie popup kapatıldı", "success")
                    return True
        except:
            pass
        return False
    
    def wait_for_cloudflare(self, timeout=30):
        """Cloudflare geçişini bekle"""
        self.log("Cloudflare kontrolü...", "info")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                page_source = self.driver.page_source
                
                # Hata kontrolü
                if '"code":"403' in page_source:
                    self.log("Bot algılandı! Sayfa yenileniyor...", "warning")
                    time.sleep(3)
                    self.driver.refresh()
                    time.sleep(2)
                    continue
                
                # Cloudflare başarılı mı kontrol et
                if "Başarılı" in page_source or "Success" in page_source:
                    self.log("Cloudflare geçildi!", "success")
                    time.sleep(1)
                    return True
                
                # Login formu görünür mü
                if "oturum aç" in page_source.lower() or "e-posta" in page_source.lower():
                    self.log("Sayfa hazır!", "success")
                    return True
                
                # Challenge devam ediyor mu
                if "checking" in page_source.lower() or "Doğrulanıyor" in page_source:
                    time.sleep(1)
                    continue
                    
            except:
                pass
            
            time.sleep(1)
        
        # Timeout olsa bile devam et
        self.log("Cloudflare timeout, yine de devam ediliyor...", "warning")
        return True
    
    def login(self) -> bool:
        """target site'a giriş yap"""
        
        # Doğrudan login sayfasına git
            login_url = self.config.urls.get("login", "")
        self.log(f"Login sayfasına gidiliyor: {login_url}", "info")
        self.driver.get(login_url)
        time.sleep(3)
        
        # Cookie popup (hızlı kontrol)
        self.handle_cookie_popup()
        
        # Sayfanın tam yüklenmesini bekle
        time.sleep(5)
        
        try:
            # iframe kontrolü
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.log(f"Sayfada {len(iframes)} iframe bulundu", "debug")
            
            # Ana sayfadaki input'ları kontrol et
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.log(f"Ana sayfada {len(all_inputs)} input var", "debug")
            
            # Eğer az input varsa iframe'e geçmeyi dene
            if len(all_inputs) < 3 and len(iframes) > 0:
                for idx, iframe in enumerate(iframes):
                    try:
                        self.driver.switch_to.frame(iframe)
                        iframe_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        self.log(f"iframe {idx}: {len(iframe_inputs)} input", "debug")
                        if len(iframe_inputs) >= 2:
                            self.log(f"iframe {idx}'e geçildi", "debug")
                            break
                        self.driver.switch_to.default_content()
                    except:
                        self.driver.switch_to.default_content()
            
            # Email input'u bul
            email_input = None
            
            # Yöntem 1: ID ile (id="email")
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                self.log("Email input (id=email) bulundu", "debug")
            except Exception as e1:
                self.log(f"id=email bulunamadı", "debug")
            
            # Yöntem 2: CSS selector ile
            if not email_input:
                try:
                    email_input = self.driver.find_element(By.CSS_SELECTOR, "input#email")
                    self.log("Email input (CSS #email) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 3: placeholder ile
            if not email_input:
                try:
                    email_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='jane.doe@email.com']")
                    self.log("Email input (placeholder) bulundu", "debug")
                except:
                    pass
                    
            # Yöntem 4: XPath ile
            if not email_input:
                try:
                    email_input = self.driver.find_element(By.XPATH, "//input[@id='email']")
                    self.log("Email input (XPath) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 5: mat-input class ile
            if not email_input:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input.mat-mdc-input-element")
                    for inp in inputs:
                        inp_type = inp.get_attribute("type") or ""
                        if inp_type in ["text", "email", ""] and inp.is_displayed():
                            email_input = inp
                            self.log("Email input (mat-input) bulundu", "debug")
                            break
                except:
                    pass
            
            # Yöntem 6: Tüm görünür input'ları tara
            if not email_input:
                try:
                    all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    self.log(f"Toplam {len(all_inputs)} input bulundu", "debug")
                    for inp in all_inputs:
                        try:
                            inp_type = inp.get_attribute("type") or ""
                            inp_class = inp.get_attribute("class") or ""
                            inp_hidden = inp.get_attribute("aria-hidden") or ""
                            
                            # Gizli değilse ve text/email tipindeyse
                            if inp_type in ["text", "email", ""] and "d-none" not in inp_class and inp_hidden != "true":
                                if inp.is_displayed():
                                    email_input = inp
                                    self.log(f"Email input (manuel) bulundu: type={inp_type}", "debug")
                                    break
                        except:
                            continue
                except Exception as e4:
                    self.log(f"Manuel tarama hatası: {str(e4)[:100]}", "debug")
            
            if not email_input:
                # Debug: Screenshot ve page source
                self.driver.save_screenshot("debug_login.png")
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                self.log("Email input bulunamadı! Screenshot: debug_login.png, HTML: debug_page.html", "error")
                return False
            
            self.log("Login formu bulundu", "success")
            
            # JavaScript ile değer yaz (Angular reactive form için)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", email_input)
            time.sleep(0.3)
            
            # Email gir - JavaScript ile
            self.driver.execute_script("arguments[0].value = '';", email_input)
            self.driver.execute_script(f"arguments[0].value = '{self.config.target_email}';", email_input)
            # Input event tetikle (Angular için)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", email_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", email_input)
            self.log("Email girildi", "debug")
            
            time.sleep(0.5)
            
            # Şifre input'u bul (id="password")
            password_input = None
            try:
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input#password"))
                )
            except:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='password']")
                except:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            # JavaScript ile şifre yaz
            self.driver.execute_script("arguments[0].scrollIntoView(true);", password_input)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].value = '';", password_input)
            self.driver.execute_script(f"arguments[0].value = '{self.config.target_password}';", password_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password_input)
            self.log("Şifre girildi", "debug")
            
            # Cloudflare Turnstile kontrolü - Başarılı yazısını bekle
            self.log("Cloudflare Turnstile bekleniyor...", "info")
            for i in range(15):  # Max 15 saniye
                try:
                    page_source = self.driver.page_source
                    if "Başarılı" in page_source or "Success" in page_source:
                        self.log("Cloudflare Turnstile geçildi!", "success")
                        break
                    # Zaten geçilmişse (checkbox yok)
                    if i > 5:
                        cf_frames = self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'cloudflare')]")
                        if len(cf_frames) == 0:
                            self.log("Cloudflare yok, devam ediliyor", "debug")
                            break
                except:
                    pass
                time.sleep(1)
            
            time.sleep(1)
            
            # Login butonu - farklı yöntemler dene
            login_btn = None
            
            # Yöntem 1: btn-brand-orange class'ı ile (primary orange button)
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-brand-orange")
                self.log("Login butonu (btn-brand-orange) bulundu", "debug")
            except:
                pass
            
            # Yöntem 2: mdc-button__label içinde "Oturum Aç"
            if not login_btn:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Oturum Aç')]]")
                    self.log("Login butonu (span içinde Oturum Aç) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 3: mat-mdc-outlined-button class'ı ile
            if not login_btn:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.mat-mdc-outlined-button")
                    self.log("Login butonu (mat-mdc-outlined-button) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 4: Text içeriği ile (normalize edilmiş)
            if not login_btn:
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        btn_text = btn.text.strip().lower()
                        if "oturum" in btn_text or "giriş" in btn_text or "login" in btn_text:
                            login_btn = btn
                            self.log(f"Login butonu (text: {btn_text}) bulundu", "debug")
                            break
                except:
                    pass
            
            # Yöntem 5: Form içindeki button
            if not login_btn:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, "form button")
                    self.log("Login butonu (form button) bulundu", "debug")
                except:
                    pass
            
            if not login_btn:
                self.log("Login butonu bulunamadı!", "error")
                self.driver.save_screenshot("debug_login_btn.png")
                return False
            
            # Butona tıkla
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
            time.sleep(0.3)
            login_btn.click()
            
            self.log("Login butonu tıklandı, OTP bekleniyor...", "info")
            
            # OTP sayfası bekle
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'tek seferlik') or contains(text(), 'OTP') or contains(text(), 'doğrulama')]"))
                )
                self.log("OTP sayfasına yönlendirildi!", "success")
                return True
            except:
                # Belki direkt dashboard'a gitti
                if "dashboard" in self.driver.current_url:
                    self.log("Dashboard'a yönlendirildi!", "success")
                    return True
                self.log("OTP sayfası bulunamadı", "error")
                return False
                
        except Exception as e:
            self.log(f"Login hatası: {e}", "error")
            return False
    
    def enter_otp(self, otp_code: str) -> bool:
        """OTP kodunu gir"""
        self.log(f"OTP kodu giriliyor: {otp_code}", "info")
        
        try:
            time.sleep(2)  # Sayfanın yüklenmesini bekle
            
            # OTP input bul - çeşitli yöntemler
            otp_input = None
            
            # Yöntem 1: id=otp ile
            try:
                otp_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "otp"))
                )
                self.log("OTP input (id=otp) bulundu", "debug")
            except:
                pass
            
            # Yöntem 2: formcontrolname ile
            if not otp_input:
                try:
                    otp_input = self.driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='otp']")
                    self.log("OTP input (formcontrolname) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 3: mat-input class ile
            if not otp_input:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input.mat-mdc-input-element")
                    for inp in inputs:
                        if inp.is_displayed():
                            otp_input = inp
                            self.log("OTP input (mat-input) bulundu", "debug")
                            break
                except:
                    pass
            
            # Yöntem 4: Görünür text/password input
            if not otp_input:
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        inp_type = inp.get_attribute("type") or ""
                        if inp_type in ["text", "password", "tel", "number"] and inp.is_displayed():
                            otp_input = inp
                            self.log(f"OTP input (type={inp_type}) bulundu", "debug")
                            break
                except:
                    pass
            
            if not otp_input:
                self.log("OTP input bulunamadı!", "error")
                self.driver.save_screenshot("debug_otp.png")
                return False
            
            # JavaScript ile değer yaz
            self.driver.execute_script("arguments[0].value = '';", otp_input)
            self.driver.execute_script(f"arguments[0].value = '{otp_code}';", otp_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", otp_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", otp_input)
            self.log("OTP kodu girildi", "debug")
            
            time.sleep(3)  # Cloudflare için bekle
            
            # Oturum Aç butonu - çeşitli yöntemler
            login_btn = None
            
            # Yöntem 1: btn-brand-orange
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-brand-orange")
                self.log("OTP butonu (btn-brand-orange) bulundu", "debug")
            except:
                pass
            
            # Yöntem 2: span içinde text
            if not login_btn:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Oturum Aç')]]")
                    self.log("OTP butonu (span text) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 3: mat-mdc-outlined-button
            if not login_btn:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.mat-mdc-outlined-button")
                    self.log("OTP butonu (mat-mdc-outlined) bulundu", "debug")
                except:
                    pass
            
            # Yöntem 4: Text ile
            if not login_btn:
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        btn_text = btn.text.strip().lower()
                        if "oturum" in btn_text or "doğrula" in btn_text or "verify" in btn_text:
                            login_btn = btn
                            self.log(f"OTP butonu (text: {btn_text}) bulundu", "debug")
                            break
                except:
                    pass
            
            # Yöntem 5: Form içindeki button
            if not login_btn:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, "form button")
                    self.log("OTP butonu (form button) bulundu", "debug")
                except:
                    pass
            
            if not login_btn:
                self.log("OTP butonu bulunamadı!", "error")
                self.driver.save_screenshot("debug_otp_btn.png")
                return False
            
            # Butona tıkla
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
            time.sleep(0.3)
            login_btn.click()
            
            self.log("OTP butonu tıklandı", "info")
            
            # Dashboard bekle
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.url_contains("dashboard")
                )
                self.log("Dashboard'a giriş yapıldı!", "success")
                return True
            except:
                # URL'de dashboard olmasa bile sayfa içeriğini kontrol et
                current_url = self.driver.current_url
                self.log(f"Şu anki URL: {current_url}", "debug")
                if "appointment" in current_url or "schedule" in current_url:
                    self.log("Randevu sayfasına yönlendirildi!", "success")
                    return True
                self.log("Dashboard'a yönlendirilemedi", "error")
                self.driver.save_screenshot("debug_after_otp.png")
                return False
                
        except Exception as e:
            self.log(f"OTP hatası: {e}", "error")
            return False
    
    def complete_dashboard_checkboxes(self) -> bool:
        """Dashboard'daki checkbox'ları işaretle"""
        self.log("Dashboard checkbox'ları işaretleniyor...", "info")
        
        time.sleep(2)
        
        try:
            # Mat-checkbox bileşenlerindeki input'ları bul ve işaretle
            # Angular Material checkbox yapısı: mat-checkbox > div > div.mdc-checkbox > input
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "mat-checkbox input[type='checkbox']")
            
            if not checkboxes:
                # Alternatif selector
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, ".mdc-checkbox__native-control")
            
            if not checkboxes:
                # En genel selector
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            for cb in checkboxes:
                if not cb.is_selected():
                    try:
                        # Önce scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                        time.sleep(0.3)
                        cb.click()
                        time.sleep(0.5)
                    except:
                        # JavaScript ile tıkla
                        self.driver.execute_script("arguments[0].click();", cb)
                        time.sleep(0.5)
            
            self.log(f"{len(checkboxes)} checkbox işaretlendi", "success")
            
            time.sleep(1)
            
            # "Yeni Rezervasyon Başlat" butonu - btn-brand-orange class'ı ile
            self.log("'Yeni Rezervasyon Başlat' butonuna tıklanıyor...", "info")
            
            # Önce butonun görünür olmasını bekle
            new_res_btn = None
            
            # Selector stratejileri
            selectors = [
                # btn-brand-orange class'ı ile (HTML'de gördüğümüz)
                (By.CSS_SELECTOR, "button.btn-brand-orange"),
                # mdc-button class'ı ile
                (By.CSS_SELECTOR, "button.mdc-button--raised.btn-brand-orange"),
                # mat-raised-button ile
                (By.CSS_SELECTOR, "button.mat-mdc-raised-button.btn-brand-orange"),
                # Metin içeriği ile
                (By.XPATH, "//button[contains(@class, 'btn-brand-orange')]"),
                # Span içindeki metin ile
                (By.XPATH, "//button[.//span[contains(text(), 'Yeni Rezervasyon')]]"),
                # mdc-button__label içindeki metin
                (By.XPATH, "//button[contains(@class, 'mdc-button')]//span[contains(text(), 'Yeni Rezervasyon')]/ancestor::button"),
            ]
            
            for selector_type, selector in selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    # Desktop versiyonu (d-lg-inline-block class'ı olan) tercih et
                    for elem in elements:
                        if elem.is_displayed():
                            new_res_btn = elem
                            self.log(f"Buton bulundu: {selector}", "info")
                            break
                    if new_res_btn:
                        break
                except:
                    continue
            
            if not new_res_btn:
                raise Exception("'Yeni Rezervasyon Başlat' butonu bulunamadı")
            
            # Butona scroll
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", new_res_btn)
            time.sleep(0.5)
            
            # Tıkla
            try:
                new_res_btn.click()
            except:
                self.driver.execute_script("arguments[0].click();", new_res_btn)
            
            self.log("Butona tıklandı, Şartlar ve Koşullar sayfası yükleniyor...", "info")
            time.sleep(3)
            
            # Şartlar ve Koşullar sayfasındaki checkbox'ı işaretle
            # HTML yapısı: mat-checkbox > div.mdc-form-field > div.mdc-checkbox > input.mdc-checkbox__native-control
            self.log("'Şartlar ve Koşullar' checkbox'ı aranıyor...", "info")
            
            checkbox_selectors = [
                # ID ile direkt
                (By.ID, "mat-mdc-checkbox-2-input"),
                # mat-checkbox içindeki input
                (By.CSS_SELECTOR, "mat-checkbox input.mdc-checkbox__native-control"),
                (By.CSS_SELECTOR, "mat-checkbox input[type='checkbox']"),
                # Class ile
                (By.CSS_SELECTOR, ".mdc-checkbox__native-control"),
                # Genel
                (By.CSS_SELECTOR, "input[type='checkbox']"),
            ]
            
            checkbox_found = False
            for selector_type, selector in checkbox_selectors:
                try:
                    checkboxes = self.driver.find_elements(selector_type, selector)
                    for cb in checkboxes:
                        if not cb.is_selected():
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                                time.sleep(0.3)
                                cb.click()
                                checkbox_found = True
                                self.log("Şartlar ve Koşullar checkbox'ı işaretlendi", "success")
                            except:
                                self.driver.execute_script("arguments[0].click();", cb)
                                checkbox_found = True
                                self.log("Şartlar ve Koşullar checkbox'ı JS ile işaretlendi", "success")
                        else:
                            checkbox_found = True
                            self.log("Şartlar ve Koşullar checkbox'ı zaten işaretli", "info")
                    if checkbox_found:
                        break
                except:
                    continue
            
            time.sleep(1)
            
            # "Devam et" butonu - mat-mdc-outlined-button class'ı ile (Şartlar sayfasında)
            # HTML: button.btn-brand-orange.mdc-button--outlined.mat-mdc-outlined-button
            self.log("'Devam et' butonuna tıklanıyor...", "info")
            
            continue_btn = None
            continue_selectors = [
                # Outlined button (Şartlar sayfasında)
                (By.CSS_SELECTOR, "button.btn-brand-orange.mat-mdc-outlined-button"),
                (By.CSS_SELECTOR, "button.btn-brand-orange.mdc-button--outlined"),
                # Genel btn-brand-orange
                (By.CSS_SELECTOR, "button.btn-brand-orange"),
                # Span içindeki metin ile
                (By.XPATH, "//button[.//span[contains(text(), 'Devam et')]]"),
                (By.XPATH, "//button[.//span[contains(text(), 'Devam')]]"),
                # mat-stroked-button attribute
                (By.CSS_SELECTOR, "button[mat-stroked-button]"),
                # Genel mdc-button
                (By.XPATH, "//button[contains(@class, 'btn-brand-orange')]"),
            ]
            
            for selector_type, selector in continue_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            continue_btn = elem
                            self.log(f"Devam et butonu bulundu: {selector}", "info")
                            break
                    if continue_btn:
                        break
                except:
                    continue
            
            if continue_btn:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                time.sleep(0.5)
                try:
                    continue_btn.click()
                    self.log("Devam et butonuna tıklandı", "success")
                except:
                    self.driver.execute_script("arguments[0].click();", continue_btn)
                    self.log("Devam et butonuna JS ile tıklandı", "success")
            else:
                self.log("Devam et butonu bulunamadı!", "warning")
            
            # your-details sayfası bekle
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("your-details")
            )
            self.log("Detaylar sayfasına yönlendirildi", "success")
            return True
            
        except Exception as e:
            self.log(f"Dashboard hatası: {e}", "error")
            return False
    
    def fill_applicant_details(self) -> bool:
        """Başvuru sahibi detaylarını doldur"""
        self.log("Başvuru bilgileri dolduruluyor...", "info")
        
        time.sleep(2)
        
        try:
            # İsim (mat-input-4)
            self.log("İsim giriliyor...", "debug")
            first_name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "mat-input-4"))
            )
            first_name_input.clear()
            first_name_input.send_keys(self.config.applicant.first_name)
            
            # Soyisim (mat-input-5)
            self.log("Soyisim giriliyor...", "debug")
            last_name_input = self.driver.find_element(By.ID, "mat-input-5")
            last_name_input.clear()
            last_name_input.send_keys(self.config.applicant.last_name)
            
            time.sleep(1)
            
            # Cinsiyet dropdown (mat-select - Angular Material)
            self.log("Cinsiyet seçiliyor...", "debug")
            # Gender mapping: Male -> Erkek, Female -> Kadın
            gender_map = {
                "male": "Erkek",
                "female": "Kadın",
                "erkek": "Erkek",
                "kadın": "Kadın"
            }
            gender_value = gender_map.get(self.config.applicant.gender.lower(), self.config.applicant.gender)
            self._select_mat_option("mat-select-0", gender_value)
            
            time.sleep(0.5)
            
            # Uyruk dropdown (mat-select - Angular Material)
            self.log("Uyruk seçiliyor...", "debug")
            self._select_mat_option("mat-select-1", self.config.applicant.nationality)
            
            time.sleep(0.5)
            
            # Pasaport numarası (mat-input-6)
            self.log("Pasaport numarası giriliyor...", "debug")
            passport_input = self.driver.find_element(By.ID, "mat-input-6")
            passport_input.clear()
            passport_input.send_keys(self.config.applicant.passport_no)
            
            # Telefon kodu (mat-input-7)
            self.log("Telefon kodu giriliyor...", "debug")
            phone_code_input = self.driver.find_element(By.ID, "mat-input-7")
            phone_code_input.clear()
            phone_code_input.send_keys(self.config.applicant.phone_code)
            
            # Telefon numarası (mat-input-8)
            self.log("Telefon numarası giriliyor...", "debug")
            phone_input = self.driver.find_element(By.ID, "mat-input-8")
            phone_input.clear()
            phone_input.send_keys(self.config.applicant.phone_number)
            
            # Email (mat-input-9)
            self.log("E-posta giriliyor...", "debug")
            email_input = self.driver.find_element(By.ID, "mat-input-9")
            email_input.clear()
            email_input.send_keys(self.config.applicant.email)
            
            self.log("Form dolduruldu", "success")
            
            # "X saniye bekleyin" sayacını bekle
            self._wait_for_countdown()
            
            # Kaydet butonu (Angular Material button)
            self.log("'Kaydet' butonuna tıklanıyor...", "info")
            save_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-brand-orange"))
            )
            self.driver.execute_script("arguments[0].click();", save_btn)
            
            # applicationdetails sayfası bekle
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("applicationdetails")
            )
            self.log("Başvuru detayları sayfasına yönlendirildi", "success")
            return True
            
        except Exception as e:
            self.log(f"Form doldurma hatası: {e}", "error")
            return False
    
    def _wait_for_countdown(self):
        """'X saniye bekleyin' sayacının bitmesini bekle"""
        self.log("Sayaç kontrol ediliyor...", "debug")
        
        try:
            # Sayfada "saniye bekleyin" ifadesini ara
            max_wait = 30  # Maksimum 30 saniye bekle
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                page_source = self.driver.page_source
                
                # "X saniye bekleyin" pattern'ini ara
                import re
                match = re.search(r'(\d+)\s*saniye\s*bekleyin', page_source, re.IGNORECASE)
                
                if match:
                    seconds = int(match.group(1))
                    if seconds > 0:
                        self.log(f"⏳ {seconds} saniye bekleniyor...", "info")
                        time.sleep(1)
                    else:
                        self.log("Sayaç bitti!", "success")
                        break
                else:
                    # Sayaç yok veya bitti
                    self.log("Sayaç bulunamadı veya bitti", "debug")
                    break
                    
            time.sleep(1)  # Ekstra güvenlik için 1 saniye daha bekle
            
        except Exception as e:
            self.log(f"Sayaç bekleme hatası: {e}", "warning")
            time.sleep(3)  # Hata durumunda 3 saniye bekle
    
    def _select_mat_option(self, select_id: str, option_text: str) -> bool:
        """Angular Material mat-select için dropdown seçimi yapar"""
        try:
            # Mat-select'e tıkla
            mat_select = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, select_id))
            )
            self.driver.execute_script("arguments[0].click();", mat_select)
            
            time.sleep(0.5)
            
            # Dropdown paneli açılana kadar bekle
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.mat-mdc-select-panel"))
            )
            
            # Option'ları bul ve seç
            options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
            for option in options:
                if option_text.lower() in option.text.lower():
                    self.driver.execute_script("arguments[0].click();", option)
                    self.log(f"'{option_text}' seçildi", "debug")
                    time.sleep(0.3)
                    return True
            
            self.log(f"'{option_text}' option bulunamadı", "warning")
            return False
            
        except Exception as e:
            self.log(f"Mat-select seçim hatası: {e}", "error")
            return False
    
    def select_appointment_category(self) -> bool:
        """Randevu kategorisini seç ve müsaitlik kontrolü yap"""
        self.log("Randevu kategorisi seçiliyor...", "info")
        
        time.sleep(2)
        
        try:
            # 1. Kategori seç (ilk mat-select)
            mat_selects = self.driver.find_elements(By.CSS_SELECTOR, "mat-select")
            if len(mat_selects) > 0:
                self._select_mat_option_by_element(mat_selects[0], self.config.appointment.category)
                self.log(f"Kategori seçildi: {self.config.appointment.category}", "success")
            
            time.sleep(2)
            
            # 2. Alt kategori seç (ikinci mat-select)
            mat_selects = self.driver.find_elements(By.CSS_SELECTOR, "mat-select")
            if len(mat_selects) > 1:
                self._select_mat_option_by_element(mat_selects[1], self.config.appointment.subcategory)
                self.log(f"Alt kategori seçildi: {self.config.appointment.subcategory}", "success")
            
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.log(f"Kategori seçim hatası: {e}", "error")
            return False
    
    def _select_mat_option_by_element(self, mat_select_element, option_text: str) -> bool:
        """Mat-select elementi kullanarak dropdown seçimi yapar"""
        try:
            # Mat-select'e tıkla
            self.driver.execute_script("arguments[0].click();", mat_select_element)
            
            time.sleep(0.5)
            
            # Dropdown paneli açılana kadar bekle
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.mat-mdc-select-panel"))
            )
            
            # Option'ları bul ve seç
            options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
            for option in options:
                if option_text.lower() in option.text.lower():
                    self.driver.execute_script("arguments[0].click();", option)
                    self.log(f"'{option_text}' seçildi", "debug")
                    time.sleep(0.3)
                    return True
            
            self.log(f"'{option_text}' option bulunamadı", "warning")
            return False
            
        except Exception as e:
            self.log(f"Mat-select seçim hatası: {e}", "error")
            return False
    
    def check_availability(self) -> tuple[bool, str]:
        """Randevu müsaitliğini kontrol et - Uygulama merkezi dropdown'una bak"""
        self.log("Randevu müsaitliği kontrol ediliyor...", "info")
        
        time.sleep(2)
        
        page_source = self.driver.page_source
        
        # "randevu müsaitliği bulunamadı" mesajı var mı?
        if "müsaitliği bulunamadı" in page_source or "randevu bulunamadı" in page_source.lower():
            self.log("❌ Randevu müsaitliği bulunamadı!", "warning")
            return False, "Randevu müsaitliği bulunamadı"
        
        # Uygulama merkezi dropdown kontrolü (üçüncü mat-select)
        try:
            mat_selects = self.driver.find_elements(By.CSS_SELECTOR, "mat-select")
            
            if len(mat_selects) >= 3:
                # Üçüncü dropdown'a tıkla
                center_select = mat_selects[2]
                self.driver.execute_script("arguments[0].click();", center_select)
                
                time.sleep(0.5)
                
                # Panel açılırsa option'ları kontrol et
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.mat-mdc-select-panel"))
                    )
                    
                    options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
                    available_centers = []
                    
                    for option in options:
                        text = option.text.strip()
                        if text and "seçin" not in text.lower():
                            available_centers.append(text)
                    
                    # Panel'i kapat (Escape tuşu veya dışarı tıkla)
                    from selenium.webdriver.common.keys import Keys
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.3)
                    
                    if available_centers:
                        self.log(f"✅ RANDEVU MEVCUT! Merkezler: {available_centers}", "success")
                        return True, f"Müsait merkezler: {', '.join(available_centers)}"
                    else:
                        self.log("❌ Uygulama merkezi seçenekleri boş", "warning")
                        return False, "Uygulama merkezi seçenekleri boş"
                        
                except:
                    # Panel açılmadı - muhtemelen disabled
                    self.log("❌ Uygulama merkezi dropdown açılamadı", "warning")
                    return False, "Uygulama merkezi seçilemiyor"
                    
        except Exception as e:
            self.log(f"Uygulama merkezi kontrolü hatası: {e}", "error")
        
        # Fallback: Devam butonu aktif mi kontrol et
        try:
            continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-brand-orange")
            if continue_btn.is_enabled() and "disabled" not in continue_btn.get_attribute("class"):
                self.log("✅ RANDEVU MEVCUT OLABİLİR! Devam butonu aktif.", "success")
                return True, "Devam butonu aktif"
        except:
            pass
        
        return False, "Randevu bulunamadı"
    
    def run_full_check(self, otp_callback=None) -> tuple[bool, str]:
        """Tam kontrol döngüsü"""
        try:
            self.start()
            
            # 1. Login
            if not self.login():
                return False, "Login başarısız"
            
            # 2. OTP
            if otp_callback:
                otp_code = otp_callback()
            else:
                otp_code = input("SMS'ten gelen OTP kodunu girin: ")
            
            if not self.enter_otp(otp_code):
                return False, "OTP doğrulama başarısız"
            
            # 3. Dashboard
            if not self.complete_dashboard_checkboxes():
                return False, "Dashboard adımı başarısız"
            
            # 4. Form
            if not self.fill_applicant_details():
                return False, "Form doldurma başarısız"
            
            # 5. Kategori
            if not self.select_appointment_category():
                return False, "Kategori seçimi başarısız"
            
            # 6. Müsaitlik
            return self.check_availability()
            
        except Exception as e:
            self.log(f"Hata: {e}", "error")
            return False, str(e)
        
        finally:
            self.stop()


if __name__ == "__main__":
    bot = AppointmentBot()
    available, message = bot.run_full_check()
    print(f"\nSonuç: {'RANDEVU VAR!' if available else 'Randevu yok'}")
    print(f"Mesaj: {message}")
