# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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


"""This module contains the handlers for the 'trader_abci' skill."""

from packages.eightballer.skills.ui_loader_abci.handlers import (
    UserInterfaceWsHandler as BaseUserInterfaceWsHandler,
    UserInterfaceHttpHandler as BaseUserInterfaceHttpHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
    IpfsHandler as BaseIpfsHandler,
    SigningHandler as BaseSigningHandler,
    ABCIRoundHandler,
    LedgerApiHandler as BaseLedgerApiHandler,
    TendermintHandler as BaseTendermintHandler,
    ContractApiHandler as BaseContractApiHandler,
)


TraderHandler = ABCIRoundHandler
HttpHandler = BaseHttpHandler
UserInterfaceHttpHandler = BaseUserInterfaceHttpHandler
UserInterfaceWsHandler = BaseUserInterfaceWsHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler
IpfsHandler = BaseIpfsHandler
