import os

# ==========================================
#         JOYST CORPORATION - CONFIG
# ==========================================

# API Configuration (Loaded securely from Environment Variables)
API_URL = os.getenv("API_URL", "https://gtccheats.xyz/Api/uidbypassapi/api_user.php")
API_KEY = os.getenv("API_KEY", "")

# Local Storage Database
UIDS_FILE = os.getenv("UIDS_FILE", "uids.json")

# Web Server Settings
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1")

# Cooldown time in seconds between requests per IP
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", 3))

# Branding Assets
BRAND_NAME   = os.getenv("BRAND_NAME", "JOYST CORPORATION")
SERVICE_NAME = os.getenv("SERVICE_NAME", "Free UID Bypass")
LOGO_URL     = os.getenv("LOGO_URL", "")
