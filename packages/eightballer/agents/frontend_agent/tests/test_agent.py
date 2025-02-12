"""Base Custom Tests for test."""

import json
import subprocess
from pathlib import Path
from collections.abc import Generator

import yaml
import docker
import pytest
from web3 import Web3
from aea.configurations.base import PublicId, ComponentType
from aea.configurations.loader import load_component_configuration
from aea.test_tools.test_cases import AEATestCaseMany
from aea.configurations.constants import (
    LAUNCH_SUCCEED_MESSAGE,
    DEFAULT_PRIVATE_KEY_FILE,
)
from aea_test_autonomy.docker.base import launch_image
from aea_test_autonomy.configurations import ANY_ADDRESS
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseTendermint,
    abci_host,
    abci_port,
    tendermint,
    ipfs_daemon,
    tendermint_port,
)
from aea_test_autonomy.docker.tendermint import TendermintDockerImage


DEFAULT_ENCODING = "utf-8"
TERMINATION_TIMEOUT = 30
HANDLER_LOAD_TIMEOUT = 30
DEFAULT_LAUNCH_TIMEOUT = 30
AGENT_NAME = "frontend_agent"
AUTHOR = "eightballer"
VERSION = "0.1.0"


@pytest.fixture
def tendermint_function(
    tendermint_port: int,  # noqa: F811
    abci_host: str,  # noqa: F811
    abci_port: int,  # noqa: F811
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    client = docker.from_env()
    image = TendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.usefixtures("tendermint_function", "tendermint_port", "abci_host", "abci_port")
class TestAgentLaunch(AEATestCaseMany, UseTendermint):
    """Test that the Agent launches."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent

    @staticmethod
    def load_custom_components():
        config_path = Path(__file__).parent.parent / "aea-config.yaml"
        with open(config_path, encoding=DEFAULT_ENCODING) as f:
            configs = list(yaml.safe_load_all(f))
            main_config = configs[0]

            components = []
            for custom_id in main_config.get("customs", []):
                public_id = PublicId.from_str(custom_id)

                component_config = load_component_configuration(
                    ComponentType.CUSTOM,
                    Path(__file__).parent.parent.parent.parent.parent / public_id.author / "customs" / public_id.name,
                )

                handler_class = component_config.json["handlers"][0]["class_name"]
                components.append((public_id.author, public_id.name, handler_class))

            return components

    @pytest.mark.parametrize(("author", "component", "handler_class"), load_custom_components())
    def test_run(self, author: str, component: str, handler_class: str) -> None:
        """Run the ABCI skill with different custom components."""
        agent_name = f"base_{author}_{component}"
        self.fetch_agent(f"{AUTHOR}/{AGENT_NAME}:{VERSION}", agent_name, is_local=self.IS_LOCAL)
        self.set_agent_context(agent_name)
        self.generate_private_key("ethereum")

        with open(f"{agent_name}/{DEFAULT_PRIVATE_KEY_FILE}", encoding=DEFAULT_ENCODING) as f:
            self.eth_address = Web3().eth.account.from_key(f.read()).address

        self.add_private_key("ethereum", DEFAULT_PRIVATE_KEY_FILE)

        self.set_config(
            f"vendor.{AUTHOR}.skills.trader_abci.models.params.args.user_interface.custom_component",
            f"{author}/{component}",
        )

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

        self.invoke("issue-certificates")
        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, f"AEA not running within timeout for {author}/{component}!"

        expected_message = f"Handler {handler_class} loaded."
        assert not self.missing_from_output(
            process,
            [expected_message],
            timeout=HANDLER_LOAD_TIMEOUT,
            is_terminating=False,
        ), f"Custom handler is not loaded for {author}/{component}!"

        process.terminate()

        assert (
            self.terminate_agents(timeout=TERMINATION_TIMEOUT) is None
        ), f"Failed to terminate agents within timeout for {author}/{component}"

    @classmethod
    def is_running(cls, process: subprocess.Popen, timeout: int = DEFAULT_LAUNCH_TIMEOUT) -> bool:
        """Check if the AEA is launched and running (ready to process messages).

        :param process: agent subprocess.
        :param timeout: the timeout to wait for launch to complete
        :return: bool indicating status
        """
        missing_strings = cls.missing_from_output(process, (LAUNCH_SUCCEED_MESSAGE,), timeout, is_terminating=False)

        return missing_strings == []
