# ------------------------------------------------------------------------------
#
#   Copyright 2024 eightballer
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This package contains a scaffold of a handler."""

from aea.skills.base import Handler

from packages.eightballer.protocols.http.message import HttpMessage as UiHttpMessage


class HttpHandler(Handler):
    """Implements the HTTP handler."""

    SUPPORTED_PROTOCOL = UiHttpMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""

    def teardown(self) -> None:
        """Tear down the handler."""

    def handle(self, message: UiHttpMessage):
        """Handle the message."""
        return self.handle_get(message)

    def handle_get(self, message: UiHttpMessage):
        """Handle GET request for /."""

        return {"ping": message.body}

    def handle_get_agent_info(self):
        """Handle GET request for /api/agent-info."""
        raise NotImplementedError

    def handle_get_mech_events(self, message):
        """Handle GET request for /api/mech-events."""
        return {"mech_events": message.body}

    def handle_unexpected_message(self, message):
        """Handler for unexpected messages."""
        self.context.logger.info(f"Received unexpected message: {message}")
        return "Content-Type: text/plain\n", b"Not Found"
