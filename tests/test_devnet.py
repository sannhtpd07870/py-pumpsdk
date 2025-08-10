"""Integration test against Solana devnet."""

import unittest
import asyncio

from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey


DEVNET_PUBLIC_KEY = "GkgkJyLRB5gWHxvv1MrAUefLAF7S9c17593sYnwXAdwp"


class TestDevnetConnectivity(unittest.TestCase):
    """Verify that the Solana devnet is reachable."""

    def test_get_balance(self):
        async def run_test():
            client = AsyncClient("https://api.devnet.solana.com")
            resp = await client.get_balance(PublicKey(DEVNET_PUBLIC_KEY))
            await client.close()
            return resp.value

        balance = asyncio.run(run_test())
        self.assertIsInstance(balance, int)

