"""Simple handler funtions for the Ui ABCI loader."""

import datetime

from aea.skills.base import Handler


class PingPongHandler(Handler):
    """Handler for the ping pong skill."""

    def setup(self):
        """Set up the handler."""

    def handle(self, message):
        """Handle the data."""
        got_message = datetime.datetime.now().isoformat()
        return f"Pong @ {got_message}: {message.data}"

    def teardown(self):
        """Implement the handler teardown."""
