import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class Mailer:
    def __init__(self):
        self.mode = os.getenv("MODE", "local").strip().lower()
        if self.mode not in {"local", "server"}:
            raise ValueError("MODE must be 'local' or 'server'")

        if self.mode == "local":
            # Authenticated SMTP using your private mailbox on your local machine
            self.from_addr = os.getenv("LOCAL_FROM")
            self.host = os.getenv("LOCAL_SMTP_HOST")
            self.port = int(os.getenv("LOCAL_SMTP_PORT", "587"))
            self.user = os.getenv("LOCAL_SMTP_USER")
            self.password = os.getenv("LOCAL_SMTP_PASS")
            self.security = os.getenv("LOCAL_SMTP_SECURITY", "starttls").strip().lower()
            if not all([self.from_addr, self.host, self.user, self.password]):
                raise ValueError("LOCAL_* env vars are incomplete for MODE=local")
        else:
            # Server mode: send via local Postfix (localhost:25), no auth
            self.from_addr = os.getenv("SERVER_FROM")
            if not self.from_addr:
                raise ValueError("SERVER_FROM is required for MODE=server")

        self.debug = os.getenv("SMTP_DEBUG", "").lower() in {"1", "true", "yes", "on"}

    def send(
        self, 
        to_addr: str, 
        subject: str, 
        text_body: str, 
        html_body: str | None = None, 
        timeout: float = 20.0
    ):
        if not to_addr:
            raise ValueError("to_addr is required")

        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg["Message-ID"] = make_msgid(domain=self.from_addr.split("@")[-1])

        if html_body:
            # Provide plain text for compatibility if HTML provided
            if not text_body:
                text_body = "This message contains HTML. Please view it in an HTML-capable client."
            msg.set_content(text_body)
            msg.add_alternative(html_body, subtype="html")
        else:
            msg.set_content(text_body or "")

        # Envelope MAIL FROM matches header From (good for SPF/DMARC)
        env_from = self.from_addr

        if self.mode == "local":
            if self.security == "ssl":
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=timeout) as s:
                    if self.debug: s.set_debuglevel(1)
                    s.login(self.user, self.password)
                    s.send_message(msg, from_addr=env_from, to_addrs=[to_addr])
            else:
                with smtplib.SMTP(self.host, self.port, timeout=timeout) as s:
                    if self.debug: s.set_debuglevel(1)
                    s.ehlo()
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                    s.login(self.user, self.password)
                    s.send_message(msg, from_addr=env_from, to_addrs=[to_addr])
            return

        # MODE=server → local Postfix (opendkim will sign)
        with smtplib.SMTP("localhost", 25, timeout=timeout) as s:
            if self.debug: s.set_debuglevel(1)
            s.send_message(msg, from_addr=env_from, to_addrs=[to_addr])
