"""Tests for websocket functionality."""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Generator

import docker
import pytest
import websockets
from aea.configurations.constants import (
    LAUNCH_SUCCEED_MESSAGE,
    DEFAULT_PRIVATE_KEY_FILE,
)
from aea.test_tools.test_cases import AEATestCaseMany
from aea_test_autonomy.configurations import ANY_ADDRESS
from aea_test_autonomy.docker.base import launch_image
from aea_test_autonomy.docker.tendermint import TendermintDockerImage
from aea_test_autonomy.fixture_helpers import (
    UseTendermint,
    abci_host,
    abci_port,
    tendermint,
    tendermint_port,
)
from web3 import Web3

logging.basicConfig(level=logging.DEBUG)

DEFAULT_ENCODING = "utf-8"
TERMINATION_TIMEOUT = 30
DEFAULT_LAUNCH_TIMEOUT = 30
AGENT_NAME = "frontend_agent"
AUTHOR = "eightballer"
VERSION = "0.1.0"
WS_PORT = 5556

@pytest.fixture(scope="function")
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

async def wait_for_log_message(process: asyncio.subprocess.Process, target_message: str, timeout: int = 30):
    """Wait until `target_message` appears in the log or until timeout."""
    start_time = asyncio.get_event_loop().time()
    print(f"Starting to wait for '{target_message}' (timeout: {timeout}s)")

    while (asyncio.get_event_loop().time() - start_time) < timeout:
        try:
            # Read line without creating a new task
            line = await process.stdout.readline()
            if not line:
                break

            decoded_line = line.decode("utf-8", errors="replace").rstrip("\n")
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"[{elapsed:.1f}s] Agent log: {decoded_line}")

            if target_message in decoded_line:
                print(f"Found target message after {elapsed:.1f} seconds")
                return True

        except Exception as e:
            print(f"Error reading process output: {e}")
            await asyncio.sleep(0.1)  # Don't break, just continue after error
            continue

    elapsed = asyncio.get_event_loop().time() - start_time
    raise asyncio.TimeoutError(f"Did not see '{target_message}' in logs after {elapsed:.1f} seconds")

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.usefixtures("tendermint_function", "tendermint_port", "abci_host", "abci_port")
class TestWebsocketIntegration(AEATestCaseMany, UseTendermint):
    """Test websocket functionality."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]

    async def setup_agent(self):
        """Set up the agent for testing."""
        agent_name = "websocket_test"
        self.fetch_agent(
            f"{AUTHOR}/{AGENT_NAME}:{VERSION}",
            agent_name,
            is_local=self.IS_LOCAL
        )
        self.set_agent_context(agent_name)

        # Generate and configure keys
        self.generate_private_key("ethereum")

        with open(
            f"{agent_name}/{DEFAULT_PRIVATE_KEY_FILE}", encoding=DEFAULT_ENCODING
            ) as f:
                self.eth_address = Web3().eth.account.from_key(f.read()).address

        self.add_private_key("ethereum", DEFAULT_PRIVATE_KEY_FILE)

        # Configure agent
        self.set_config(
            f"vendor.{AUTHOR}.skills.trader_abci.models.params.args.setup.all_participants",
            json.dumps([self.eth_address]),
            "list",
        )
        self.set_config("vendor.valory.connections.abci.config.host", ANY_ADDRESS)
        self.set_config("vendor.valory.connections.abci.config.port", self.abci_port)

        # Start agent
        self.invoke("issue-certificates")
        process = self.run_agent()
        assert self.is_running(process), "Agent failed to start!"
        return process

    async def test_websocket_connection(self):
        """Test basic websocket connection."""
        process = None
        try:
            logging.debug("Setting up test agent...")
            process = await self.setup_agent()

            assert not self.missing_from_output(
                process, ("UI behaviours",), timeout=30, is_terminating=False
            ), "UI Handler not loaded within timeout!"

            # Attempt to connect to the websocket
            logging.debug("Connecting to WebSocket on ws://localhost:%s/ws", WS_PORT)
            async with websockets.connect(
                f"ws://localhost:{WS_PORT}/ws",
                timeout=10,
                close_timeout=5,
            ) as websocket:

                # Log the initial connection state
                logging.debug("Initial WebSocket state: %s", websocket.state)

                # 1. Test basic message
                test_message = {"type": "test", "data": "hello"}
                logging.debug("Sending test message: %s", test_message)
                await websocket.send(json.dumps(test_message))

                # Wait for Pong response
                start_time = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - start_time) < 10:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    logging.debug("Received response: %s", response)
                    if "Pong" in response:
                        break
                else:
                    pytest.fail("No valid Pong response received within timeout")

                # Verify connection is still open before proceeding
                if websocket.closed:
                    pytest.fail("WebSocket closed unexpectedly after Pong")

                # 2. Test agent info request (only after successful Pong)
                agent_info_request = {"type": "agent-info"}
                logging.debug("Sending agent-info request: %s", agent_info_request)
                await websocket.send(json.dumps(agent_info_request))

                start_time = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - start_time) < 10:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20)
                    logging.debug("Received agent-info response: %s", response)
                    
                    try:
                        data = json.loads(response)
                        if isinstance(data, dict) and "agent-address" in data:
                            assert "agent-status" in data
                            break
                    except json.JSONDecodeError:
                        continue
                else:
                    pytest.fail("No valid agent-info response received within timeout")

        finally:
            if process:
                logging.debug("Terminating agent process...")
                process.terminate()
                try:
                    assert (
                        self.terminate_agents(timeout=TERMINATION_TIMEOUT) is None
                    ), f"Failed to terminate agents within timeout for {AUTHOR}/{AGENT_NAME}"
                except Exception as e:
                    logging.error("Error during agent termination: %s", e, exc_info=True)
