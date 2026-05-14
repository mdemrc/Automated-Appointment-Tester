"""
Semi-automated appointment assistant - configuration template.
Copy this file to `config.local.py` and fill it in for local testing.
The repository must NEVER contain real personal data.
"""

import os

USER_INFO = {
    "first_name": os.environ.get("APPT_FIRST_NAME", "FIRSTNAME"),
    "last_name": os.environ.get("APPT_LAST_NAME", "LASTNAME"),
    "gender": "Erkek",
    "nationality": "Country",
    "passport_no": os.environ.get("APPT_PASSPORT_NO", "X00000000"),
    "passport_expiry": os.environ.get("APPT_PASSPORT_EXP", "01/01/2030"),
    "phone_code": "00",
    "phone_number": os.environ.get("APPT_PHONE", "0000000000"),
    "email": os.environ.get("APPT_EMAIL", "user@example.com"),
}

APPOINTMENT_INFO = {
    "category": os.environ.get("APPT_CATEGORY", "1 - Category"),
    "subcategory": os.environ.get("APPT_SUBCATEGORY", "Subcategory"),
}

OTP_SERVER = {
    "url": os.environ.get("OTP_SERVER_URL", "http://localhost:5000"),
    "api_key": os.environ.get("OTP_API_KEY", ""),
    "check_interval": 2,
}

CHROME_DEBUG_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))
