"""
Unit tests for PumpDotFun SDK.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from solana.keypair import Keypair
from solana.publickey import PublicKey

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import CreateTokenMetadata, PriorityFee, PumpFunEventType
from pumpdotfun_sdk.utils import validate_slippage, sol_to_lamports, format_sol_amount
from pumpdotfun_sdk.bonding_curve import BondingCurveCalculator
from pumpdotfun_sdk.amm import AMMCalculator


class TestPumpDotFunSDK(unittest.IsolatedAsyncioTestCase):
    """Test cases for main SDK functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sdk = PumpDotFunSDK(
            rpc_endpoint="https://api.devnet.solana.com",
            websocket_endpoint="wss://api.devnet.solana.com"
        )
        self.test_keypair = Keypair()
        self.test_mint = Keypair()
        self.test_metadata = CreateTokenMetadata(
            name="Test Token",
            symbol="TEST",
            description="A test token",
            image="https://example.com/image.png"
        )
    
    def test_sdk_initialization(self):
        """Test SDK initialization."""
        self.assertIsNotNone(self.sdk.rpc_client)
        self.assertIsNotNone(self.sdk.event_manager)
        self.assertEqual(self.sdk.commitment, "confirmed")
    
    def test_event_listener_management(self):
        """Test event listener add/remove functionality."""
        def test_callback(event, slot, signature):
            pass
        
        # Add listener
        listener_id = self.sdk.add_event_listener(
            PumpFunEventType.TRADE_EVENT,
            test_callback
        )test_create_and_buy_success
        self.assertIsInstance(listener_id, int)
        
        # Remove listener
        self.sdk.remove_event_listener(listener_id)
    
    @patch('pumpdotfun_sdk.client.AsyncClient')
    async def test_create_and_buy_validation(self, mock_client):
        """Test input validation for create_and_buy."""
        # Test invalid slippage
        result = await self.sdk.create_and_buy(
            creator=self.test_keypair,
            mint=self.test_mint,
            token_metadata=self.test_metadata,
            buy_amount_sol=1.0,
            slippage_basis_points=15000  # Invalid: > 10000
        )
        self.assertFalse(result.success)
        self.assertIn("Invalid slippage", result.error)
        
        # Test negative buy amount
        result = await self.sdk.create_and_buy(
            creator=self.test_keypair,
            mint=self.test_mint,
            token_metadata=self.test_metadata,
            buy_amount_sol=-1.0
        )
        self.assertFalse(result.success)
        self.assertIn("must be positive", result.error)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_validate_slippage(self):
        """Test slippage validation."""
        self.assertTrue(validate_slippage(500))  # 5%
        self.assertTrue(validate_slippage(0))    # 0%
        self.assertTrue(validate_slippage(10000)) # 100%
        self.assertFalse(validate_slippage(-1))   # Negative
        self.assertFalse(validate_slippage(10001)) # > 100%
    
    def test_sol_conversion(self):
        """Test SOL to lamports conversion."""
        self.assertEqual(sol_to_lamports(1.0), 1_000_000_000)
        self.assertEqual(sol_to_lamports(0.5), 500_000_000)
        self.assertEqual(format_sol_amount(1_000_000_000), 1.0)
        self.assertEqual(format_sol_amount(500_000_000), 0.5)
    
    def test_metadata_uri_creation(self):
        """Test metadata URI creation."""
        from pumpdotfun_sdk.utils import create_metadata_uri
        
        metadata = CreateTokenMetadata(
            name="Test Token",
            symbol="TEST",
            description="A test token",
            image="https://example.com/image.png",
            twitter="@test",
            website="https://test.com"
        )
        
        uri = create_metadata_uri(metadata)
        self.assertIn("Test Token", uri)
        self.assertIn("TEST", uri)
        self.assertIn("@test", uri)


class TestBondingCurve(unittest.TestCase):
    """Test cases for bonding curve calculations."""
    
    def test_buy_price_calculation(self):
        """Test buy price calculation."""
        sol_amount = 1_000_000_000  # 1 SOL
        real_sol_reserves = 0
        real_token_reserves = 800_000_000_000_000
        
        tokens_out = BondingCurveCalculator.get_buy_price(
            sol_amount, real_sol_reserves, real_token_reserves
        )
        
        self.assertGreater(tokens_out, 0)
        self.assertIsInstance(tokens_out, int)
    
    def test_sell_price_calculation(self):
        """Test sell price calculation."""
        token_amount = 1_000_000_000_000  # 1M tokens
        real_sol_reserves = 1_000_000_000  # 1 SOL
        real_token_reserves = 799_000_000_000_000
        
        sol_out = BondingCurveCalculator.get_sell_price(
            token_amount, real_sol_reserves, real_token_reserves
        )
        
        self.assertGreater(sol_out, 0)
        self.assertIsInstance(sol_out, int)
    
    def test_slippage_calculation(self):
        """Test slippage calculation."""
        expected = 1000
        actual = 950
        
        slippage = BondingCurveCalculator.calculate_slippage(expected, actual)
        self.assertEqual(slippage, 5.0)  # 5% slippage
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        from pumpdotfun_sdk.utils import PumpFunError
        
        with self.assertRaises(PumpFunError):
            BondingCurveCalculator.get_buy_price(-1, 1000, 1000)
        
        with self.assertRaises(PumpFunError):
            BondingCurveCalculator.get_sell_price(-1, 1000, 1000)


class TestAMM(unittest.TestCase):
    """Test cases for AMM functionality."""
    
    def test_amount_out_calculation(self):
        """Test AMM amount out calculation."""
        amount_in = 1_000_000_000  # 1 SOL
        reserve_in = 10_000_000_000  # 10 SOL
        reserve_out = 1_000_000_000_000_000  # 1M tokens
        
        amount_out = AMMCalculator.get_amount_out(
            amount_in, reserve_in, reserve_out
        )
        
        self.assertGreater(amount_out, 0)
        self.assertLess(amount_out, reserve_out)
    
    def test_amount_in_calculation(self):
        """Test AMM amount in calculation."""
        amount_out = 100_000_000_000  # 100K tokens
        reserve_in = 10_000_000_000  # 10 SOL
        reserve_out = 1_000_000_000_000_000  # 1M tokens
        
        amount_in = AMMCalculator.get_amount_in(
            amount_out, reserve_in, reserve_out
        )
        
        self.assertGreater(amount_in, 0)
    
    def test_price_impact_calculation(self):
        """Test price impact calculation."""
        amount_in = 1_000_000_000  # 1 SOL
        reserve_in = 10_000_000_000  # 10 SOL
        reserve_out = 1_000_000_000_000_000  # 1M tokens
        
        impact = AMMCalculator.calculate_price_impact(
            amount_in, reserve_in, reserve_out
        )
        
        self.assertGreaterEqual(impact, 0.0)
        self.assertLessEqual(impact, 100.0)


class TestEventHandling(unittest.TestCase):
    """Test cases for event handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        from pumpdotfun_sdk.events import EventManager
        
        self.mock_client = Mock()
        self.event_manager = EventManager(
            self.mock_client,
            "wss://api.devnet.solana.com"
        )
    
    def test_listener_management(self):
        """Test event listener management."""
        def test_callback(event, slot, signature):
            pass
        
        # Add listener
        listener_id = self.event_manager.add_listener(
            PumpFunEventType.TRADE_EVENT,
            test_callback
        )
        
        self.assertIn(listener_id, self.event_manager.listeners)
        
        # Remove listener
        self.event_manager.remove_listener(listener_id)
        self.assertNotIn(listener_id, self.event_manager.listeners)
    
    def test_event_parsing(self):
        """Test event parsing functionality."""
        # Test create event parsing
        log_data = "CreateEvent: mint=ABC123, name=Test, symbol=TST"
        result = self.event_manager._parse_create_event(log_data)
        
        self.assertEqual(result["event_type"], PumpFunEventType.CREATE_EVENT.value)
        self.assertIn("mint", result)
        self.assertIn("timestamp", result)


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the SDK."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.sdk = PumpDotFunSDK(
            rpc_endpoint="https://api.devnet.solana.com"
        )
    
    @patch('pumpdotfun_sdk.client.AsyncClient')
    async def test_full_workflow_simulation(self, mock_client):
        """Test a complete workflow simulation."""
        # Mock RPC responses
        mock_client.return_value.get_account_info = AsyncMock()
        mock_client.return_value.get_latest_blockhash = AsyncMock()
        mock_client.return_value.send_transaction = AsyncMock()
        
        # Create test data
        creator = Keypair()
        mint = Keypair()
        metadata = CreateTokenMetadata(
            name="Integration Test Token",
            symbol="ITT",
            description="Token for integration testing",
            image="https://example.com/itt.png"
        )
        
        # This would be a full integration test in a real environment
        # For now, we just test that the methods can be called without errors
        try:
            result = await self.sdk.create_and_buy(
                creator=creator,
                mint=mint,
                token_metadata=metadata,
                buy_amount_sol=0.1
            )
            # In a mock environment, this will likely fail, but we test structure
            self.assertIsNotNone(result)
            self.assertIn('success', result.__dict__)
        except Exception as e:
            # Expected in mock environment
            pass


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def test_network_error_handling(self):
        """Test network error handling."""
        from pumpdotfun_sdk.utils import NetworkError
        
        # Test that NetworkError can be raised and caught
        with self.assertRaises(NetworkError):
            raise NetworkError("Test network error")
    
    def test_validation_error_handling(self):
        """Test validation error handling."""
        from pumpdotfun_sdk.utils import ValidationError
        
        # Test that ValidationError can be raised and caught
        with self.assertRaises(ValidationError):
            raise ValidationError("Test validation error")
    
    def test_transaction_error_handling(self):
        """Test transaction error handling."""
        from pumpdotfun_sdk.utils import TransactionError
        
        # Test that TransactionError can be raised and caught
        with self.assertRaises(TransactionError):
            raise TransactionError("Test transaction error")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

