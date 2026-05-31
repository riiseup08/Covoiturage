"""Monetbil adapter (skeleton).

Outlines the real HTTP integration. Not wired to live credentials; activate by
setting ``PAYMENT_PROVIDER = "covoiturage.payments.monetbil.MonetbilProvider"``
and the ``MONETBIL_*`` env vars. Kept thin on purpose — fill in once an account
and sandbox keys are available.
"""

import os

from .base import MobileMoneyProvider, PaymentResult

MONETBIL_BASE_URL = "https://api.monetbil.com/payment/v1"


class MonetbilProvider(MobileMoneyProvider):
    def __init__(self):
        self.service_key = os.environ.get("MONETBIL_SERVICE_KEY", "")
        self.service_secret = os.environ.get("MONETBIL_SERVICE_SECRET", "")
        if not self.service_key:
            raise RuntimeError("MONETBIL_SERVICE_KEY is required for MonetbilProvider")

    def request_payment(self, phone, amount, provider, reference):
        # POST {MONETBIL_BASE_URL}/placePayment with service, phonenumber, amount,
        # operator, payment_ref -> returns payment_id; poll checkPayment for status.
        raise NotImplementedError("Monetbil integration not yet wired")

    def payout(self, phone, amount, provider, reference):
        raise NotImplementedError("Monetbil payout not yet wired")

    def refund(self, reference, amount):
        raise NotImplementedError("Monetbil refund not yet wired")
