"""Base Custom Tests for test."""

import json
import subprocess
from pathlib import Path

import pytest
import requests
from web3 import Web3
from aea.test_tools.test_cases import AEATestCaseMany
from aea.configurations.constants import (
    LAUNCH_SUCCEED_MESSAGE,
    DEFAULT_PRIVATE_KEY_FILE,
)
from aea_test_autonomy.configurations import ANY_ADDRESS, DEFAULT_REQUESTS_TIMEOUT
from aea_test_autonomy.fixture_helpers import (
    UseTendermint,
    abci_host,
    abci_port,
    tendermint,
    ipfs_daemon,
    tendermint_port,
)


DEFAULT_ENCODING = "utf-8"
TENDERMINT_URL = "http://localhost:8080/hard_reset"
TERMINATION_TIMEOUT = 30
DEFAULT_LAUNCH_TIMEOUT = 30
AGENT_NAME = "frontend_agent"
AUTHOR = "eightballer"
VERSION = "0.1.0"
HANDLER_SUCCEED_MESSAGE = "Handler PingPongHandler loaded."


@pytest.mark.usefixtures("tendermint", "tendermint_port", "abci_host", "abci_port")
class TestAgentLaunch(AEATestCaseMany, UseTendermint):
    """Test that the Agent launches."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent

    def test_run(self) -> None:
        """Run the ABCI skill."""
        agent_name = "base"
        self.fetch_agent(
            f"{AUTHOR}/{AGENT_NAME}:{VERSION}", agent_name, is_local=self.IS_LOCAL
        )
        self.set_agent_context(agent_name)
        self.generate_private_key("ethereum")

        with open(
            f"{agent_name}/{DEFAULT_PRIVATE_KEY_FILE}", encoding=DEFAULT_ENCODING
        ) as f:
            self.eth_address = Web3().eth.account.from_key(f.read()).address

        self.add_private_key("ethereum", DEFAULT_PRIVATE_KEY_FILE)
        self._set_configs()

        self.invoke("issue-certificates")
        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"
        assert not self.missing_from_output(
            process, (HANDLER_SUCCEED_MESSAGE,), timeout=30, is_terminating=False
        ), "Custom handler is not loaded!"

        # Kill process
        process.kill()
        process.wait()

        # Terminate agents
        assert (
            self.terminate_agents(timeout=TERMINATION_TIMEOUT) is None
        ), "Failed to terminate agents within timeout"

    @classmethod
    def is_running(
        cls, process: subprocess.Popen, timeout: int = DEFAULT_LAUNCH_TIMEOUT
    ) -> bool:
        """Check if the AEA is launched and running (ready to process messages).

        :param process: agent subprocess.
        :param timeout: the timeout to wait for launch to complete
        :return: bool indicating status
        """
        missing_strings = cls.missing_from_output(
            process, (LAUNCH_SUCCEED_MESSAGE,), timeout, is_terminating=False
        )

        return missing_strings == []

    def _set_configs(self) -> None:
        """Set the current agent's config overrides."""

        self.set_config(
            f"vendor.{AUTHOR}.skills.trader_abci.models.params.args.setup.all_participants",
            json.dumps([self.eth_address]),
            "list",
        )
        self.set_config(
            "vendor.valory.connections.abci.config.host",
            ANY_ADDRESS,
        )
        self.set_config(
            "vendor.valory.connections.abci.config.port",
            self.abci_port,
        )
