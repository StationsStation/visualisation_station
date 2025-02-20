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

"""This module contains the trader ABCI application."""

from packages.valory.skills.reset_pause_abci.rounds import (
    ResetPauseAbciApp,
    ResetAndPauseRound,
    FinishedResetAndPauseRound,
    FinishedResetAndPauseErrorRound,
)
from packages.valory.skills.abstract_round_abci.base import AbciApp
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedRegistrationRound,
)
from packages.eightballer.skills.ui_loader_abci.rounds import (
    DoneRound,
    SetupRound,
    HealthcheckRound,
    ComponentLoadingAbciApp,
)
from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: SetupRound,
    DoneRound: ResetAndPauseRound,
    FinishedResetAndPauseRound: HealthcheckRound,
    FinishedResetAndPauseErrorRound: ResetAndPauseRound,
}


TraderAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        ComponentLoadingAbciApp,
        ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
)


TraderAbciApp._setup = TraderAbciApp.setup  # noqa


def setup_with_cross_period_keys(abci_app: AbciApp) -> None:
    """Extend the setup to always include the cross-period keys.

    Hacky solution necessary for always setting the cross-period persisted keys
    and not raising an exception when the first period ends.
    This also protects us in case a round timeout is raised.

    :param abci_app: the abi app's instance.
    """
    # call the original setup method
    abci_app._setup()  # noqa

    # update the db to include all the cross-period persisted keys
    update = {
        db_key: abci_app.synchronized_data.db.get(db_key, None)
        for db_key in abci_app.cross_period_persisted_keys
    }
    abci_app.synchronized_data.db.update(**update)


# replace the setup method with the mocked version
TraderAbciApp.setup = setup_with_cross_period_keys  # type: ignore
