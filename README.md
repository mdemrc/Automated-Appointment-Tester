# Automated Appointment Tester

A Python-based browser-automation harness used to stress-test the reliability of public appointment-booking web interfaces. The project pairs a Selenium-driven desktop client with a small Flask server that exposes a one-time-password (OTP) relay endpoint, useful when the target form requires a code delivered to a mobile device.

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)](https://www.python.org)
[![Selenium](https://img.shields.io/badge/Selenium-WebDriver-43B02A?logo=selenium)](https://www.selenium.dev)
[![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask)](https://flask.palletsprojects.com)
[![Use](https://img.shields.io/badge/Use-Educational%20%2F%20Testing-blue)](#license)

> ⓘ **Disclaimer.** The project is published strictly as an *educational, defensive-testing* artefact. It demonstrates how to programmatically interact with a real-world web form — handling dynamic DOM, slow networks, captchas, and OTP flows — so that the owner of such a form can use the same scripts to test the robustness of their own interface. The repository ships without any credentials, target URLs, or production configuration.
>
> ⓘ **Bildirim.** Proje, yalnızca *eğitim ve savunmacı test amaçlı* bir nesne olarak yayımlanmıştır. Yöneticisinin kendi formunun dayanıklılığını test etmek için kullanabileceği şekilde; dinamik DOM, yavaş ağlar, CAPTCHA ve OTP akışlarıyla etkileşim tekniklerini gösterir. Repo; herhangi bir kimlik bilgisi, hedef URL veya üretim yapılandırması içermez.

---

## English

### ◆ Overview

The repository is a layered automation rig:

| Layer | Path | Role |
|---|---|---|
| ▣ Driver | `main.py`, `appointment_bot.py` | Boots Selenium / undetected-chromedriver, walks through the form |
| ▣ Notifications | `notifications.py`, `telegram_otp.py` | Pushes events to a Telegram chat for visibility |
| ▣ OTP relay | `otp_server.py`, `otp_watch.py`, `remote_otp_client.py` | Local + remote OTP forwarding |
| ▣ Semi-automatic | `semi_auto/` | Operator-in-the-loop variant for harder forms |
| ▣ Ubuntu server | `ubuntu_server/` | Standalone Flask API for cloud OTP relay |

### ⚡ Key Capabilities

- ► Reliable navigation through SPA-style forms with explicit and implicit waits
- ► Robust element resolution with retries, exponential backoff, and screenshot capture on failure
- ► OTP relay via Telegram and a self-hosted Flask endpoint (no third-party paid service required)
- ► Headless and headed modes for desktop and Ubuntu-server deployments
- ► Centralised, file-based configuration; no secrets baked into source

### ▣ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Browser automation | Selenium WebDriver, undetected-chromedriver |
| Web API | Flask |
| Scheduling | `schedule` module |
| Messaging | Telegram Bot API |

### ▦ Architecture

```
┌────────────────────┐         ┌─────────────────────┐
│  Mobile relay      │  HTTPS  │  Flask OTP API      │
│  (Tasker / app)    │ ──────▶ │  (ubuntu_server/)   │
└────────────────────┘         └──────────┬──────────┘
                                          │ X-API-Key
                                          ▼
┌────────────────────┐         ┌─────────────────────┐
│  Selenium driver   │  poll   │  remote_otp_client  │
│  main.py / appt_bot│ ──────▶ │  otp_watch          │
└────────┬───────────┘         └─────────────────────┘
         │                                  │
         ▼                                  ▼
   Target site form               Telegram bot (events)
```

### ▶ Getting Started

```bash
python -m venv venv
.\venv\Scripts\activate          # or: source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py    # fill in non-sensitive test parameters
python main.py
```

For the Ubuntu OTP server:

```bash
cd ubuntu_server
pip install -r requirements.txt
OTP_API_KEY=$(openssl rand -hex 16) python app.py
```

### ⓘ Operational Notes

- ► The repository does not include `chrome_profile/`, `venv/`, or any captured screenshots / logs; these are gitignored
- ► All sensitive runtime parameters (target URL, credentials, Telegram token, OTP API key) are expected to live outside the repository in a local `.env` or `config.py`

---

## Türkçe

### ◆ Genel Bakış

Repo, katmanlı bir otomasyon iskelesidir:

| Katman | Yol | Rolü |
|---|---|---|
| ▣ Sürücü | `main.py`, `appointment_bot.py` | Selenium / undetected-chromedriver'ı başlatır, form üzerinde gezinir |
| ▣ Bildirimler | `notifications.py`, `telegram_otp.py` | Görünürlük için Telegram sohbetine olay gönderir |
| ▣ OTP rölesi | `otp_server.py`, `otp_watch.py`, `remote_otp_client.py` | Yerel ve uzak OTP iletimi |
| ▣ Yarı otomatik | `semi_auto/` | Operatör-döngüde varyant — zorlu formlar için |
| ▣ Ubuntu sunucu | `ubuntu_server/` | Bulut OTP rölesi için bağımsız Flask API |

### ⚡ Öne Çıkan Yetenekler

- ► Açık ve örtük beklemelerle SPA tarzı formlarda güvenilir gezinme
- ► Yeniden deneme, üstel geri çekilme ve hata durumunda ekran görüntüsü ile sağlam eleman çözümü
- ► Telegram ve kendi sunucusunda barındırılan bir Flask uç noktası üzerinden OTP iletimi (üçüncü taraf ücretli servis gerekmez)
- ► Masaüstü ve Ubuntu sunucu konuşlandırmaları için headless ve görünür modlar
- ► Merkezi, dosya tabanlı yapılandırma; kaynak içinde sır barındırmaz

### ▶ Kurulum

```bash
python -m venv venv
.\venv\Scripts\activate          # veya: source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
python main.py
```

Ubuntu OTP sunucusu için:

```bash
cd ubuntu_server
pip install -r requirements.txt
OTP_API_KEY=$(openssl rand -hex 16) python app.py
```

### ⓘ Operasyonel Notlar

- ► Repo; `chrome_profile/`, `venv/` veya yakalanmış ekran görüntüleri/logları içermez; bunlar gitignore'lanmıştır
- ► Tüm hassas çalışma parametreleri (hedef URL, kimlik bilgileri, Telegram token, OTP API anahtarı) repo dışında bir yerde (yerel `.env` veya `config.py`) bulunmalıdır

---

## License

Released for educational and defensive testing purposes only.
