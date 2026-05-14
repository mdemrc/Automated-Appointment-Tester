"""
Form Doldurucu - Tarayıcıdaki formu doldurur
Undetected Chrome ile çalışır
"""

import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FormFiller:
    def __init__(self):
        self.driver = None
    
    def start_browser(self) -> bool:
        """Undetected Chrome başlat"""
        print(f"   🔄 Undetected Chrome başlatılıyor...")
        
        try:
            options = uc.ChromeOptions()
            options.add_argument("--lang=tr-TR")
            options.add_argument("--window-size=1366,768")
            
            # Profile dizini (cookie'ler kalıcı olsun)
            profile_dir = os.path.join(os.path.dirname(__file__), "chrome_profile")
            options.add_argument(f"--user-data-dir={profile_dir}")
            
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self.driver.implicitly_wait(10)
            
            print(f"✅ Tarayıcı başlatıldı!")
            return True
            
        except Exception as e:
            print(f"❌ Tarayıcı başlatılamadı: {e}")
            return False
    
    def go_to_target(self):
        """Open the configured target login page."""
        import os
        url = os.environ.get("TARGET_LOGIN_URL", "https://example.com/login")
        print(f"   Navigating to {url}")
        self.driver.get(url)
        time.sleep(3)
    
    def disconnect(self):
        """Bağlantıyı kapat (tarayıcıyı kapatmaz)"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _select_mat_option(self, select_element, option_text: str) -> bool:
        """Angular Material mat-select için seçim yap"""
        try:
            self.driver.execute_script("arguments[0].click();", select_element)
            time.sleep(0.5)
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.mat-mdc-select-panel"))
            )
            
            options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
            for option in options:
                if option_text.lower() in option.text.lower():
                    self.driver.execute_script("arguments[0].click();", option)
                    time.sleep(0.3)
                    return True
            
            # Escape ile kapat
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            return False
            
        except Exception as e:
            print(f"⚠️ Dropdown seçim hatası: {e}")
            return False
    
    def fill_your_details(self, user_info: dict) -> bool:
        """'Detaylarınız' (your-details) sayfasını doldur"""
        print("\n📝 'Detaylarınız' formu dolduruluyor...")
        
        try:
            # Sayfa kontrolü
            if "your-details" not in self.driver.current_url:
                print(f"⚠️ Yanlış sayfa! Şu anki: {self.driver.current_url}")
                print("   'your-details' sayfasında olmalısınız")
                return False
            
            time.sleep(1)
            
            # İsim (mat-input-4)
            print("  → İsim giriliyor...")
            first_name = self.driver.find_element(By.ID, "mat-input-4")
            first_name.clear()
            first_name.send_keys(user_info["first_name"])
            
            # Soyisim (mat-input-5)
            print("  → Soyisim giriliyor...")
            last_name = self.driver.find_element(By.ID, "mat-input-5")
            last_name.clear()
            last_name.send_keys(user_info["last_name"])
            
            time.sleep(0.5)
            
            # Cinsiyet (mat-select-0)
            print("  → Cinsiyet seçiliyor...")
            gender_select = self.driver.find_element(By.ID, "mat-select-0")
            self._select_mat_option(gender_select, user_info["gender"])
            
            time.sleep(0.5)
            
            # Uyruk (mat-select-1)
            print("  → Uyruk seçiliyor...")
            nationality_select = self.driver.find_element(By.ID, "mat-select-1")
            self._select_mat_option(nationality_select, user_info["nationality"])
            
            time.sleep(0.5)
            
            # Pasaport numarası (mat-input-6)
            print("  → Pasaport numarası giriliyor...")
            passport = self.driver.find_element(By.ID, "mat-input-6")
            passport.clear()
            passport.send_keys(user_info["passport_no"])
            
            # Pasaport geçerlilik tarihi varsa
            if "passport_expiry" in user_info:
                print("  → Pasaport geçerlilik tarihi giriliyor...")
                try:
                    # Tarih input'unu bul (genellikle mat-input-7 veya datepicker)
                    expiry_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                        "input[formcontrolname*='expiry'], input[formcontrolname*='validity'], input[placeholder*='tarih']")
                    
                    if expiry_inputs:
                        expiry_inputs[0].clear()
                        expiry_inputs[0].send_keys(user_info["passport_expiry"])
                    else:
                        # mat-input-7 dene
                        try:
                            expiry = self.driver.find_element(By.ID, "mat-input-7")
                            expiry.clear()
                            expiry.send_keys(user_info["passport_expiry"])
                        except:
                            print("  ⚠️ Pasaport geçerlilik alanı bulunamadı")
                except:
                    pass
            
            # Telefon kodu
            print("  → Telefon kodu giriliyor...")
            try:
                phone_code = self.driver.find_element(By.ID, "mat-input-7")
                phone_code.clear()
                phone_code.send_keys(user_info["phone_code"])
            except:
                try:
                    phone_code = self.driver.find_element(By.ID, "mat-input-8")
                    phone_code.clear()
                    phone_code.send_keys(user_info["phone_code"])
                except:
                    print("  ⚠️ Telefon kodu alanı bulunamadı")
            
            # Telefon numarası
            print("  → Telefon numarası giriliyor...")
            try:
                phone = self.driver.find_element(By.ID, "mat-input-8")
                phone.clear()
                phone.send_keys(user_info["phone_number"])
            except:
                try:
                    phone = self.driver.find_element(By.ID, "mat-input-9")
                    phone.clear()
                    phone.send_keys(user_info["phone_number"])
                except:
                    print("  ⚠️ Telefon numarası alanı bulunamadı")
            
            # Email
            print("  → E-posta giriliyor...")
            try:
                email = self.driver.find_element(By.ID, "mat-input-9")
                email.clear()
                email.send_keys(user_info["email"])
            except:
                try:
                    email = self.driver.find_element(By.ID, "mat-input-10")
                    email.clear()
                    email.send_keys(user_info["email"])
                except:
                    print("  ⚠️ E-posta alanı bulunamadı")
            
            print("\n✅ Form dolduruldu!")
            print("⚠️ Lütfen bilgileri kontrol edip 'Kaydet' butonuna tıklayın")
            return True
            
        except Exception as e:
            print(f"❌ Form doldurma hatası: {e}")
            return False
    
    def fill_application_details(self, appointment_info: dict) -> bool:
        """'Başvuru Detayları' (applicationdetails) sayfasını doldur"""
        print("\n📝 'Başvuru Detayları' formu dolduruluyor...")
        
        try:
            if "applicationdetails" not in self.driver.current_url:
                print(f"⚠️ Yanlış sayfa! Şu anki: {self.driver.current_url}")
                print("   'applicationdetails' sayfasında olmalısınız")
                return False
            
            time.sleep(1)
            
            mat_selects = self.driver.find_elements(By.CSS_SELECTOR, "mat-select")
            
            if len(mat_selects) >= 2:
                # Kategori
                print(f"  → Kategori seçiliyor: {appointment_info['category']}")
                self._select_mat_option(mat_selects[0], appointment_info["category"])
                time.sleep(1)
                
                # Alt kategori
                print(f"  → Alt kategori seçiliyor: {appointment_info['subcategory']}")
                mat_selects = self.driver.find_elements(By.CSS_SELECTOR, "mat-select")
                if len(mat_selects) >= 2:
                    self._select_mat_option(mat_selects[1], appointment_info["subcategory"])
                
                print("\n✅ Kategori seçildi!")
                print("🔍 Uygulama merkezi dropdown'unu kontrol edin")
                return True
            else:
                print("❌ Dropdown'lar bulunamadı")
                return False
                
        except Exception as e:
            print(f"❌ Hata: {e}")
            return False
    
    def enter_otp(self, otp_code: str) -> bool:
        """OTP kodunu gir"""
        print(f"\n🔢 OTP giriliyor: {otp_code}")
        
        try:
            # OTP input'u bul
            otp_input = None
            
            selectors = [
                (By.ID, "otp"),
                (By.NAME, "otp"),
                (By.CSS_SELECTOR, "input[type='tel']"),
                (By.CSS_SELECTOR, "input[formcontrolname='otp']"),
                (By.CSS_SELECTOR, "input.otp-input"),
            ]
            
            for by, selector in selectors:
                try:
                    otp_input = self.driver.find_element(by, selector)
                    if otp_input:
                        break
                except:
                    continue
            
            if otp_input:
                otp_input.clear()
                otp_input.send_keys(otp_code)
                print("✅ OTP girildi!")
                return True
            else:
                print("❌ OTP input alanı bulunamadı")
                return False
                
        except Exception as e:
            print(f"❌ OTP girme hatası: {e}")
            return False


if __name__ == "__main__":
    from config import USER_INFO, CHROME_DEBUG_PORT
    
    filler = FormFiller(CHROME_DEBUG_PORT)
    
    if filler.connect_to_browser():
        filler.fill_your_details(USER_INFO)
