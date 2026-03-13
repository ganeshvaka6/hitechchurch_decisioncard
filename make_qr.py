
# generate_qr.py
import os
import qrcode
from pathlib import Path

# Set this in your environment for production; falls back to localhost for local testing
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")

# If your form is at '/', keep endpoint="/"
# If you later move it to '/form', just change endpoint to "/form"
endpoint = "/"

full_url = f"{APP_BASE_URL.rstrip('/')}{endpoint}"

print("Using APP_BASE_URL:", APP_BASE_URL)
print("Generating QR for: ", full_url)

# Ensure /static exists
static_dir = Path("static")
static_dir.mkdir(parents=True, exist_ok=True)

# Create QR
qr = qrcode.QRCode(
    version=1,      # 1=smallest; increase if your URL is very long
    box_size=10,    # pixel size of each box
    border=4        # border boxes (quiet zone)
)
qr.add_data(full_url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")

# Save permanent asset
out_path = static_dir / "permanent_qr.png"
img.save(out_path)

print(f"✅ Saved permanent QR to: {out_path.resolve()}")
print("Tip: You can serve it at /static/permanent_qr.png")
