"""SMS gateway interface."""

from dataclasses import dataclass


@dataclass
class SmsResult:
    success: bool
    error: str = ""


class SmsGateway:
    def send_sms(self, to, text) -> SmsResult:
        raise NotImplementedError
