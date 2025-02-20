"""
Simple handler funtions for the Ui ABCI loader.
"""

import datetime

from aea.skills.base import Handler


class PingPongHandler(Handler):
    """Handler for the ping pong skill."""

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
