"""
SMS sending abstraction for OTP delivery.

Supports multiple backends common in Africa:
- Console (dev): prints OTP to terminal
- Africa's Talking: pan-African SMS gateway
- Twilio: international fallback

Configure via settings:
    SMS_BACKEND = 'console' | 'africastalking' | 'twilio'
"""
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

# African phone number prefixes (non-exhaustive, covers major markets)
AFRICAN_COUNTRY_CODES = [
    '+237',  # Cameroon
    '+225',  # Côte d'Ivoire
    '+221',  # Senegal
    '+223',  # Mali
    '+226',  # Burkina Faso
    '+228',  # Togo
    '+229',  # Benin
    '+233',  # Ghana
    '+234',  # Nigeria
    '+235',  # Chad
    '+241',  # Gabon
    '+242',  # Congo
    '+243',  # DRC
    '+244',  # Angola
    '+245',  # Guinea-Bissau
    '+250',  # Rwanda
    '+251',  # Ethiopia
    '+252',  # Somalia
    '+253',  # Djibouti
    '+254',  # Kenya
    '+255',  # Tanzania
    '+256',  # Uganda
    '+257',  # Burundi
    '+258',  # Mozambique
    '+260',  # Zambia
    '+261',  # Madagascar
    '+262',  # Reunion
    '+263',  # Zimbabwe
    '+265',  # Malawi
    '+266',  # Lesotho
    '+267',  # Botswana
    '+268',  # Eswatini
    '+269',  # Comoros
    '+27',   # South Africa
    '+212',  # Morocco
    '+213',  # Algeria
    '+216',  # Tunisia
    '+218',  # Libya
    '+220',  # Gambia
    '+224',  # Guinea
    '+227',  # Niger
    '+231',  # Liberia
    '+232',  # Sierra Leone
    '+236',  # Central African Republic
    '+240',  # Equatorial Guinea
    '+249',  # Sudan
    '+264',  # Namibia
    '+291',  # Eritrea
]


def normalize_phone(phone):
    """Normalize phone number: strip spaces/dashes, ensure + prefix."""
    if not phone:
        return ''
    phone = re.sub(r'[\s\-\.\(\)]', '', phone.strip())
    # If starts with 00, replace with +
    if phone.startswith('00'):
        phone = '+' + phone[2:]
    # If no +, assume Cameroon (+237) as default
    if not phone.startswith('+'):
        if len(phone) == 9 and phone[0] in ('6', '2'):
            phone = '+237' + phone
        elif len(phone) >= 10:
            phone = '+' + phone
    return phone


def validate_african_phone(phone):
    """Check if phone number looks like a valid African number."""
    phone = normalize_phone(phone)
    if not phone or len(phone) < 10:
        return False
    return any(phone.startswith(code) for code in AFRICAN_COUNTRY_CODES)


def send_otp_sms(phone, code):
    """Send OTP code via configured SMS backend."""
    phone = normalize_phone(phone)
    message = f"Covoit.Africa - Votre code de vérification est : {code}. Valable 10 minutes."

    backend = getattr(settings, 'SMS_BACKEND', 'console')

    if backend == 'console':
        return _send_console(phone, message, code)
    elif backend == 'africastalking':
        return _send_africastalking(phone, message)
    elif backend == 'twilio':
        return _send_twilio(phone, message)
    else:
        logger.error("SMS_BACKEND inconnu : %s", backend)
        return False


def _send_console(phone, message, code):
    """Dev backend: print OTP to console."""
    logger.info("=" * 50)
    logger.info("SMS OTP vers %s", phone)
    logger.info("Code: %s", code)
    logger.info("Message: %s", message)
    logger.info("=" * 50)
    print(f"\n{'=' * 50}")
    print(f"  SMS OTP -> {phone}")
    print(f"  Code: {code}")
    print(f"{'=' * 50}\n")
    return True


def _send_africastalking(phone, message):
    """Send SMS via Africa's Talking API."""
    try:
        import africastalking  # noqa: F811
    except ImportError:
        logger.error("Le package 'africastalking' n'est pas installé. pip install africastalking")
        return False

    username = getattr(settings, 'AT_USERNAME', '')
    api_key = getattr(settings, 'AT_API_KEY', '')
    if not username or not api_key:
        logger.error("AT_USERNAME et AT_API_KEY doivent être configurés dans settings.")
        return False

    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
    try:
        response = sms.send(message, [phone], sender_id=getattr(settings, 'AT_SENDER_ID', None))
        logger.info("Africa's Talking response: %s", response)
        return True
    except Exception:
        logger.exception("Erreur envoi SMS Africa's Talking vers %s", phone)
        return False


def _send_twilio(phone, message):
    """Send SMS via Twilio."""
    try:
        from twilio.rest import Client
    except ImportError:
        logger.error("Le package 'twilio' n'est pas installé. pip install twilio")
        return False

    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')
    if not all([sid, token, from_number]):
        logger.error("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER requis.")
        return False

    try:
        client = Client(sid, token)
        client.messages.create(body=message, from_=from_number, to=phone)
        return True
    except Exception:
        logger.exception("Erreur envoi SMS Twilio vers %s", phone)
        return False
