# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

"""Custom objects for the trader ABCI application."""

from typing import Dict, Type, Union, cast

from packages.valory.skills.reset_pause_abci.rounds import Event as ResetPauseEvent
from packages.eightballer.skills.ui_loader_abci.models import (
    SharedState as BaseSharedState,
    UserInterfaceLoaderParams,
    UserInterfaceClientStrategy as BaseUserInterfaceClientStrategy,
)
from packages.eightballer.skills.ui_loader_abci.rounds import Event as UIEvent
from packages.valory.skills.abstract_round_abci.models import (
    ApiSpecs,
    Requests as BaseRequests,
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.eightballer.skills.trader_abci.composition import TraderAbciApp


UserInterfaceClientStrategy = BaseUserInterfaceClientStrategy

EventType = Union[
    Type[UIEvent],
    Type[ResetPauseEvent],
]
EventToTimeoutMappingType = Dict[
    Union[UIEvent, ResetPauseEvent],
    float,
]


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


MARGIN = 5


class RandomnessApi(ApiSpecs):
    """A model for randomness api specifications."""


class TraderParams(
    UserInterfaceLoaderParams,
):
    """A model to represent the trader params."""


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = TraderAbciApp

    @property
    def params(self) -> TraderParams:
        """Get the parameters."""
        return cast(TraderParams, self.context.params)

    def setup(self) -> None:
        """Set up."""
        super().setup()

        events = (UIEvent, ResetPauseEvent)
        round_timeout = self.params.round_timeout_seconds
        round_timeout_overrides = {
            cast(EventType, event).ROUND_TIMEOUT: round_timeout for event in events
        }
        reset_pause_timeout = self.params.reset_pause_duration + MARGIN
        event_to_timeout_overrides: EventToTimeoutMappingType = {
            **round_timeout_overrides,
            UIEvent.ERROR: round_timeout,
            ResetPauseEvent.RESET_AND_PAUSE_TIMEOUT: reset_pause_timeout,
        }

        for event, override in event_to_timeout_overrides.items():
            TraderAbciApp.event_to_timeout[event] = override
