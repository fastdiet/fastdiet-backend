import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from fastapi import HTTPException
from pydantic import EmailStr

from app.core.config import get_settings
from app.core.errors import ErrorCode

settings = get_settings()
logger = logging.getLogger(__name__)

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.brevo_api_key

async def send_transactional_email_with_brevo(
    to_email: EmailStr,
    subject: str,
    template_context: dict,
    template_id: int
):
    template_context['subject'] = subject
    
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    sender = sib_api_v3_sdk.SendSmtpEmailSender(email=settings.sender_email, name="FastDiet")
    to = [sib_api_v3_sdk.SendSmtpEmailTo(email=to_email)]
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender,
        to=to,
        template_id=template_id,
        params=template_context,
        reply_to=sender
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email sent successfully to {to_email} via Brevo API. Message ID: {api_response.message_id}")
    except ApiException as e:
        error_body = e.body
        logger.error(f"Error sending email to {to_email} via Brevo API: {error_body}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": ErrorCode.EMAIL_SEND_ERROR, "message": "Error sending email"}
        )
