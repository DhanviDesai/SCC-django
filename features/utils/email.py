import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import email
from email.utils import formataddr
import atexit

from django.conf import settings

class EmailClient:
    _instance = None

    def __init__(self):
        self.server = smtplib.SMTP_SSL(settings.MAIL_SMTP_SERVER, 465)
        self.server.set_debuglevel(1)
        self.server.login(settings.MAIL_EMAIL_LOGIN, settings.MAIL_EMAIL_PASSWORD)
        self.sender_name = "SCC Team"
        atexit.register(self.close)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def close(self):
        if self.server:
            self.server.quit()
            time.sleep(1)

    def send_invite_guest(self, tournament, inviter, to_email, password_reset_link):

        plain_text = f"""
            Hi,

            Welcome! You have been invited to take part in {tournament} by {inviter}.
            Your account has been successfully created.

            To get started, please click on the link or copy and paste the following link into your browser to set your password:
            {password_reset_link}

            This link is valid for the next 24 hours.

            Thanks,
            The SCC Team
            """

        html_content = f"""
            <html>
            <head></head>
            <body>
            <h2 style="color: #333;">Welcome to SCC!</h2>
            <p>Hi,</p>
            <p>Welcome! You have been invited to take part in {tournament} by {inviter}.</p>
            <p>Your account has been successfully created. To get started, you just need to set a password.</p>
            <a href="{password_reset_link}" style="background-color: #4CAF50; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; border-radius: 8px;">Set Your Password</a>
            <p>Thanks,<br>The SCC Team</p>
            </body>
            </html>
            """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Invitation to join {tournament}"
        msg['From'] = formataddr((self.sender_name, settings.MAIL_EMAIL_LOGIN))
        msg['To'] = to_email
        msg['Date'] = email.utils.formatdate(localtime=True)
        msg['Message-ID'] = email.utils.make_msgid()
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        self.server.send_message(msg)
        time.sleep(1)
