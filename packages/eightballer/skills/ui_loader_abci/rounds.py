# -*- coding: utf-8 -*-
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

"""This package contains the rounds of ComponentLoadingAbciApp."""

from enum import Enum
from typing import Set, Dict, Tuple, Optional, FrozenSet

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AppState,
    EventToTimeout,
    DegenerateRound,
    BaseSynchronizedData,
    AbciAppTransitionFunction,
    CollectSameUntilThresholdRound,
)
from packages.eightballer.skills.ui_loader_abci.payloads import (
    ErrorPayload,
    SetupPayload,
    HealthcheckPayload,
)


class Event(Enum):
    """ComponentLoadingAbciApp Events"""

    DONE = "done"
    ERROR = "error"
    ROUND_TIMEOUT = "round_timeout"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def error_data(self) -> Optional[ErrorPayload]:
        """Return the error data."""
        return str(self.db.get_strict("error_data"))

    @property
    def setup_data(self) -> Optional[SetupPayload]:
        """Return the setup data."""
        return str(self.db.get_strict("setup_data"))

    @property
    def healthcheck_data(self) -> Optional[HealthcheckPayload]:
        """Return the healthcheck data."""
        return str(self.db.get_strict("healthcheck_data"))


class BaseRound(CollectSameUntilThresholdRound):
    """BaseRound"""

    payload_class = None
    payload_attribute = None
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""

        if not self.threshold_reached:
            return None
        state = self.synchronized_data.update(
            synchronized_data_class=self.synchronized_data_class,
            **{self.payload_attribute: self.most_voted_payload},
        )
        return state, Event.DONE


class ErrorRound(BaseRound):
    """ErrorRound"""

    payload_class = ErrorPayload
    payload_attribute = "error_data"
    synchronized_data_class = SynchronizedData


class HealthcheckRound(BaseRound):
    """HealthcheckRound"""

    payload_class = HealthcheckPayload
    synchronized_data_class = SynchronizedData
    payload_attribute = "healthcheck_data"


class SetupRound(BaseRound):
    """SetupRound"""

    payload_class = SetupPayload
    synchronized_data_class = SynchronizedData
    payload_attribute = "setup_data"


class DoneRound(DegenerateRound):
    """DoneRound"""


class ComponentLoadingAbciApp(AbciApp[Event]):
    """ComponentLoadingAbciApp"""

    initial_round_cls: AppState = SetupRound
    initial_states: Set[AppState] = {HealthcheckRound, SetupRound}
    transition_function: AbciAppTransitionFunction = {
        SetupRound: {Event.DONE: HealthcheckRound, Event.ERROR: ErrorRound},
        HealthcheckRound: {Event.DONE: DoneRound, Event.ERROR: ErrorRound},
        ErrorRound: {Event.DONE: SetupRound},
        DoneRound: {},
    }
    final_states: Set[AppState] = {DoneRound}
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
    db_pre_conditions: Dict[AppState, Set[str]] = {
        HealthcheckRound: set([]),
        SetupRound: set([]),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        DoneRound: set([]),
    }
