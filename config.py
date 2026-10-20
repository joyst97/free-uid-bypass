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

# 3-Day Free Trial Event Deadline (Format: YYYY-MM-DD HH:MM:SS)
EVENT_END_TIME = os.getenv("EVENT_END_TIME", "2026-10-23 23:59:59")

# Discord Invite Link for Tickets / Purchase
DISCORD_URL = os.getenv("DISCORD_URL", "https://discord.gg/BwU4eESvEZ")

# Branding Assets
BRAND_NAME   = os.getenv("BRAND_NAME", "JOYST CORPORATION")
SERVICE_NAME = os.getenv("SERVICE_NAME", "Free UID Bypass")
LOGO_URL     = os.getenv("LOGO_URL", "")
