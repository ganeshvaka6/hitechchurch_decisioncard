
import os
import re
import json
from datetime import datetime, timezone, timedelta
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_file

import gspread
from google.oauth2.service_account import Credentials
from twilio.rest import Client
import qrcode

# ---------------- ENV VARIABLES ----------------
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
TWILIO_TEMPLATE_SID = os.getenv("TWILIO_TEMPLATE_SID")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

app = Flask(__name__)

# ------------ (A) RENDER FIX: AUTO-SET APP_BASE_URL ------------
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
if RENDER_EXTERNAL_URL:
    APP_BASE_URL = RENDER_EXTERNAL_URL
# ---------------------------------------------------------------

# ---------------- GOOGLE SHEETS ----------------
def get_sheet():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(GOOGLE_SHEET_KEY)
    ws = sh.sheet1

    values = ws.get_all_values()
    if not values:
        ws.append_row([
            "Submission Timestamp",
            "Form Date",
            "First Name",
            "Last Name",
            "Phone",
            "Heard About",
            "Connection Options",
            "Spiritual Decision",
            "Current Location",
            "Native Place",
            "Appointment Date",
            "Appointment Time",
            "Prayer Request",
        ])
    return ws

# ---------------- HELPERS ----------------
def format_wa_number(number: str) -> str:
    raw = number or ""
    s = re.sub(r"\D+", "", raw)
    if raw.strip().startswith('+') and len(s) >= 8:
        return f"whatsapp:+{s}"
    if s.startswith('91') and len(s) == 12:
        return f"whatsapp:+{s}"
    if len(s) == 10:
        return f"whatsapp:+91{s}"
    if 8 <= len(s) <= 15:
        return f"whatsapp:+{s}"
    return f"whatsapp:+{s}"

# ---------------- WHATSAPP ----------------
def send_whatsapp_confirmation(first_name: str, appt_date: str, appt_time: str, mobile: str):
    if not (TWILIO_SID and TWILIO_AUTH and TWILIO_WHATSAPP_FROM and TWILIO_TEMPLATE_SID):
        print("[WA] Missing Twilio env vars")
        return None
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        to = format_wa_number(mobile)
        payload = {
            'from_': TWILIO_WHATSAPP_FROM,
            'to': to,
            'content_sid': TWILIO_TEMPLATE_SID,
            'content_variables': json.dumps({
                "1": first_name,
                "2": appt_date,
                "3": appt_time,
            })
        }
        msg = client.messages.create(**payload)
        print("[WA] SENT:", msg.sid)
        return msg.sid
    except Exception as e:
        print("[WA] Error:", e)
        return None

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(tz=ist).strftime('%Y-%m-%d')
    return render_template('form.html', current_date=today)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json(force=True) or {}
    first = (data.get('first_name') or '').strip()
    last = (data.get('last_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    heard = (data.get('heard_about') or '').strip()
    connect = ", ".join(data.get('connect_options') or [])
    spiritual = ", ".join(data.get('spiritual_decision') or [])
    current_loc = (data.get('current_location') or '').strip()
    native_place = (data.get('native_place') or '').strip()
    appt_date = (data.get('appointment_date') or '').strip()
    appt_time = (data.get('appointment_time') or '').strip()
    prayer = (data.get('prayer_request') or '').strip()

    if not first or not phone:
        return jsonify({'ok': False, 'message': 'First name and phone are required.'}), 400

    ws = get_sheet()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    ws.append_row([
        ts,
        appt_date,
        first,
        last,
        phone,
        heard,
        connect,
        spiritual,
        current_loc,
        native_place,
        appt_date,
        appt_time,
        prayer,
    ])

    send_whatsapp_confirmation(first, appt_date, appt_time, phone)

    return jsonify({'ok': True, 'message': 'Thank you! Your registration is received. A WhatsApp confirmation has been sent.'})


@app.route('/qr')
def qr():
    url = (APP_BASE_URL or '').strip() or request.host_url.rstrip('/')
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


# ------------ (B) HTML Friendly Submit Route (SAFE ADDITION) ------------
@app.route('/submit-form', methods=['POST'])
def submit_form():
    """
    Allows <form> HTML POST submissions and forwards them into the JSON API.
    Does NOT disturb existing code.
    """
    form_data = request.form.to_dict(flat=True)

    form_data["connect_options"] = request.form.getlist("connect_options")
    form_data["spiritual_decision"] = request.form.getlist("spiritual_decision")

    # Reuse your existing JSON submit function
    with app.test_request_context(json=form_data):
        return submit()
# -------------------------------------------------------------------------


@app.route('/health')
def health():
    return jsonify({'ok': True}), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
