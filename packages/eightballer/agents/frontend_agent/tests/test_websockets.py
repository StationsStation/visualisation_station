"""Tests for websocket functionality."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Generator
import time
import contextlib

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
from aea_test_autonomy.fixture_helpers import ( # noqa: F401
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

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.usefixtures("tendermint_function", "tendermint_port", "abci_host", "abci_port")
class TestWebsocketIntegration(AEATestCaseMany, UseTendermint):
    """Test websocket functionality."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "INFO"]

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
            process = await self.setup_agent()

            assert not self.missing_from_output(
                process, ("UI behaviours",), timeout=30, is_terminating=False
            ), "UI Handler not loaded within timeout!"

            async with websockets.connect(
                f"ws://localhost:{WS_PORT}/ws",
                timeout=10,
                close_timeout=5,
            ) as websocket:
                # Test basic message
                test_message = {"type": "test", "data": "hello"}
                await websocket.send(json.dumps(test_message))

                # Wait for Pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                assert "Pong" in response

                # Send agent-info request
                await websocket.send(json.dumps({"type": "agent-info"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                assert "Pong" in response

                # Test complete
                return

        finally:
            if process:
                process.terminate()

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.usefixtures("tendermint_function", "tendermint_port", "abci_host", "abci_port")
class TestWebsocketConnectionManagement(AEATestCaseMany, UseTendermint):
    """Test websocket functionality."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "INFO"]

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

    async def test_websocket_connection_management(self):
        """Test websocket connection handling."""
        process = None
        try:
            process = await self.setup_agent()

            assert not self.missing_from_output(
                process, ("UI behaviours",), timeout=30, is_terminating=False
            ), "UI Handler not loaded within timeout!"

            # Test connection close handling
            ws = await websockets.connect(f"ws://localhost:{WS_PORT}/ws")
            await ws.close()

            # Test reconnection works
            async with websockets.connect(f"ws://localhost:{WS_PORT}/ws") as ws:
                await ws.send(json.dumps({"type": "test"}))
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                assert "Pong" in response

        finally:
            if process:
                process.terminate()

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.usefixtures("tendermint_function", "tendermint_port", "abci_host", "abci_port")
class TestWebsocketMultipleConnections(AEATestCaseMany, UseTendermint):
    """Test websocket functionality."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "INFO"]

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

    async def test_multiple_websocket_clients(self):
        """Test multiple websocket clients receive messages."""
        process = None
        try:
            process = await self.setup_agent()
            
            assert not self.missing_from_output(
                process, ("UI behaviours",), timeout=30, is_terminating=False
            ), "UI Handler not loaded within timeout!"

            # Connect both clients using async context manager
            async with contextlib.AsyncExitStack() as stack:
                clients = [
                    await stack.enter_async_context(
                        websockets.connect(
                            f"ws://localhost:{WS_PORT}/ws",
                            ping_interval=20,
                            ping_timeout=20
                        )
                    ) for _ in range(2)
                ]
                
                # Send test messages
                await asyncio.sleep(1)  # Ensure connections
                test_msg = json.dumps({"type": "test", "data": "hello"})
                await asyncio.gather(*[client.send(test_msg) for client in clients])
                
                # Collect responses with timeout
                responses = {i: [] for i in range(2)}
                async with asyncio.TaskGroup() as tg:
                    async def collect(client_id):
                        try:
                            while True:
                                msg = await clients[client_id].recv()
                                responses[client_id].append(msg)
                                if "Pong" in msg:
                                    break
                        except Exception as e:
                            logging.error(f"Client {client_id} error: {e}")
                    
                    for i in range(2):
                        tg.create_task(collect(i))
                
                # Verify responses
                assert all(any("Pong" in msg for msg in msgs) 
                          for msgs in responses.values()), \
                    f"Not all clients received Pong: {responses}"
                
        finally:
            if process:
                process.terminate()

