import unittest
import asyncio
import base58

from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solana.keypair import Keypair

from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import CreateTokenMetadata


DEVNET_PUBLIC_KEY = "GkgkJyLRB5gWHxvv1MrAUefLAF7S9c17593sYnwXAdwp"
DEVNET_SECRET_BASE58 = "5QYZkjJ1PShm8YeUaxiwWvFzfazJ3irpmwwJh9zJ6aHdg3vDDvhoeS1v1hKQxuRfCu94R3gVCVVWMLjoYss5MM94"


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


class TestDevnetIntegration(unittest.IsolatedAsyncioTestCase):
    """Run a simulated create-buy-sell flow on devnet."""

    async def asyncSetUp(self):
        self.sdk = PumpDotFunSDK("https://api.devnet.solana.com")
        secret = base58.b58decode(DEVNET_SECRET_BASE58)
        self.creator = Keypair.from_secret_key(secret)
        self.mint = Keypair()

    async def asyncTearDown(self):
        await self.sdk.close()

    async def test_create_buy_sell_flow(self):
        metadata = CreateTokenMetadata(
            name="E2E Token",
            symbol="E2E",
            description="Integration test token",
            image="https://example.com/image.png",
        )

        buy_res = await self.sdk.create_and_buy(
            creator=self.creator,
            mint=self.mint,
            token_metadata=metadata,
            buy_amount_sol=0.000001,
            simulate=True,
        )
        self.assertTrue(buy_res.success, buy_res.error)

        sell_res = await self.sdk.sell(
            seller=self.creator,
            mint=self.mint.public_key,
            sell_token_amount=1_000_000,
            simulate=True,
            mint_authority=self.mint,
        )
        self.assertTrue(sell_res.success, sell_res.error)

        print(
            f"Mint: {buy_res.results['mint']}\n"
            f"Create: {buy_res.results['create_signature']}\n"
            f"Buy: {buy_res.results['buy_signature']}\n"
            f"Sell: {sell_res.signature}"
        )

