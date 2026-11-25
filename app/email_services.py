import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def send_email(to_email: str, subject: str, body: str, attachment_path: str) -> None:
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not password:
        raise ValueError("GMAIL_ADDRESS or GMAIL_APP_PASSWORD is missing in .env")

    # Build the email
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach the resume (PDF)
    path = Path(attachment_path)
    msg.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=path.name,
    )

    # Log in to Gmail and send
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)