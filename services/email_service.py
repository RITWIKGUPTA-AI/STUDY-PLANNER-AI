import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

if not SMTP_USER or not SMTP_PASSWORD:
    print("WARNING: SMTP_USER / SMTP_PASSWORD are not set. Password-reset "
          "emails will not be sent until these are added to your .env file "
          "or hosting environment variables. See the setup notes in the "
          "changelog for how to get a free Gmail App Password.")


def send_email(to_email, subject, body):
    """
    Sends a plain-text email. Returns True on success, False on failure —
    never raises, so a misconfigured/unreachable SMTP server can't crash
    whatever route triggered the email.
    """

    if not SMTP_USER or not SMTP_PASSWORD:
        print("Email not sent (SMTP not configured):", subject, "->", to_email)
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        return True

    except Exception as e:
        print("\n========== EMAIL SEND ERROR ==========")
        print(e)
        print("=======================================\n")
        return False


def send_password_reset_email(to_email, username, reset_url):
    subject = "Reset your Student Study Planner password"
    body = f"""Hi {username},

We received a request to reset your Student Study Planner password.

Click the link below to choose a new password. This link expires in 30 minutes:

{reset_url}

If you didn't request this, you can safely ignore this email — your password will not be changed.

- Student Study Planner
"""
    return send_email(to_email, subject, body)
