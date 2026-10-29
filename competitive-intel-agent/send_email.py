import os
import smtplib
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import markdown
from dotenv import load_dotenv

load_dotenv()
DIGEST_DIR = Path("digests")


def todays_digest():
    path = DIGEST_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    if not path.exists():
        sys.exit(f"No digest for today ({path.name}). Not sending an old one.")
    return path


def main():
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    to = os.getenv("DIGEST_TO") or sender
    if not sender or not password:
        sys.exit("Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")

    path = todays_digest()
    body = path.read_text(encoding="utf-8")
    subject = f"Competitive intel digest: {path.stem}"
    if "## Source problems" in body:
        subject += " (source problems)"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(body)
    msg.add_alternative(markdown.markdown(body), subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)
    print(f"Sent {path.name} to {to}")


if __name__ == "__main__":
    main()