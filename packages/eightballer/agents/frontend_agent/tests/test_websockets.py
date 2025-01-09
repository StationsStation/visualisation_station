"""Tests for websocket functionality."""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Generator
import time

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

            # Connect two clients with keep_alive
            async with websockets.connect(
                f"ws://localhost:{WS_PORT}/ws",
                ping_interval=20,
                ping_timeout=20
            ) as ws1, websockets.connect(
                f"ws://localhost:{WS_PORT}/ws",
                ping_interval=20,
                ping_timeout=20
            ) as ws2:
                
                # Ensure connections are established
                await asyncio.sleep(1)
                
                # Send test messages from both clients
                test_msg = {"type": "test", "data": "hello"}
                await ws1.send(json.dumps(test_msg))
                await ws2.send(json.dumps(test_msg))
                
                # Use a queue to collect messages
                message_queue = asyncio.Queue()
                
                async def collect_messages(websocket, queue, client_id):
                    try:
                        while True:
                            msg = await websocket.recv()
                            logging.debug(f"Client {client_id} received: {msg}")
                            await queue.put((client_id, msg))
                    except websockets.exceptions.ConnectionClosed:
                        logging.warning(f"Client {client_id} connection closed")
                    except Exception as e:
                        logging.error(f"Error collecting messages for client {client_id}: {e}")
                
                # Start collectors
                collectors = [
                    asyncio.create_task(collect_messages(ws1, message_queue, 1)),
                    asyncio.create_task(collect_messages(ws2, message_queue, 2))
                ]
                
                # Collect messages for 3 seconds
                messages_by_client = {1: [], 2: []}
                try:
                    end_time = time.time() + 3
                    while time.time() < end_time:
                        try:
                            client_id, msg = await asyncio.wait_for(
                                message_queue.get(), 
                                timeout=0.1
                            )
                            messages_by_client[client_id].append(msg)
                            # If both clients have received Pong, we can break early
                            if all(any("Pong" in m for m in messages_by_client[i]) for i in [1, 2]):
                                break
                        except asyncio.TimeoutError:
                            continue
                finally:
                    # Cleanup collectors
                    for collector in collectors:
                        collector.cancel()
                    
                # Log all received messages for debugging
                for client_id, messages in messages_by_client.items():
                    logging.info(f"Client {client_id} messages: {messages}")
                    
                # Verify messages
                assert any("Pong" in msg for msg in messages_by_client[1]), \
                    f"Client 1 didn't receive Pong. Got: {messages_by_client[1]}"
                assert any("Pong" in msg for msg in messages_by_client[2]), \
                    f"Client 2 didn't receive Pong. Got: {messages_by_client[2]}"
                
        finally:
            if process:
                process.terminate()

