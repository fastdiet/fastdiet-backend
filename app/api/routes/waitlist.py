import logging
from fastapi import APIRouter, HTTPException, Query, status
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pydantic import BaseModel, EmailStr
from app.core.config import get_settings
from app.core.email_templates import EMAIL_TEXTS
from app.services.email import send_transactional_email_with_brevo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["waitlist"], prefix="/waitlist")
settings = get_settings()

class WaitlistSignup(BaseModel):
    email: EmailStr

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.brevo_api_key
api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))

LIST_ID = 5
TEMPLATE_ID = 2

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_for_waitlist(payload: WaitlistSignup, lang: str = Query("es", pattern="^(es|en)$")):
    """ Add a user to the waitlist using Brevo API"""

    logger.info(f"Attempting to add email {payload.email} to the waitlist (lang={lang}).")
    create_contact = sib_api_v3_sdk.CreateContact(
        email=payload.email,
        list_ids=[LIST_ID],
        update_enabled=True
    )

    try:
        api_response = api_instance.create_contact(create_contact)
        logger.info(f"Successfully added email {payload.email} to the waitlist with contact ID {api_response.id}.")
    except ApiException as e:
        logger.error(f"Failed to add email {payload.email} to the waitlist: {e.body}", exc_info=True)
        if e.status == 400:
            return {"message": "Contact may already exist, request processed."}
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add contact to the waitlist."
        )
    
    lang_texts = EMAIL_TEXTS.get(lang, EMAIL_TEXTS["en"])
    action_texts = lang_texts["waitlist_confirmed"]

    email_context = {
        "title": action_texts["title"],
        "greeting": action_texts["greeting"],
        "line1": action_texts["line1"],
        "highlight_text": action_texts["highlight_text"],
        "line2": action_texts["line2"],
        "farewell": action_texts["farewell"],
        "fastdiet_team": action_texts["fastdiet_team"],
        "footer_text": action_texts["footer_text"]
    }

    try:
        await send_transactional_email_with_brevo(
            to_email=payload.email,
            subject=action_texts["subject"],
            template_context=email_context,
            template_id=TEMPLATE_ID
        )
    except Exception:
        logger.error(f"Contact {payload.email} was added to the list, but the confirmation email failed to send.")

    return {"message": "Successfully added to the waitlist and confirmation email sent."}