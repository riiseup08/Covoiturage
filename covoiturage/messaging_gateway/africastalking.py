"""Africa's Talking SMS gateway (skeleton).

Activate with ``SMS_GATEWAY = "covoiturage.messaging_gateway.africastalking.AfricasTalkingGateway"``
and the ``AT_USERNAME`` / ``AT_API_KEY`` env vars. Real send is left unimplemented
until a sandbox account is available.
"""

import os

from .base import SmsGateway, SmsResult


class AfricasTalkingGateway(SmsGateway):
    def __init__(self):
        self.username = os.environ.get("AT_USERNAME", "")
        self.api_key = os.environ.get("AT_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("AT_API_KEY is required for AfricasTalkingGateway")

    def send_sms(self, to, text):
        # POST https://api.africastalking.com/version1/messaging
        # headers: apiKey; data: username, to, message
        raise NotImplementedError("Africa's Talking integration not yet wired")
