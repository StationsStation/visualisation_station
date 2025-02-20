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

"""This module contains the behaviours for the trader skill."""

from packages.eightballer.skills.trader_abci.composition import TraderAbciApp
from packages.valory.skills.registration_abci.behaviours import (
    RegistrationStartupBehaviour,
    AgentRegistrationRoundBehaviour,
)
from packages.eightballer.skills.ui_loader_abci.behaviours import (
    ComponentLoadingRoundBehaviour,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    BaseBehaviour,
    AbstractRoundBehaviour,
)
from packages.eightballer.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)


class TraderConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the trader."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = TraderAbciApp

    behaviours: set[type[BaseBehaviour]] = {
        *AgentRegistrationRoundBehaviour.behaviours,
        *ComponentLoadingRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
    }
