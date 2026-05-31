"""Mobile-Money provider abstraction.

``get_provider()`` returns the configured provider instance. Defaults to the
in-memory ``StubProvider`` so the escrow flow runs end-to-end without any
external account or network access.
"""

from django.conf import settings
from django.utils.module_loading import import_string

from .base import MobileMoneyProvider, PaymentResult  # noqa: F401

_DEFAULT = "covoiturage.payments.stub.StubProvider"


def get_provider():
    path = getattr(settings, "PAYMENT_PROVIDER", _DEFAULT)
    return import_string(path)()
