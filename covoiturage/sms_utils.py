"""
SMS OTP utilities for phone verification.
Integrates with Twilio or similar SMS service.
"""
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from .models import PhoneOTP
import os

# Configuration - Update these with your SMS service credentials
SMS_SERVICE = os.environ.get('SMS_SERVICE', 'twilio')  # Options: 'twilio', 'log'
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')


def generate_otp(length=6):
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP via SMS.
    
    Args:
        phone_number: Recipient phone number
        otp_code: OTP code to send
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        if SMS_SERVICE == 'twilio':
            return _send_with_twilio(phone_number, otp_code)
        else:
            # For development: just log the OTP
            print(f"[SMS OTP] Phone: {phone_number}, Code: {otp_code}")
            return True
    except Exception as e:
        print(f"Error sending SMS to {phone_number}: {str(e)}")
        return False


def _send_with_twilio(phone_number, otp_code):
    """Send SMS using Twilio"""
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=f"Your Covoiturage verification code is: {otp_code}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return message.sid is not None
    except ImportError:
        print("Twilio library not installed. Install with: pip install twilio")
        return False


def request_phone_otp(phone_number, user=None):
    """
    Request an OTP for phone verification.
    
    Args:
        phone_number: Phone number to verify
        user: Optional User object
        
    Returns:
        dict: {'success': bool, 'otp_id': str or None, 'message': str}
    """
    # Clean phone number
    phone_number = ''.join(filter(str.isdigit, phone_number))
    if len(phone_number) < 10:
        return {'success': False, 'message': 'Invalid phone number'}
    
    # Delete any old OTPs for this phone
    PhoneOTP.objects.filter(phone=phone_number, is_verified=False).delete()
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    # Create OTP record
    phone_otp = PhoneOTP.objects.create(
        phone=phone_number,
        otp_code=otp_code,
        user=user,
        expires_at=expires_at
    )
    
    # Send SMS
    if send_otp_sms(phone_number, otp_code):
        return {
            'success': True,
            'otp_id': phone_otp.id,
            'message': f'OTP sent to {phone_number}'
        }
    else:
        phone_otp.delete()
        return {
            'success': False,
            'message': 'Failed to send OTP. Please try again.'
        }


def verify_otp(otp_id, otp_code):
    """
    Verify an OTP code.
    
    Args:
        otp_id: PhoneOTP record ID
        otp_code: Code entered by user
        
    Returns:
        dict: {'success': bool, 'message': str, 'phone': str or None}
    """
    try:
        phone_otp = PhoneOTP.objects.get(id=otp_id)
    except PhoneOTP.DoesNotExist:
        return {'success': False, 'message': 'OTP request not found'}
    
    # Check if expired
    if timezone.now() > phone_otp.expires_at:
        phone_otp.delete()
        return {'success': False, 'message': 'OTP has expired. Request a new one.'}
    
    # Check attempts
    if phone_otp.attempts >= 5:
        phone_otp.delete()
        return {'success': False, 'message': 'Too many attempts. Request a new OTP.'}
    
    # Verify code
    if phone_otp.otp_code != otp_code:
        phone_otp.attempts += 1
        phone_otp.save()
        return {'success': False, 'message': f'Invalid OTP. {5 - phone_otp.attempts} attempts remaining.'}
    
    # Mark as verified
    phone_otp.is_verified = True
    phone_otp.save()
    
    return {
        'success': True,
        'message': 'Phone verified successfully',
        'phone': phone_otp.phone
    }
