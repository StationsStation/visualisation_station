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

"""This module contains the shared state for the abci skill of ComponentLoadingAbciApp."""

from typing import Any

from aea.skills.base import Model

from packages.eightballer.skills.ui_loader_abci.rounds import (
    Event,
    ComponentLoadingAbciApp,
)
from packages.valory.skills.abstract_round_abci.models import (
    Requests as BaseRequests,
    BaseParams,
    SharedState as BaseSharedState,
    BenchmarkTool as BaseBenchmarkTool,
)


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = ComponentLoadingAbciApp


class UserInterfaceClientStrategy(Model):
    """This class represents a user interface client strategy."""

    clients: dict[str, dict] = {}
    handlers: list = []
    behaviours: list = []
    routes: dict = {}


class UserInterfaceLoaderParams(BaseParams):
    """Keep the current params of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters' object."""
        # this is a mapping from a prediction market spec's attribute to the creators we want to take into account
        user_interface_config = kwargs.get("user_interface")
        self.user_interface_enabled = user_interface_config.get("enabled", False)
        if self.user_interface_enabled:
            custom_component_name = user_interface_config.get(
                "custom_component",
            )
            self.user_interface_name = custom_component_name
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up."""
        super().setup()
        ComponentLoadingAbciApp.event_to_timeout[Event.ROUND_TIMEOUT] = self.context.params.round_timeout_seconds


Params = UserInterfaceLoaderParams
Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
