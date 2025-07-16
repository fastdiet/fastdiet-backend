import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException
from pydantic import EmailStr
from app.core.config import get_settings
from app.core.errors import ErrorCode


settings = get_settings()
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
SENDER_EMAIL = settings.sender_email
SENDER_PASSWORD = settings.sender_password

# Function to send an email using SMTP
def send_email(to_email: EmailStr, subject: str, body: str):
    try:
        validate_email(to_email)
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        return True
    except EmailNotValidError:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.EMAIL_NOT_VALID, "message": "Email not valid"}
        )
    except Exception as e:
        print("Error sending the email:", repr(e))
        raise HTTPException(
            status_code=500,
            detail={"code": ErrorCode.EMAIL_SEND_ERROR, "message": "Error sending email"}
        )