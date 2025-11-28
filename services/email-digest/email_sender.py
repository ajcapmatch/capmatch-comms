"""Email sending functionality (currently logs to console)."""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


def send_digest_email(
    user_email: str,
    user_name: Optional[str],
    html_body: str,
    text_body: str,
    event_count: int
) -> bool:
    """
    Send digest email via Resend API.
    Currently logs to console instead of actually sending.
    
    Returns True if "sent" successfully, False otherwise.
    """
    try:
        # Log email details to console
        logger.info("=" * 80)
        logger.info(f"EMAIL DIGEST - To: {user_email}")
        logger.info(f"Subject: Your CapMatch Daily Digest")
        logger.info(f"Events: {event_count}")
        logger.info("-" * 80)
        logger.info("HTML Body:")
        logger.info(html_body)
        logger.info("-" * 80)
        logger.info("Text Body:")
        logger.info(text_body)
        logger.info("=" * 80)
        
        # TODO: When ready to send actual emails, uncomment and implement:
        # import resend
        # resend.api_key = Config.RESEND_API_KEY
        # 
        # params = {
        #     "from": Config.EMAIL_FROM,
        #     "to": [user_email],
        #     "subject": "Your CapMatch Daily Digest",
        #     "html": html_body,
        #     "text": text_body,
        # }
        # 
        # email = resend.Emails.send(params)
        # return email.get('id') is not None
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {user_email}: {e}")
        return False

