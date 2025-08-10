"""Tests for recently fixed bugs."""

import unittest
import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

from solana.publickey import PublicKey

from pumpdotfun_sdk.utils import wait_for_confirmation
from pumpdotfun_sdk.events import EventManager
from pumpdotfun_sdk.global_account import GlobalAccountManager, GlobalAccountData


class TestWaitForConfirmation(unittest.TestCase):
    """Ensure wait_for_confirmation handles string statuses."""

    def test_confirmation_status_string(self):
        async def run_test():
            mock_client = AsyncMock()
            status = SimpleNamespace(confirmation_status="finalized")
            mock_client.get_signature_statuses.return_value = SimpleNamespace(value=[status])
            return await wait_for_confirmation(mock_client, "sig", commitment="confirmed", timeout=1)

        result = asyncio.run(run_test())
        self.assertTrue(result)


class TestParseLogMessage(unittest.TestCase):
    """Ensure EventManager parses dict-based messages."""

    def test_dict_message_parsing(self):
        manager = EventManager(AsyncMock(), "wss://example.com")
        message = {"result": {"logs": ["Program log: CreateEvent"]}}
        event_data = manager._parse_log_message(message)
        self.assertIsNotNone(event_data)
        self.assertEqual(event_data["event_type"], "createEvent")


class TestGlobalAccountManager(unittest.TestCase):
    """Ensure global account data handles base64 encoded responses."""

    def test_base64_decoding(self):
        raw = b"\x00" * 200
        encoded = base64.b64encode(raw).decode("utf-8")

        mock_client = AsyncMock()
        account_info = SimpleNamespace(value=SimpleNamespace(data=[encoded, "base64"]))
        mock_client.get_account_info.return_value = account_info

        manager = GlobalAccountManager(mock_client, PublicKey("11111111111111111111111111111111"))

        async def run_test():
            return await manager.fetch_global_account_data(force_refresh=True)

        data = asyncio.run(run_test())
        self.assertIsInstance(data, GlobalAccountData)

