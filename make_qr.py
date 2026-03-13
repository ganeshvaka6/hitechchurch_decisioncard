
import os
import qrcode
from pathlib import Path

# 1. Try to use Render's automatic URL
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# 2. Otherwise use APP_BASE_URL (env override)
APP_BASE_URL = os.getenv("APP_BASE_URL")

# 3. Local fallback
DEFAULT_LOCAL = "http://127.0.0.1:5000"

# Decide final base URL (same logic as your backend)
BASE_URL = (RENDER_EXTERNAL_URL or APP_BASE_URL or DEFAULT_LOCAL).rstrip("/")

# Your form is at "/"
endpoint = "/"
full_url = f"{BASE_URL}{endpoint}"

print("Using BASE_URL:", BASE_URL)
print("Generating QR for:", full_url)

# Save into /static so your backend can serve it
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

output_file = static_dir / "permanent_qr.png"

qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(full_url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save(output_file)

print(f"✅ QR Code saved to: {output_file.resolve()}")
