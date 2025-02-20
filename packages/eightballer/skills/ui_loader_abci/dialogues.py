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

"""This module contains the dialogues of the ComponentLoadingAbciApp."""

from typing import Any

from aea.skills.base import Model
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.eightballer.protocols.http.dialogues import (
    HttpDialogue as BaseUiHttpDialogue,
    HttpDialogues as BaseUiHttpDialogues,
)
from packages.eightballer.protocols.websockets.dialogues import (
    WebsocketsDialogue as BaseWebsocketsDialogue,
    WebsocketsDialogues as BaseWebsocketsDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogue as BaseAbciDialogue,
    HttpDialogue as BaseHttpDialogue,
    IpfsDialogue as BaseIpfsDialogue,
    AbciDialogues as BaseAbciDialogues,
    HttpDialogues as BaseHttpDialogues,
    IpfsDialogues as BaseIpfsDialogues,
    SigningDialogue as BaseSigningDialogue,
    SigningDialogues as BaseSigningDialogues,
    LedgerApiDialogue as BaseLedgerApiDialogue,
    LedgerApiDialogues as BaseLedgerApiDialogues,
    TendermintDialogue as BaseTendermintDialogue,
    ContractApiDialogue as BaseContractApiDialogue,
    TendermintDialogues as BaseTendermintDialogues,
    ContractApiDialogues as BaseContractApiDialogues,
)


class UserInterfaceHttpDialogue(BaseUiHttpDialogue):
    """Dialogue class for the ui_loader_abci skill."""


class UserInterfaceHttpDialogues(Model, BaseUiHttpDialogues):
    """Dialogues class for the ui_loader_abci skill."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize dialogues.

        Args:
        ----
            **kwargs: Keyword arguments

        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message.

            Args:
            ----
                message (Message): an incoming/outgoing first message
                receiver_address (Address): the address of the receiving agent

            Returns:
            -------
                BaseDialogue.Role: The role of the agent

            """
            del message, receiver_address
            return BaseUiHttpDialogue.Role.SERVER

        BaseUiHttpDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


class UserInterfaceWebSocketDialogue(BaseWebsocketsDialogue):
    """Dialogue class for the ui_loader_abci skill."""


class UserInterfaceWebSocketDialogues(Model, BaseWebsocketsDialogues):
    """Dialogues class for the ui_loader_abci skill."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize dialogues.

        Args:
        ----
            **kwargs: Keyword arguments

        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message.

            Args:
            ----
                message (Message): an incoming/outgoing first message
                receiver_address (Address): the address of the receiving agent

            Returns:
            -------
                BaseDialogue.Role: The role of the agent

            """
            del message, receiver_address
            return BaseWebsocketsDialogue.Role.SERVER

        BaseWebsocketsDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


AbciDialogue = BaseAbciDialogue
AbciDialogues = BaseAbciDialogues


HttpDialogue = BaseHttpDialogue
HttpDialogues = BaseHttpDialogues

SigningDialogue = BaseSigningDialogue
SigningDialogues = BaseSigningDialogues


LedgerApiDialogue = BaseLedgerApiDialogue
LedgerApiDialogues = BaseLedgerApiDialogues


ContractApiDialogue = BaseContractApiDialogue
ContractApiDialogues = BaseContractApiDialogues


TendermintDialogue = BaseTendermintDialogue
TendermintDialogues = BaseTendermintDialogues


IpfsDialogue = BaseIpfsDialogue
IpfsDialogues = BaseIpfsDialogues
