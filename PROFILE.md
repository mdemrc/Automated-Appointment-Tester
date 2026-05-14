# Automated Appointment Tester — Project Description

## English

Automated Appointment Tester is a Python-based browser-automation harness used to stress-test the reliability of public appointment-booking web interfaces. It pairs a Selenium-driven desktop client with a small Flask server that exposes a one-time-password (OTP) relay endpoint — useful when the target form requires a code that is normally delivered to a mobile device — and a Telegram bot layer that streams visibility events to the operator.

Technically the project is a layered automation rig: a driver layer built on Selenium and undetected-chromedriver, a notifications layer that pushes events to Telegram, an OTP relay layer composed of a local watcher and a remote client speaking to a Flask API, a semi-automatic variant for forms that require an operator in the loop, and a standalone Ubuntu-server flavour that can be deployed independently. Reliability comes from explicit and implicit waits, retries with exponential backoff, screenshot capture on failure, and centralised file-based configuration that keeps secrets out of source.

The project is published strictly as an educational, defensive-testing artefact: the owner of such a form can use the same scripts to verify the robustness of their own interface. The repository ships without any credentials, target URLs, or production configuration, and every sensitive runtime parameter is expected to live outside the codebase. The interesting engineering lessons here are about resilient DOM walking, OTP plumbing, and how to keep a long-running browser automation script honest in the face of slow networks and shifting markup.

## Türkçe

Automated Appointment Tester; Python tabanlı, herkese açık randevu alma web arayüzlerinin güvenilirliğini stres testi etmek için kullanılan bir tarayıcı otomasyon iskelesidir. Selenium tabanlı bir masaüstü istemcisini; normalde mobil cihaza iletilen bir tek kullanımlık şifreyi (OTP) röleleyen küçük bir Flask sunucusu ve operatöre görünürlük olaylarını yayınlayan bir Telegram bot katmanı ile birleştirir.

Teknik olarak proje katmanlı bir otomasyon iskelesidir: Selenium ve undetected-chromedriver üzerine inşa edilmiş bir sürücü katmanı, olayları Telegram'a yayınlayan bir bildirim katmanı, yerel bir izleyici ve Flask API ile konuşan uzak istemciden oluşan bir OTP röle katmanı, operatörü döngüde gerektiren formlar için yarı otomatik bir varyant ve bağımsız olarak konuşlandırılabilen ayrı bir Ubuntu sunucu sürümü. Güvenilirlik; açık ve örtük beklemelerden, üstel geri çekilmeli yeniden denemelerden, hata durumunda ekran görüntüsü yakalamadan ve sırları kaynak dışında tutan merkezi dosya tabanlı bir yapılandırmadan gelir.

Proje, yalnızca eğitim ve savunmacı test amaçlı bir nesne olarak yayımlanmıştır: böyle bir formun sahibi, kendi arayüzünün dayanıklılığını doğrulamak için aynı betikleri kullanabilir. Repo; kimlik bilgisi, hedef URL veya üretim yapılandırması içermez ve tüm hassas çalışma parametrelerinin kod tabanı dışında yaşaması beklenir. Buradaki ilginç mühendislik dersleri; dayanıklı DOM gezinmesi, OTP boru hattı ve yavaş ağlar ile değişen markup karşısında uzun süreli bir tarayıcı otomasyon betiğinin nasıl dürüst tutulacağı üzerinedir.
