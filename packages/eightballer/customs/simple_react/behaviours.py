"""Behaviours for the simple react skill."""

import os
from typing import cast
from pathlib import Path

from aea.skills.base import Behaviour

from packages.eightballer.protocols.websockets.message import WebsocketsMessage
from packages.eightballer.skills.ui_loader_abci.models import (
    UserInterfaceClientStrategy,
)


class LogReadingBehaviour(Behaviour):
    """Reads in the log file and sends the new lines to the client."""

    lines: int = 0
    client_to_lines: dict = {}
    log_file: str = ""

    @property
    def strategy(self) -> str | None:
        """Get the strategy."""
        return cast(UserInterfaceClientStrategy, self.context.user_interface_client_strategy)

    def setup(self):
        """Implement the setup."""
        super().setup()
        self.lines = 0
        self.client_to_lines = {}
        self.log_file = os.environ.get("LOG_FILE", "log.txt")

    def send_message(self, data, dialogue):
        """Send a message to the client."""
        msg = dialogue.reply(
            performative=WebsocketsMessage.Performative.SEND,
            data=data,
        )
        self.context.outbox.put_message(message=msg)

    def teardown(self):
        """Implement the handler teardown."""

    def act(self):
        """We read in the log file and send the new lines to the client.
        We do so in an efficent manner, only reading the new lines.
        we make sure to send a message to all clients.
        """
        self.read_log()

    def read_log(self):
        """Read in each log line."""
        with open(
            Path(self.log_file),
            encoding="utf-8",
        ) as f:
            for line in f.readlines()[self.lines :]:
                self.lines += 1
                for dialogue in self.strategy.clients.values():
                    self.send_message(line, dialogue)
