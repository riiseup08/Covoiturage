"""In-memory Mobile-Money provider for development and tests.

Succeeds synchronously and records calls so tests can assert on them. No network.
"""

import uuid

from .base import MobileMoneyProvider, PaymentResult


class StubProvider(MobileMoneyProvider):
    calls = []  # class-level log: list of (action, phone, amount, provider, reference)

    @classmethod
    def reset(cls):
        cls.calls = []

    def _record(self, action, phone, amount, provider, reference):
        type(self).calls.append((action, phone, str(amount), provider, reference))

    def request_payment(self, phone, amount, provider, reference):
        ref = reference or f"stub-{uuid.uuid4().hex[:12]}"
        self._record("request_payment", phone, amount, provider, ref)
        return PaymentResult(success=True, reference=ref)

    def payout(self, phone, amount, provider, reference):
        self._record("payout", phone, amount, provider, reference)
        return PaymentResult(success=True, reference=reference)

    def refund(self, reference, amount):
        self._record("refund", "", amount, "", reference)
        return PaymentResult(success=True, reference=reference)
