import os
import json
import time
import datetime
import requests
from flask import Flask, render_template, request, jsonify
import config

app = Flask(__name__)

# Cooldown storage: {ip_address: timestamp}
ip_cooldowns = {}

# ───────────────────────────────────────────────
# EVENT TIME HELPERS
# ───────────────────────────────────────────────
def get_event_target():
    try:
        return datetime.datetime.strptime(config.EVENT_END_TIME, "%Y-%m-%d %H:%M:%S")
    except Exception:
        # Fallback to 72 hours from now
        return datetime.datetime.now() + datetime.timedelta(days=3)

def is_event_active():
    target = get_event_target()
    return datetime.datetime.now() < target

def get_event_seconds_remaining():
    target = get_event_target()
    delta = target - datetime.datetime.now()
    return max(0, int(delta.total_seconds()))


def sanitize_public_message(msg: str) -> str:
    if not msg:
        return "Server rejected request."
    return msg.replace("GTC", "JOYST").replace("gtc", "joyst").replace("gtccheats.xyz", "gateway")


# ───────────────────────────────────────────────
# DATABASE HELPERS
# ───────────────────────────────────────────────
def load_uids():
    if not os.path.exists(config.UIDS_FILE):
        return {}
    try:
        with open(config.UIDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {config.UIDS_FILE}: {e}")
        return {}

def save_uids(data):
    try:
        with open(config.UIDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {config.UIDS_FILE}: {e}")

def cleanup_expired_uids():
    uids_data = load_uids()
    if not uids_data:
        return
    now = datetime.datetime.now()
    updated = False
    for uid in list(uids_data.keys()):
        item = uids_data[uid]
        expiry_str = item.get("expiry_time")
        if not expiry_str:
            continue
        try:
            expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if now >= expiry_dt:
                del uids_data[uid]
                updated = True
        except Exception:
            pass
    if updated:
        save_uids(uids_data)

def check_ip_cooldown(ip: str):
    now = time.time()
    last_time = ip_cooldowns.get(ip, 0)
    elapsed = now - last_time
    if elapsed < config.COOLDOWN_SECONDS:
        return int(config.COOLDOWN_SECONDS - elapsed)
    return 0

def set_ip_cooldown(ip: str):
    ip_cooldowns[ip] = time.time()

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or "127.0.0.1"


# ───────────────────────────────────────────────
# WEB ROUTES
# ───────────────────────────────────────────────
@app.route('/')
def index():
    cleanup_expired_uids()
    event_active = is_event_active()
    rem_seconds = get_event_seconds_remaining()
    
    return render_template(
        'index.html',
        brand_name=config.BRAND_NAME,
        service_name=config.SERVICE_NAME,
        logo_url=config.LOGO_URL,
        event_active=event_active,
        event_end_time=config.EVENT_END_TIME,
        event_rem_seconds=rem_seconds,
        discord_url=config.DISCORD_URL
    )


@app.route('/api/event-status', methods=['GET'])
def api_event_status():
    active = is_event_active()
    rem = get_event_seconds_remaining()
    return jsonify({
        "active": active,
        "ended": not active,
        "remaining_seconds": rem,
        "end_time": config.EVENT_END_TIME,
        "discord_url": config.DISCORD_URL
    })


@app.route('/api/whitelist', methods=['POST'])
def api_whitelist():
    cleanup_expired_uids()
    client_ip = get_client_ip()

    # 1. 3-DAY AUTOMATIC HARD CUTOFF CHECK
    if not is_event_active():
        return jsonify({
            "success": False,
            "event_ended": True,
            "message": "Free UID bypass trial has ended. To purchase access, please create a ticket in our Discord server."
        }), 403

    # 2. Cooldown check
    cooldown = check_ip_cooldown(client_ip)
    if cooldown > 0:
        return jsonify({
            "success": False,
            "message": f"Please wait {cooldown}s before submitting again."
        }), 429

    data = request.get_json(silent=True) or {}
    raw_uid = str(data.get("uid", "")).strip().replace('"', '').replace("'", "")

    # 3. Validation: Numbers only
    if not raw_uid.isdigit():
        return jsonify({
            "success": False,
            "message": "UID must contain numbers only."
        }), 400

    # 4. Validation: Length > 6
    if len(raw_uid) <= 6:
        return jsonify({
            "success": False,
            "message": "UID must be at least 7 digits."
        }), 400

    set_ip_cooldown(client_ip)

    # 5. Verify API Key is configured in environment
    if not config.API_KEY:
        return jsonify({
            "success": False,
            "message": "Gateway API Key is not configured in server environment."
        }), 500

    # 6. Call external API (Live server check)
    headers = {
        'X-API-KEY': config.API_KEY,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) JOYST/1.0'
    }
    payload = {
        'account_id': raw_uid,
        'for_days': 1
    }

    try:
        response = requests.post(
            f"{config.API_URL}?action=add",
            json=payload,
            headers=headers,
            timeout=12
        )

        try:
            res_json = response.json()
        except Exception:
            res_json = None

        if response.status_code == 409 or (res_json and "already active" in str(res_json.get("message", "")).lower()):
            return jsonify({
                "success": False,
                "message": "This UID is already active on the bypass network."
            }), 409

        if res_json and res_json.get('success'):
            now = datetime.datetime.now()
            added_time = now.strftime('%Y-%m-%d %H:%M:%S')
            expiry_dt = now + datetime.timedelta(days=1)
            expiry_time = expiry_dt.strftime('%Y-%m-%d %H:%M:%S')

            # Save in local database
            uids_data = load_uids()
            uids_data[raw_uid] = {
                "uid": raw_uid,
                "added_time": added_time,
                "expiry_time": expiry_time,
                "days": 1,
                "ip": client_ip,
                "status": "Active"
            }
            save_uids(uids_data)

            return jsonify({
                "success": True,
                "message": "UID whitelisted successfully for 24 hours.",
                "data": {
                    "uid": raw_uid,
                    "added_time": added_time,
                    "expiry_time": expiry_time,
                    "duration": "24 Hours",
                    "status": "Active"
                }
            }), 200
        else:
            raw_err = res_json.get('message', 'Server rejected request.') if res_json else f"Server error ({response.status_code})"
            return jsonify({
                "success": False,
                "message": sanitize_public_message(raw_err)
            }), 400

    except requests.RequestException as e:
        print(f"API Error: {e}")
        return jsonify({
            "success": False,
            "message": "Unable to connect to gateway. Please try again."
        }), 502


@app.route('/api/status/<uid>', methods=['GET'])
def api_status(uid):
    cleanup_expired_uids()
    clean_uid = str(uid).strip().replace('"', '').replace("'", "")

    if not clean_uid.isdigit():
        return jsonify({
            "success": False,
            "message": "UID must be numeric."
        }), 400

    # 1. LIVE API QUERY FIRST (Real-time check)
    headers = {
        'X-API-KEY': config.API_KEY,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) JOYST/1.0'
    }

    if config.API_KEY:
        try:
            r = requests.get(
                f"{config.API_URL}?action=info&account_id={clean_uid}",
                headers=headers,
                timeout=8
            )
            res_json = r.json() if r.status_code in (200, 400, 403, 404) else None

            # If API explicitly says not success
            if res_json and not res_json.get("success"):
                err_msg = str(res_json.get("message", ""))
                if "not found" in err_msg.lower():
                    clean_msg = "No active whitelist found for this UID. It may have been removed or expired."
                elif "another admin" in err_msg.lower():
                    clean_msg = "This UID is registered under another license."
                else:
                    clean_msg = sanitize_public_message(err_msg)
                
                uids_data = load_uids()
                if clean_uid in uids_data:
                    del uids_data[clean_uid]
                    save_uids(uids_data)
                return jsonify({
                    "success": False,
                    "message": clean_msg
                }), 404

            # If API says success: True
            if res_json and res_json.get("success") and "data" in res_json:
                api_data = res_json["data"]
                expiry_str = api_data.get("expiry_date")
                added_str = api_data.get("added_on", "N/A")

                # Compute remaining seconds from expiry_date if available
                remaining_seconds = 86400
                now = datetime.datetime.now()
                if expiry_str:
                    try:
                        expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                        remaining_seconds = max(0, int((expiry_dt - now).total_seconds()))
                    except Exception:
                        pass

                hours = remaining_seconds // 3600
                minutes = (remaining_seconds % 3600) // 60
                seconds = remaining_seconds % 60

                return jsonify({
                    "success": True,
                    "data": {
                        "uid": clean_uid,
                        "status": "Active",
                        "added_time": added_str,
                        "expiry_time": expiry_str or "24 Hours from activation",
                        "remaining_seconds": remaining_seconds,
                        "remaining_formatted": f"{hours}h {minutes}m {seconds}s",
                        "progress_percent": max(0, min(100, int((remaining_seconds / 86400) * 100)))
                    }
                }), 200

        except Exception as e:
            print(f"Live API status query error: {e}")

    # 2. Fallback to local database if remote gateway is unreachable
    uids_data = load_uids()
    now = datetime.datetime.now()

    if clean_uid in uids_data:
        info = uids_data[clean_uid]
        expiry_str = info.get("expiry_time")
        try:
            expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            remaining_seconds = int((expiry_dt - now).total_seconds())
        except Exception:
            remaining_seconds = 0

        if remaining_seconds > 0:
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            seconds = remaining_seconds % 60
            return jsonify({
                "success": True,
                "data": {
                    "uid": clean_uid,
                    "status": "Active",
                    "added_time": info.get("added_time"),
                    "expiry_time": expiry_str,
                    "remaining_seconds": remaining_seconds,
                    "remaining_formatted": f"{hours}h {minutes}m {seconds}s",
                    "progress_percent": max(0, min(100, int((remaining_seconds / 86400) * 100)))
                }
            })

    return jsonify({
        "success": False,
        "message": "No active whitelist found for this UID."
    }), 404


if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
