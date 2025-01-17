"""
Simple handler funtions for the Ui ABCI loader.
"""

import datetime

from aea.skills.base import Handler
from packages.eightballer.protocols.http.message import HttpMessage as UiHttpMessage
from packages.eightballer.protocols.websockets.message import WebsocketsMessage


class PingPongHandler(Handler):
    """Handler for the ping pong skill."""

    SUPPORTED_PROTOCOL = WebsocketsMessage.protocol_id

    def setup(self):
        """Set up the handler."""

    def handle(self, message):
        """Handle the data."""
        got_message = datetime.datetime.now().isoformat()
        response = f"Pong @ {got_message}: {message.data}"
        return response

    def teardown(self):
        """
        Implement the handler teardown.
        """

class HttpHandler(Handler):
    """Handler for the http skill."""

    SUPPORTED_PROTOCOL = UiHttpMessage.protocol_id

    def setup(self):
        """Set up the handler."""

    def handle(self, message: UiHttpMessage):
        """Handle the message."""
        return self.handle_get(message)

    def handle_get(self, message: UiHttpMessage):
        """Handle GET request for /."""

        return {"ping": message.body}

    def teardown(self):
        """Tear down the handler."""
