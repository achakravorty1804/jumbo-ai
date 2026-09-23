import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email(subject: str, body: str, recipient: str | None = None) -> None:
    """
    Send a plain-text email through Gmail SMTP.
    """

    if not GMAIL_ADDRESS:
        raise RuntimeError("GMAIL_ADDRESS is missing from .env")

    if not GMAIL_APP_PASSWORD:
        raise RuntimeError("GMAIL_APP_PASSWORD is missing from .env")

    recipient = recipient or GMAIL_ADDRESS

    message = EmailMessage()
    message["From"] = GMAIL_ADDRESS
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(message)