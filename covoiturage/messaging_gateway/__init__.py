"""SMS gateway abstraction.

``get_gateway()`` returns the configured gateway. Defaults to ``ConsoleGateway``
(prints to stdout / records calls) so SMS-dependent flows run with no account.
"""

from django.conf import settings
from django.utils.module_loading import import_string

from .base import SmsGateway, SmsResult  # noqa: F401

_DEFAULT = "covoiturage.messaging_gateway.console.ConsoleGateway"


def get_gateway():
    path = getattr(settings, "SMS_GATEWAY", _DEFAULT)
    return import_string(path)()
