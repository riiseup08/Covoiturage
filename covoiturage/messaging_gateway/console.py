"""Console SMS gateway: logs messages and records them for tests."""

import logging

from .base import SmsGateway, SmsResult

logger = logging.getLogger("covoiturage.sms")


class ConsoleGateway(SmsGateway):
    sent = []  # class-level log of (to, text)

    @classmethod
    def reset(cls):
        cls.sent = []

    def send_sms(self, to, text):
        type(self).sent.append((to, text))
        logger.info("SMS -> %s: %s", to, text)
        return SmsResult(success=True)
