import logging
import os

from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioService:

    def __init__(self):
        self.client = Client(os.environ["TWILIO_SID"], os.environ["TWILIO_AUTH"])
        self.from_number = os.environ["TWILIO_NUMBER"]

    def send_message(self, number: str, message: str) -> bool:
        try:
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=number,
            )
            return True
        except Exception as e:
            logger.error("Failed to send SMS to %s: %s", number, e)
            return False