"""Mobile-Money provider interface."""

from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    reference: str = ""
    error: str = ""


class MobileMoneyProvider:
    """Interface every Mobile-Money adapter implements.

    Amounts are ``decimal.Decimal`` in the wallet currency (XAF/FCFA). ``phone``
    is the subscriber MSISDN; ``provider`` is the operator id (mtn/orange/...).
    """

    def request_payment(self, phone, amount, provider, reference) -> PaymentResult:
        """Charge the passenger (pull funds into platform escrow)."""
        raise NotImplementedError

    def payout(self, phone, amount, provider, reference) -> PaymentResult:
        """Disburse funds to the driver."""
        raise NotImplementedError

    def refund(self, reference, amount) -> PaymentResult:
        """Refund a previously charged payment."""
        raise NotImplementedError
