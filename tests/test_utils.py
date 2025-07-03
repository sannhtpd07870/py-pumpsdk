"""
Unit tests for utility functions.
"""

import unittest
import json
import time
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pumpdotfun_sdk.utils import (
    create_metadata_uri,
    validate_slippage,
    format_sol_amount,
    format_token_amount,
    sol_to_lamports,
    calculate_slippage_amount,
    encode_instruction_data,
    decode_account_data,
    PumpFunError,
    TransactionError,
    ValidationError,
    NetworkError
)
from pumpdotfun_sdk.types import CreateTokenMetadata


class TestMetadataUtils(unittest.TestCase):
    """Test metadata utility functions."""
    
    def test_create_metadata_uri_basic(self):
        """Test basic metadata URI creation."""
        metadata = CreateTokenMetadata(
            name="Test Token",
            symbol="TEST",
            description="A test token for testing",
            image="https://example.com/test.png"
        )
        
        uri = create_metadata_uri(metadata)
        parsed = json.loads(uri)
        
        self.assertEqual(parsed["name"], "Test Token")
        self.assertEqual(parsed["symbol"], "TEST")
        self.assertEqual(parsed["description"], "A test token for testing")
        self.assertEqual(parsed["image"], "https://example.com/test.png")
        self.assertTrue(parsed["showName"])
        self.assertIn("createdOn", parsed)
    
    def test_create_metadata_uri_with_socials(self):
        """Test metadata URI creation with social links."""
        metadata = CreateTokenMetadata(
            name="Social Token",
            symbol="SOC",
            description="Token with social links",
            image="https://example.com/social.png",
            twitter="@socialtoken",
            telegram="https://t.me/socialtoken",
            website="https://socialtoken.com"
        )
        
        uri = create_metadata_uri(metadata)
        parsed = json.loads(uri)
        
        self.assertEqual(parsed["twitter"], "@socialtoken")
        self.assertEqual(parsed["telegram"], "https://t.me/socialtoken")
        self.assertEqual(parsed["website"], "https://socialtoken.com")
    
    def test_create_metadata_uri_minimal(self):
        """Test metadata URI creation with minimal data."""
        metadata = CreateTokenMetadata(
            name="Min Token",
            symbol="MIN",
            description="Minimal token",
            image="https://example.com/min.png",
            show_name=False
        )
        
        uri = create_metadata_uri(metadata)
        parsed = json.loads(uri)
        
        self.assertFalse(parsed["showName"])
        self.assertNotIn("twitter", parsed)
        self.assertNotIn("telegram", parsed)
        self.assertNotIn("website", parsed)


class TestValidationUtils(unittest.TestCase):
    """Test validation utility functions."""
    
    def test_validate_slippage_valid_values(self):
        """Test slippage validation with valid values."""
        self.assertTrue(validate_slippage(0))      # 0%
        self.assertTrue(validate_slippage(100))    # 1%
        self.assertTrue(validate_slippage(500))    # 5%
        self.assertTrue(validate_slippage(1000))   # 10%
        self.assertTrue(validate_slippage(5000))   # 50%
        self.assertTrue(validate_slippage(10000))  # 100%
    
    def test_validate_slippage_invalid_values(self):
        """Test slippage validation with invalid values."""
        self.assertFalse(validate_slippage(-1))     # Negative
        self.assertFalse(validate_slippage(-100))   # Negative
        self.assertFalse(validate_slippage(10001))  # > 100%
        self.assertFalse(validate_slippage(20000))  # > 100%


class TestConversionUtils(unittest.TestCase):
    """Test conversion utility functions."""
    
    def test_sol_to_lamports_conversion(self):
        """Test SOL to lamports conversion."""
        self.assertEqual(sol_to_lamports(0), 0)
        self.assertEqual(sol_to_lamports(1), 1_000_000_000)
        self.assertEqual(sol_to_lamports(0.5), 500_000_000)
        self.assertEqual(sol_to_lamports(2.5), 2_500_000_000)
        self.assertEqual(sol_to_lamports(0.001), 1_000_000)
    
    def test_format_sol_amount_conversion(self):
        """Test lamports to SOL formatting."""
        self.assertEqual(format_sol_amount(0), 0.0)
        self.assertEqual(format_sol_amount(1_000_000_000), 1.0)
        self.assertEqual(format_sol_amount(500_000_000), 0.5)
        self.assertEqual(format_sol_amount(2_500_000_000), 2.5)
        self.assertEqual(format_sol_amount(1_000_000), 0.001)
    
    def test_format_token_amount(self):
        """Test token amount formatting."""
        self.assertEqual(format_token_amount(1_000_000, 6), 1.0)
        self.assertEqual(format_token_amount(500_000, 6), 0.5)
        self.assertEqual(format_token_amount(1_000_000_000, 9), 1.0)
        self.assertEqual(format_token_amount(123_456_789, 6), 123.456789)
    
    def test_round_trip_conversions(self):
        """Test round-trip conversions."""
        original_sol = 1.5
        lamports = sol_to_lamports(original_sol)
        converted_back = format_sol_amount(lamports)
        self.assertEqual(original_sol, converted_back)


class TestSlippageUtils(unittest.TestCase):
    """Test slippage calculation utilities."""
    
    def test_calculate_slippage_amount_minimum(self):
        """Test minimum slippage amount calculation."""
        expected = 1000
        slippage_bp = 500  # 5%
        
        minimum = calculate_slippage_amount(expected, slippage_bp, is_minimum=True)
        self.assertEqual(minimum, 950)  # 1000 - 5% = 950
    
    def test_calculate_slippage_amount_maximum(self):
        """Test maximum slippage amount calculation."""
        expected = 1000
        slippage_bp = 500  # 5%
        
        maximum = calculate_slippage_amount(expected, slippage_bp, is_minimum=False)
        self.assertEqual(maximum, 1050)  # 1000 + 5% = 1050
    
    def test_calculate_slippage_amount_edge_cases(self):
        """Test slippage calculation edge cases."""
        # Zero slippage
        result = calculate_slippage_amount(1000, 0, is_minimum=True)
        self.assertEqual(result, 1000)
        
        # Maximum slippage (100%)
        result = calculate_slippage_amount(1000, 10000, is_minimum=True)
        self.assertEqual(result, 0)
        
        # Small amounts
        result = calculate_slippage_amount(1, 500, is_minimum=True)
        self.assertEqual(result, 0)  # Rounds down to 0


class TestDataEncodingUtils(unittest.TestCase):
    """Test data encoding/decoding utilities."""
    
    def test_encode_instruction_data(self):
        """Test instruction data encoding."""
        data = {
            "instruction": "buy",
            "amount": 1000000000,
            "slippage": 500
        }
        
        encoded = encode_instruction_data(data)
        self.assertIsInstance(encoded, bytes)
        
        # Should be valid JSON when decoded
        decoded_str = encoded.decode('utf-8')
        decoded_data = json.loads(decoded_str)
        self.assertEqual(decoded_data["instruction"], "buy")
        self.assertEqual(decoded_data["amount"], 1000000000)
    
    def test_decode_account_data(self):
        """Test account data decoding."""
        import base64
        
        # Create test data
        test_data = b"test account data"
        encoded_data = base64.b64encode(test_data).decode('ascii')
        
        decoded = decode_account_data(encoded_data)
        self.assertIn("raw_data", decoded)
        self.assertEqual(decoded["raw_data"], test_data)
    
    def test_decode_account_data_invalid(self):
        """Test account data decoding with invalid input."""
        # Invalid base64
        decoded = decode_account_data("invalid_base64!")
        self.assertEqual(decoded, {})


class TestErrorClasses(unittest.TestCase):
    """Test custom error classes."""
    
    def test_pump_fun_error(self):
        """Test PumpFunError class."""
        error = PumpFunError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)
    
    def test_transaction_error(self):
        """Test TransactionError class."""
        error = TransactionError("Transaction failed")
        self.assertEqual(str(error), "Transaction failed")
        self.assertIsInstance(error, PumpFunError)
        self.assertIsInstance(error, Exception)
    
    def test_validation_error(self):
        """Test ValidationError class."""
        error = ValidationError("Invalid input")
        self.assertEqual(str(error), "Invalid input")
        self.assertIsInstance(error, PumpFunError)
        self.assertIsInstance(error, Exception)
    
    def test_network_error(self):
        """Test NetworkError class."""
        error = NetworkError("Network connection failed")
        self.assertEqual(str(error), "Network connection failed")
        self.assertIsInstance(error, PumpFunError)
        self.assertIsInstance(error, Exception)


class TestAsyncUtils(unittest.TestCase):
    """Test async utility functions."""
    
    @patch('pumpdotfun_sdk.utils.asyncio.sleep')
    async def test_wait_for_confirmation_success(self, mock_sleep):
        """Test successful transaction confirmation."""
        from pumpdotfun_sdk.utils import wait_for_confirmation
        
        # Mock successful confirmation
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.value = [Mock()]
        mock_response.value[0].confirmation_status = Mock()
        mock_response.value[0].confirmation_status.value = 1
        mock_client.get_signature_statuses.return_value = mock_response
        
        result = await wait_for_confirmation(
            mock_client, "test_signature", "confirmed", timeout=5
        )
        
        self.assertTrue(result)
    
    @patch('pumpdotfun_sdk.utils.asyncio.sleep')
    async def test_wait_for_confirmation_timeout(self, mock_sleep):
        """Test transaction confirmation timeout."""
        from pumpdotfun_sdk.utils import wait_for_confirmation
        
        # Mock no confirmation
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.value = [None]
        mock_client.get_signature_statuses.return_value = mock_response
        
        result = await wait_for_confirmation(
            mock_client, "test_signature", "confirmed", timeout=1
        )
        
        self.assertFalse(result)
    
    @patch('pumpdotfun_sdk.utils.asyncio.sleep')
    async def test_wait_for_confirmation_error(self, mock_sleep):
        """Test transaction confirmation with RPC error."""
        from pumpdotfun_sdk.utils import wait_for_confirmation
        
        # Mock RPC error
        mock_client = AsyncMock()
        mock_client.get_signature_statuses.side_effect = Exception("RPC Error")
        
        result = await wait_for_confirmation(
            mock_client, "test_signature", "confirmed", timeout=1
        )
        
        self.assertFalse(result)


class TestUtilityIntegration(unittest.TestCase):
    """Integration tests for utility functions."""
    
    def test_metadata_and_validation_integration(self):
        """Test integration between metadata creation and validation."""
        # Create valid metadata
        metadata = CreateTokenMetadata(
            name="Integration Token",
            symbol="INT",
            description="Token for integration testing",
            image="https://example.com/int.png"
        )
        
        # Create URI
        uri = create_metadata_uri(metadata)
        
        # Validate the URI is valid JSON
        try:
            parsed = json.loads(uri)
            self.assertIsInstance(parsed, dict)
            self.assertIn("name", parsed)
            self.assertIn("symbol", parsed)
        except json.JSONDecodeError:
            self.fail("Generated URI is not valid JSON")
    
    def test_slippage_and_conversion_integration(self):
        """Test integration between slippage and conversion utilities."""
        # Test workflow: SOL -> lamports -> apply slippage -> back to SOL
        original_sol = 1.0
        lamports = sol_to_lamports(original_sol)
        
        # Apply 5% slippage
        min_lamports = calculate_slippage_amount(lamports, 500, is_minimum=True)
        max_lamports = calculate_slippage_amount(lamports, 500, is_minimum=False)
        
        # Convert back to SOL
        min_sol = format_sol_amount(min_lamports)
        max_sol = format_sol_amount(max_lamports)
        
        self.assertEqual(min_sol, 0.95)  # 1.0 - 5%
        self.assertEqual(max_sol, 1.05)  # 1.0 + 5%
        
        # Validate slippage values
        self.assertTrue(validate_slippage(500))


if __name__ == '__main__':
    unittest.main(verbosity=2)

