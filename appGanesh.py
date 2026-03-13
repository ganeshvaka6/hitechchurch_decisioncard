
import os
from flask import Flask, render_template, request, redirect, url_for, flash

# --- Configuration ---
# Set SECRET_KEY for flashing messages (you can also set via environment variable)
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = SECRET_KEY


# ---- Routes ----
@app.route("/")
def index():
    """
    Home route – renders the decision card form.
    """
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    """
    Handles form submission.
    Replace with DB/email integration as needed.
    """
    # Extract fields from the form (make sure names match inputs in form.html)
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    city = request.form.get("city", "").strip()
    decision = request.form.get("decision", "").strip()
    prayer = request.form.get("prayer", "").strip()

    # Basic server-side validation
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("index"))

    # TODO: Persist data (DB/Sheet) or send email
    # For now, just log to server console
    app.logger.info("New Decision Card: %s | %s | %s | %s | %s | %s",
                    name, phone, email, city, decision, prayer)

    # Redirect to a simple thank-you page
    return redirect(url_for("thank_you", name=name))


@app.route("/thank-you")
def thank_you():
    """
    Thank-you page after a successful submission.
    """
    name = request.args.get("name", "Friend")
    return render_template("thank_you.html", name=name)


# Optional: health check for uptime monitors
@app.route("/healthz")
def healthz():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # Local dev run; Render will use Gunicorn (see Start Command).
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
