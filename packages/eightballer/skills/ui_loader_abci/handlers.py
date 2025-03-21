# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

"""This module contains the handlers for the skill of ComponentLoadingAbciApp."""

import json
from typing import cast

from aea.protocols.base import Message

from packages.eightballer.protocols.http.message import HttpMessage as UiHttpMessage
from packages.eightballer.protocols.websockets.message import WebsocketsMessage
from packages.eightballer.skills.ui_loader_abci.models import (
    UserInterfaceClientStrategy,
)
from packages.eightballer.protocols.websockets.dialogues import (
    WebsocketsDialogue,
    WebsocketsDialogues,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
    IpfsHandler as BaseIpfsHandler,
    SigningHandler as BaseSigningHandler,
    ABCIRoundHandler as BaseABCIRoundHandler,
    LedgerApiHandler as BaseLedgerApiHandler,
    TendermintHandler as BaseTendermintHandler,
    ContractApiHandler as BaseContractApiHandler,
)


DEFAULT_ENCODING = "utf-8"
ERROR_RESPONSE = {"error": "Not Found"}
CONTENT_TYPE_JSON = "Content-Type: application/json"


DEFAULT_API_HEADERS = "Content-Type: application/json\n"


class BaseHandler(BaseHttpHandler):
    """Base handler for logging."""

    @property
    def strategy(self) -> str | None:
        """Get the strategy."""
        return cast(UserInterfaceClientStrategy, self.context.user_interface_client_strategy)

    def get_headers(self, original_headers: str) -> str:
        """Appends cors headers."""
        cors_headers = "Access-Control-Allow-Origin: *\n"
        cors_headers += "Access-Control-Allow-Methods: GET,POST\n"
        cors_headers += "Access-Control-Allow-Headers: Content-Type,Accept\n"
        return cors_headers + original_headers


class UserInterfaceHttpHandler(BaseHandler):
    """Handler for the HTTP requests of the ui_loader_abci skill."""

    SUPPORTED_PROTOCOL = UiHttpMessage.protocol_id

    def handle(self, message: Message) -> None:
        """Handle the message."""
        self.context.logger.debug("Handling new http connection message in skill")
        message = cast(UiHttpMessage, message)
        dialogue = self.context.user_interface_http_dialogues.update(message)
        if dialogue is None:
            self.context.logger.error(f"Could not locate dialogue for message={message}")
            return
        self.handle_http_request(message, dialogue)

    def handle_http_request(self, message: UiHttpMessage, dialogue) -> None:
        """We handle the http request to return the necessary files."""
        if self.is_api_route(message.url):
            api_response = self.handle_api_request(message, dialogue)
            return self.send_api_http_response(
                api_response,
                dialogue,
            )
        if self.is_websocket_request(message):
            return self.handle_websocket_request(message, dialogue)
        headers, content = self.handle_frontend_request(message, dialogue)
        return self.send_http_response(message, dialogue, headers, content)

    def is_api_route(self, url: str) -> bool:
        """Check if the url is an api route."""
        parts = url.split("/")
        if "api" in parts:
            self.context.logger.info(f"API route detected: {url}")
            return True
        return False

    def is_websocket_request(self, message: UiHttpMessage) -> bool:
        """Check if the request is a websocket request using the headers."""
        return "Upgrade: websocket" in message.headers

    def handle_websocket_request(self, message: UiHttpMessage, dialogue) -> None:
        """Handle the websocket request."""
        self.strategy.clients[dialogue.incomplete_dialogue_label.get_incomplete_version().dialogue_reference[0]] = (
            dialogue
        )

        self.context.logger.debug(f"Total clients: {len(self.strategy.clients)}")
        self.context.logger.debug(f"Handling websocket request in skill: {message.dialogue_reference}")

    def handle_api_request(self, message: UiHttpMessage, dialogue) -> UiHttpMessage:
        """Handle the api request."""
        self.context.logger.debug(f"Received api route request: {message.url}")
        self.context.logger.debug(f"Received dialogue: {dialogue}")

        parts = message.url.split("/")

        if parts[-1] == "agent-info":
            data = {
                "service-id": self.context.params.on_chain_service_id,
                "safe-address": self.context.params.setup_params["safe_contract_address"],
                "agent-address": self.context.agent_address,
                "agent-status": "active" if self.context.is_active else "inactive",
            }
            content = json.dumps(data).encode(DEFAULT_ENCODING)
            return UiHttpMessage(
                performative=UiHttpMessage.Performative.RESPONSE,
                status_code=200,
                status_text="OK",
                headers=CONTENT_TYPE_JSON,
                version=message.version,
                body=content,
            )

        for handler in self.strategy.handlers:
            result = handler.handle(message)
            self.context.logger.debug(f"Received result: {result}")
            if result is not None:
                return UiHttpMessage(
                    performative=UiHttpMessage.Performative.RESPONSE,
                    status_code=result.status_code,
                    status_text=result.status_text,
                    headers=CONTENT_TYPE_JSON,
                    version=message.version,
                    body=result.body,
                )

        content = json.dumps(ERROR_RESPONSE).encode(DEFAULT_ENCODING)
        return UiHttpMessage(
            performative=UiHttpMessage.Performative.RESPONSE,
            status_code=404,
            headers=CONTENT_TYPE_JSON,
            version=message.version,
            status_text="Not Found",
            body=content,
        )

    def handle_frontend_request(self, message: UiHttpMessage, dialogue) -> bytes:
        """Handle the frontend request."""
        del dialogue

        routes = self.strategy.routes
        self.context.logger.debug(f"Available routes: {list(routes.keys())}")
        path = "/".join(message.url.split("/")[3:])
        if path == "":
            path = "index.html"

        content = None if routes is None else routes.get(path, None)
        # we want to extract the path from the url
        self.context.logger.info(f"Received request for path: {path}")

        if path is None or content is None:
            self.context.logger.warning(f"Context not found for path: {path}")
            content = b"Not found!"
        # as we are serving the frontend, we need to set the headers accordingly
        # X-Content-Type-Options: nosniff
        # we now set headers for the responses
        if path.endswith(".html"):
            headers = "Content-Type: text/html; charset=utf-8\n"
        elif path.endswith(".js"):
            headers = "Content-Type: application/javascript; charset=utf-8\n"
        elif path.endswith(".css"):
            headers = "Content-Type: text/css; charset=utf-8\n"
        elif path.endswith(".png"):
            headers = "Content-Type: image/png\n"
        elif path.endswith(".ico"):
            headers = "Content-Type: image/x-icon\n"
        elif path.endswith(".json"):
            headers = "Content-Type: application/json; charset=utf-8\n"
        else:
            headers = "Content-Type: text/plain; charset=utf-8\n"

        return headers, content

    def send_http_response(self, message: UiHttpMessage, dialogue, headers: str, content: bytes) -> None:
        """Send the http response."""
        cors_headers = self.get_headers(headers)
        response_msg = dialogue.reply(
            performative=UiHttpMessage.Performative.RESPONSE,
            target_message=message,
            status_code=200,
            headers=cors_headers,
            version=message.version,
            status_text="OK",
            body=content,
        )
        self.context.outbox.put_message(message=response_msg)

    def send_api_http_response(self, message: UiHttpMessage, dialogue) -> None:
        """Send the api http response."""
        cors_headers = self.get_headers(message.headers)
        response_msg = dialogue.reply(
            performative=UiHttpMessage.Performative.RESPONSE,
            target_message=message,
            status_code=message.status_code,
            headers=cors_headers,
            version=message.version,
            status_text=message.status_text,
            body=message.body,
        )
        self.context.outbox.put_message(message=response_msg)


class UserInterfaceWsHandler(UserInterfaceHttpHandler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = WebsocketsMessage.protocol_id

    def handle(self, message: Message) -> None:
        """Implement the reaction to an envelope.

        Args:
        ----
            message (Message): the message

        """
        if message.performative == WebsocketsMessage.Performative.CONNECT:
            return self._handle_connect(message)

        dialogue = self.websocket_dialogues.get_dialogue(message)

        if message.performative == WebsocketsMessage.Performative.DISCONNECT:
            return self._handle_disconnect(message, dialogue)
        # it is an existing dialogue
        if dialogue is None:
            self.context.logger.error(f"Could not locate dialogue for message={message}")
            return None
        if message.performative == WebsocketsMessage.Performative.SEND:
            return self._handle_send(message, dialogue)
        self.context.logger.warning(f"Cannot handle websockets message of performative={message.performative}")
        return None

    def _handle_disconnect(self, message: Message, dialogue: WebsocketsDialogue) -> None:
        """Implement the reaction to an envelope.

        Args:
        ----
            message (Message): the message

        """
        self.context.logger.info(f"Handling disconnect message in skill: {message}")
        ws_dialogues_to_connections = {v.incomplete_dialogue_label: k for k, v in self.strategy.clients.items()}
        if dialogue.incomplete_dialogue_label in ws_dialogues_to_connections:
            del self.strategy.clients[ws_dialogues_to_connections[dialogue.incomplete_dialogue_label]]
            self.context.logger.info(f"Total clients: {len(self.strategy.clients)}")
        else:
            self.context.logger.warning(f"Could not find dialogue to disconnect: {dialogue.incomplete_dialogue_label}")

    def _handle_send(self, message: Message, dialogue) -> None:
        """Implement the reaction to an envelope.

        Args:
        ----
            message (Message): the message

        """
        # we here need to basically literate all of the handlers from the custom component
        # and then call the handle method on them.

        for handler_func in self.strategy.handlers:
            response_data = handler_func.handle(message)
            if response_data is not None:
                self.context.logger.info(f"Handling message in skill: {message.data}")
                response_message = dialogue.reply(
                    performative=WebsocketsMessage.Performative.SEND,
                    target_message=dialogue.last_message,
                    data=response_data,
                )
                self.context.outbox.put_message(message=response_message)

    @property
    def websocket_dialogues(self) -> "WebsocketsDialogues":
        """Get the http dialogues."""
        return cast(WebsocketsDialogues, self.context.user_interface_ws_dialogues)

    def _handle_connect(self, message: Message) -> None:
        """Implement the reaction to the connect message."""

        dialogue: WebsocketsDialogue = self.websocket_dialogues.get_dialogue(message)

        if dialogue:
            self.context.logger.debug(f"Already have a dialogue for message={message}")
            return
        client_reference = message.url
        dialogue = self.websocket_dialogues.update(message)
        response_msg = dialogue.reply(
            performative=WebsocketsMessage.Performative.CONNECTION_ACK,
            success=True,
            target_message=message,
        )
        self.context.logger.info(f"Handling connect message in skill: {client_reference}")
        self.strategy.clients[client_reference] = dialogue
        self.context.outbox.put_message(message=response_msg)


ABCIHandler = BaseABCIRoundHandler
HttpHandler = BaseHttpHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler
IpfsHandler = BaseIpfsHandler
