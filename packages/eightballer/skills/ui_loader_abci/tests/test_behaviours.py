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

"""This package contains round behaviours of ComponentLoadingAbciApp."""

from typing import Any
from pathlib import Path
from dataclasses import field, dataclass
from collections.abc import Hashable

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.eightballer.skills.ui_loader_abci.rounds import Event, SynchronizedData
from packages.eightballer.skills.ui_loader_abci.behaviours import (
    ErrorBehaviour,
    SetupBehaviour,
    HealthcheckBehaviour,
    ComponentLoadingBaseBehaviour,
    ComponentLoadingRoundBehaviour,
)
from packages.valory.skills.abstract_round_abci.behaviours import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)


@dataclass
class BehaviourTestCase:
    """BehaviourTestCase."""

    name: str
    initial_data: dict[str, Hashable]
    event: Event
    kwargs: dict[str, Any] = field(default_factory=dict)


class BaseComponentLoadingTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parent.parent

    behaviour: ComponentLoadingRoundBehaviour
    behaviour_class: type[ComponentLoadingBaseBehaviour]
    next_behaviour_class: type[ComponentLoadingBaseBehaviour]
    synchronized_data: SynchronizedData
    done_event = Event.DONE

    @property
    def current_behaviour_id(self) -> str:
        """Current RoundBehaviour's behaviour id."""

        return self.behaviour.current_behaviour.behaviour_id

    def fast_forward(self, data: dict[str, Any] | None = None) -> None:
        """Fast-forward on initialization."""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert self.current_behaviour_id == self.behaviour_class.behaviour_id

    def complete(self, event: Event) -> None:
        """Complete test."""

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert self.current_behaviour_id == self.next_behaviour_class.behaviour_id


class TestErrorBehaviour(BaseComponentLoadingTest):
    """Tests ErrorBehaviour."""

    behaviour_class: type[BaseBehaviour] = ErrorBehaviour
    next_behaviour_class: type[BaseBehaviour] = ...

    @pytest.mark.parametrize("test_case", [])
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)


class TestHealthcheckBehaviour(BaseComponentLoadingTest):
    """Tests HealthcheckBehaviour."""

    behaviour_class: type[BaseBehaviour] = HealthcheckBehaviour
    next_behaviour_class: type[BaseBehaviour] = ...

    @pytest.mark.parametrize("test_case", [])
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)


class TestSetupBehaviour(BaseComponentLoadingTest):
    """Tests SetupBehaviour."""

    behaviour_class: type[BaseBehaviour] = SetupBehaviour
    next_behaviour_class: type[BaseBehaviour] = ...

    @pytest.mark.parametrize("test_case", [])
    def test_run(self, test_case: BehaviourTestCase) -> None:
        """Run tests."""

        self.fast_forward(test_case.initial_data)
        self.complete(test_case.event)
