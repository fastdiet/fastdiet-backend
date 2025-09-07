import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr
from app.core.config import get_settings
from app.core.errors import ErrorCode


settings = get_settings()
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
SENDER_EMAIL = settings.sender_email
SENDER_PASSWORD = settings.sender_password

logger = logging.getLogger(__name__)
env = Environment(loader=FileSystemLoader("app/templates"))

# Function to send an email using SMTP
def send_email(
        to_email: EmailStr,
        subject: str,
        template_context: dict,
        template_name: str = "email_template.html"
):
    try:
        validate_email(to_email)
        template = env.get_template(template_name)
        html_content = template.render(template_context)
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            server.quit()

        logger.info(f"Email sent successfully to {to_email}")
        return True
    except EmailNotValidError:
        logger.warning(f"Email cannot be sent to {to_email} because it is not a valid email")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.EMAIL_NOT_VALID, "message": "Email not valid"}
        )
    except Exception as e:
        logger.warning(f"Error sending email to {to_email}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": ErrorCode.EMAIL_SEND_ERROR, "message": "Error sending email"}
        )