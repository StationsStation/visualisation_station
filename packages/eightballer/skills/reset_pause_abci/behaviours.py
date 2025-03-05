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

"""This module contains the behaviours for the 'reset_pause_abci' skill."""

import json
from abc import ABC
from typing import cast
from collections.abc import Generator

from packages.valory.skills.abstract_round_abci.base import BaseSynchronizedData
from packages.valory.skills.abstract_round_abci.models import TendermintRecoveryParams
from packages.eightballer.skills.reset_pause_abci.models import Params, SharedState
from packages.eightballer.skills.reset_pause_abci.rounds import (
    ResetPauseAbciApp,
    ResetAndPauseRound,
)
from packages.eightballer.skills.reset_pause_abci.payloads import ResetPausePayload
from packages.valory.skills.abstract_round_abci.behaviours import (
    BaseBehaviour,
    AbstractRoundBehaviour,
)


class ResetAndPauseBaseBehaviour(BaseBehaviour, ABC):
    """Reset behaviour."""

    @property
    def synchronized_data(self) -> BaseSynchronizedData:
        """Return the synchronized data."""
        return cast(
            BaseSynchronizedData,
            cast(SharedState, self.context.state).synchronized_data,
        )

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class ResetAndPauseBehaviour(ResetAndPauseBaseBehaviour):
    """Reset and pause behaviour."""

    matching_round = ResetAndPauseRound

    def async_act(self) -> Generator:
        """Do the action.

        Steps:
        - Trivially log the behaviour.
        - Sleep for configured interval.
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """
        # + 1 because `period_count` starts from 0
        n_periods_done = self.synchronized_data.period_count + 1
        reset_tm_nodes = n_periods_done % self.params.reset_tendermint_after == 0
        if reset_tm_nodes:
            tendermint_reset = yield from self.reset_tendermint_with_wait()
            if not tendermint_reset:
                return
        else:
            yield from self.wait_from_last_timestamp(self.params.reset_pause_duration)
        self.context.logger.info("Period end.")
        self.context.benchmark_tool.save(self.synchronized_data.period_count)

        payload = ResetPausePayload(self.context.agent_address, self.synchronized_data.period_count)
        yield from self.send_a2a_transaction(payload, reset_tm_nodes)
        yield from self.wait_until_round_end()
        self.set_done()

    def reset_tendermint_with_wait(  # pylint: disable=too-many-locals, too-many-statements
        self,
        on_startup: bool = False,
        is_recovery: bool = False,
    ) -> Generator[None, None, bool]:
        """Performs a hard reset (unsafe-reset-all) on the tendermint node."""
        yield from self._start_reset(on_startup=on_startup)
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            msg = "Error resetting tendermint node."
            raise RuntimeError(msg)

        if not self._is_healthy:
            self.context.logger.info(
                f"Resetting tendermint node at end of period={self.synchronized_data.period_count}."
            )

            backup_blockchain = self.round_sequence.blockchain
            self.round_sequence.reset_blockchain()
            reset_params = self._get_reset_params(on_startup)
            request_message, http_dialogue = self._build_http_request_message(
                "GET",
                self.params.tendermint_com_url + "/hard_reset",
                parameters=reset_params,
            )
            result = yield from self._do_request(request_message, http_dialogue)
            try:
                response = json.loads(result.body.decode())
                if response.get("status"):
                    self.context.logger.debug(response.get("message"))
                    self.context.logger.info("Resetting tendermint node successful!")
                    is_replay = response.get("is_replay", False)
                    if is_replay:
                        # in case of replay, the local blockchain should be set up differently.
                        self.round_sequence.reset_blockchain(is_replay=is_replay, is_init=True)
                    for handler_name in self.context.handlers.__dict__:
                        dialogues = getattr(self.context, f"{handler_name}_dialogues")
                        dialogues.cleanup()
                    if not is_recovery:
                        # in case of successful reset we store the reset params in the shared state,
                        # so that in the future if the communication with tendermint breaks, and we need to
                        # perform a hard reset to restore it, we can use these as the right ones
                        round_count = self.synchronized_data.db.round_count - 1
                        # in case we need to reset in order to recover agent <-> tm communication
                        # we store this round as the one to start from
                        restart_from_round = self.matching_round
                        self.shared_state.tm_recovery_params = TendermintRecoveryParams(
                            reset_params=reset_params,
                            round_count=round_count,
                            reset_from_round=restart_from_round.auto_round_id(),
                            serialized_db_state=self.shared_state.synchronized_data.db.serialize(),
                        )
                    self.round_sequence.abci_app.cleanup(
                        self.params.cleanup_history_depth,
                        self.params.cleanup_history_depth_current,
                    )
                    self._end_reset()

                else:
                    msg = response.get("message")
                    self.round_sequence.blockchain = backup_blockchain
                    self.context.logger.error(f"Error resetting: {msg}")
                    yield from self.sleep(self.params.sleep_time)
                    return False
            except json.JSONDecodeError:
                self.context.logger.exception("Error communicating with tendermint com server.")
                self.round_sequence.blockchain = backup_blockchain
                yield from self.sleep(self.params.sleep_time)
                return False

        status = yield from self._get_status()
        try:
            json_body = json.loads(status.body.decode())
        except json.JSONDecodeError:
            self.context.logger.exception("Tendermint not accepting transactions yet, trying again!")
            yield from self.sleep(self.params.sleep_time)
            return False

        remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
        local_height = self.round_sequence.height
        if local_height != remote_height:
            self.context.logger.warning(
                f"local height ({local_height}) != remote height ({remote_height}); retrying..."
            )
            yield from self.sleep(self.params.sleep_time)
            return False

        self.context.logger.info(f"local height == remote height == {local_height}; continuing execution...")
        self._is_healthy = False
        return True  # noqa


class ResetPauseABCIConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the reset_pause_abci app."""

    initial_behaviour_cls = ResetAndPauseBehaviour
    abci_app_cls = ResetPauseAbciApp
    behaviours: set[type[BaseBehaviour]] = {
        ResetAndPauseBehaviour,  # type: ignore
    }
