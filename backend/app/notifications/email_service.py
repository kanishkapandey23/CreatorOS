"""Email reminders — SMTP when configured, console log otherwise."""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("creatoros.notifications.email")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "CreatorOS <noreply@creatoros.app>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def is_email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_reminder_email(to_email: str, subject: str, body: str, action_href: str = None) -> bool:
    link = action_href or FRONTEND_URL
    if not link.startswith("http"):
        link = f"{FRONTEND_URL}{link}"

    html = f"""
    <div style="font-family: Georgia, serif; max-width: 520px; margin: 0 auto; color: #1a1a1a;">
      <p style="font-size: 15px; line-height: 1.6;">{body.replace(chr(10), '<br>')}</p>
      <p style="margin-top: 24px;">
        <a href="{link}" style="display: inline-block; padding: 10px 18px; background: #1a1a1a; color: #fff; text-decoration: none; border-radius: 8px; font-size: 14px;">
          Open CreatorOS
        </a>
      </p>
      <p style="margin-top: 32px; font-size: 12px; color: #888;">CreatorOS — your quiet content manager</p>
    </div>
    """

    if not is_email_configured():
        logger.info(f"[EMAIL preview] To: {to_email} | Subject: {subject}\n{body}\nLink: {link}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
