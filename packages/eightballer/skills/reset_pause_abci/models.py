# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""This module contains the shared state for the 'reset_pause_abci' application."""

from packages.valory.skills.abstract_round_abci.models import (
    Requests as BaseRequests,
    BaseParams,
    SharedState as BaseSharedState,
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.eightballer.skills.reset_pause_abci.rounds import Event, ResetPauseAbciApp


MARGIN = 5

Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = ResetPauseAbciApp

    def setup(self) -> None:
        """Set up."""
        super().setup()
        ResetPauseAbciApp.event_to_timeout[Event.ROUND_TIMEOUT] = self.context.params.round_timeout_seconds
        ResetPauseAbciApp.event_to_timeout[Event.RESET_AND_PAUSE_TIMEOUT] = (
            self.context.params.reset_pause_duration + MARGIN
        )


Params = BaseParams
