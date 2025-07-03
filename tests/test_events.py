"""
Unit tests for event handling functionality.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pumpdotfun_sdk.events import EventManager
from pumpdotfun_sdk.types import PumpFunEventType, CreateEvent, TradeEvent, CompleteEvent
from solders.pubkey import Pubkey as PublicKey


class TestEventManager(unittest.TestCase):
    """Test cases for EventManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.websocket_url = "wss://api.devnet.solana.com"
        self.event_manager = EventManager(self.mock_client, self.websocket_url)
    
    def test_initialization(self):
        """Test EventManager initialization."""
        self.assertEqual(self.event_manager.rpc_client, self.mock_client)
        self.assertEqual(self.event_manager.websocket_url, self.websocket_url)
        self.assertEqual(self.event_manager.listeners, {})
        self.assertEqual(self.event_manager.next_id, 1)
        self.assertFalse(self.event_manager.is_listening)
        self.assertIsNone(self.event_manager.websocket_connection)
        self.assertIsNone(self.event_manager.listen_task)
    
    def test_add_listener(self):
        """Test adding event listeners."""
        def test_callback(event, slot, signature):
            pass
        
        # Add first listener
        listener_id = self.event_manager.add_listener(
            PumpFunEventType.CREATE_EVENT,
            test_callback
        )
        
        self.assertEqual(listener_id, 1)
        self.assertIn(listener_id, self.event_manager.listeners)
        self.assertEqual(
            self.event_manager.listeners[listener_id]["event_type"],
            PumpFunEventType.CREATE_EVENT
        )
        self.assertEqual(
            self.event_manager.listeners[listener_id]["callback"],
            test_callback
        )
        
        # Add second listener
        listener_id2 = self.event_manager.add_listener(
            PumpFunEventType.TRADE_EVENT,
            test_callback
        )
        
        self.assertEqual(listener_id2, 2)
        self.assertEqual(self.event_manager.next_id, 3)
    
    def test_remove_listener(self):
        """Test removing event listeners."""
        def test_callback(event, slot, signature):
            pass
        
        # Add listener
        listener_id = self.event_manager.add_listener(
            PumpFunEventType.CREATE_EVENT,
            test_callback
        )
        
        # Verify it exists
        self.assertIn(listener_id, self.event_manager.listeners)
        
        # Remove listener
        self.event_manager.remove_listener(listener_id)
        
        # Verify it's removed
        self.assertNotIn(listener_id, self.event_manager.listeners)
        
        # Test removing non-existent listener (should not raise error)
        self.event_manager.remove_listener(999)
    
    def test_get_pump_fun_program_id(self):
        """Test getting PumpFun program ID."""
        program_id = self.event_manager._get_pump_fun_program_id()
        self.assertIsInstance(program_id, str)
        self.assertTrue(len(program_id) > 0)


class TestEventParsing(unittest.TestCase):
    """Test event parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.event_manager = EventManager(self.mock_client, "wss://test.com")
    
    def test_parse_create_event(self):
        """Test parsing create events."""
        log_data = "CreateEvent: mint=ABC123, name=TestToken, symbol=TST"
        result = self.event_manager._parse_create_event(log_data)
        
        self.assertEqual(result["event_type"], PumpFunEventType.CREATE_EVENT.value)
        self.assertIn("mint", result)
        self.assertIn("name", result)
        self.assertIn("symbol", result)
        self.assertIn("uri", result)
        self.assertIn("user", result)
        self.assertIn("timestamp", result)
        self.assertIsInstance(result["timestamp"], int)
    
    def test_parse_trade_event(self):
        """Test parsing trade events."""
        log_data = "TradeEvent: mint=ABC123, user=DEF456, buy=true"
        result = self.event_manager._parse_trade_event(log_data)
        
        self.assertEqual(result["event_type"], PumpFunEventType.TRADE_EVENT.value)
        self.assertIn("mint", result)
        self.assertIn("user", result)
        self.assertIn("is_buy", result)
        self.assertIn("sol_amount", result)
        self.assertIn("token_amount", result)
        self.assertIn("timestamp", result)
        self.assertIsInstance(result["is_buy"], bool)
    
    def test_parse_complete_event(self):
        """Test parsing complete events."""
        log_data = "CompleteEvent: mint=ABC123, user=DEF456"
        result = self.event_manager._parse_complete_event(log_data)
        
        self.assertEqual(result["event_type"], PumpFunEventType.COMPLETE_EVENT.value)
        self.assertIn("mint", result)
        self.assertIn("user", result)
        self.assertIn("timestamp", result)
    
    def test_parse_log_message_with_create_event(self):
        """Test parsing log messages containing create events."""
        mock_message = Mock()
        mock_message.result = {
            "logs": [
                "Program log: CreateEvent data here",
                "Other log entry"
            ]
        }
        
        with patch.object(self.event_manager, '_parse_create_event') as mock_parse:
            mock_parse.return_value = {"event_type": "createEvent", "test": "data"}
            
            result = self.event_manager._parse_log_message(mock_message)
            
            self.assertIsNotNone(result)
            mock_parse.assert_called_once()
    
    def test_parse_log_message_no_events(self):
        """Test parsing log messages with no events."""
        mock_message = Mock()
        mock_message.result = {
            "logs": [
                "Regular program log",
                "Another regular log"
            ]
        }
        
        result = self.event_manager._parse_log_message(mock_message)
        self.assertIsNone(result)
    
    def test_parse_log_message_invalid_format(self):
        """Test parsing malformed log messages."""
        mock_message = Mock()
        mock_message.result = None
        
        result = self.event_manager._parse_log_message(mock_message)
        self.assertIsNone(result)


class TestEventObjectCreation(unittest.TestCase):
    """Test event object creation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.event_manager = EventManager(self.mock_client, "wss://test.com")
    
    def test_create_create_event_object(self):
        """Test creating CreateEvent objects."""
        event_data = {
            "mint": "11111111111111111111111111111112",
            "name": "Test Token",
            "symbol": "TEST",
            "uri": "https://example.com/metadata.json",
            "user": "11111111111111111111111111111113",
            "timestamp": 1234567890
        }
        
        event_obj = self.event_manager._create_event_object(
            PumpFunEventType.CREATE_EVENT.value,
            event_data
        )
        
        self.assertIsInstance(event_obj, CreateEvent)
        self.assertIsInstance(event_obj.mint, PublicKey)
        self.assertEqual(event_obj.name, "Test Token")
        self.assertEqual(event_obj.symbol, "TEST")
        self.assertEqual(event_obj.uri, "https://example.com/metadata.json")
        self.assertIsInstance(event_obj.user, PublicKey)
        self.assertEqual(event_obj.timestamp, 1234567890)
    
    def test_create_trade_event_object(self):
        """Test creating TradeEvent objects."""
        event_data = {
            "mint": "11111111111111111111111111111112",
            "user": "11111111111111111111111111111113",
            "is_buy": True,
            "sol_amount": 1000000000,
            "token_amount": 1000000000000,
            "timestamp": 1234567890
        }
        
        event_obj = self.event_manager._create_event_object(
            PumpFunEventType.TRADE_EVENT.value,
            event_data
        )
        
        self.assertIsInstance(event_obj, TradeEvent)
        self.assertIsInstance(event_obj.mint, PublicKey)
        self.assertIsInstance(event_obj.user, PublicKey)
        self.assertTrue(event_obj.is_buy)
        self.assertEqual(event_obj.sol_amount, 1000000000)
        self.assertEqual(event_obj.token_amount, 1000000000000)
        self.assertEqual(event_obj.timestamp, 1234567890)
    
    def test_create_complete_event_object(self):
        """Test creating CompleteEvent objects."""
        event_data = {
            "mint": "11111111111111111111111111111112",
            "user": "11111111111111111111111111111113",
            "timestamp": 1234567890
        }
        
        event_obj = self.event_manager._create_event_object(
            PumpFunEventType.COMPLETE_EVENT.value,
            event_data
        )
        
        self.assertIsInstance(event_obj, CompleteEvent)
        self.assertIsInstance(event_obj.mint, PublicKey)
        self.assertIsInstance(event_obj.user, PublicKey)
        self.assertEqual(event_obj.timestamp, 1234567890)
    
    def test_create_unknown_event_object(self):
        """Test creating objects for unknown event types."""
        from pumpdotfun_sdk.utils import PumpFunError
        
        event_data = {"test": "data"}
        
        with self.assertRaises(PumpFunError):
            self.event_manager._create_event_object("unknown_event", event_data)


class TestEventProcessing(unittest.TestCase):
    """Test event processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.event_manager = EventManager(self.mock_client, "wss://test.com")
        self.callback_called = False
        self.callback_event = None
        self.callback_slot = None
        self.callback_signature = None
    
    def test_callback(self, event, slot, signature):
        """Test callback function."""
        self.callback_called = True
        self.callback_event = event
        self.callback_slot = slot
        self.callback_signature = signature
    
    async def test_process_message_with_matching_listener(self):
        """Test processing messages with matching listeners."""
        # Add listener
        listener_id = self.event_manager.add_listener(
            PumpFunEventType.CREATE_EVENT,
            self.test_callback
        )
        
        # Mock message processing
        mock_message = Mock()
        
        with patch.object(self.event_manager, '_parse_log_message') as mock_parse:
            mock_parse.return_value = {
                "event_type": PumpFunEventType.CREATE_EVENT.value,
                "mint": "11111111111111111111111111111112",
                "name": "Test",
                "symbol": "TST",
                "uri": "https://test.com",
                "user": "11111111111111111111111111111113",
                "timestamp": 1234567890,
                "slot": 12345,
                "signature": "test_signature"
            }
            
            await self.event_manager._process_message(mock_message)
            
            # Verify callback was called
            self.assertTrue(self.callback_called)
            self.assertIsInstance(self.callback_event, CreateEvent)
            self.assertEqual(self.callback_slot, 12345)
            self.assertEqual(self.callback_signature, "test_signature")
    
    async def test_process_message_no_matching_listener(self):
        """Test processing messages with no matching listeners."""
        # Add listener for different event type
        self.event_manager.add_listener(
            PumpFunEventType.TRADE_EVENT,
            self.test_callback
        )
        
        # Mock message processing
        mock_message = Mock()
        
        with patch.object(self.event_manager, '_parse_log_message') as mock_parse:
            mock_parse.return_value = {
                "event_type": PumpFunEventType.CREATE_EVENT.value,
                "slot": 12345,
                "signature": "test_signature"
            }
            
            await self.event_manager._process_message(mock_message)
            
            # Verify callback was not called
            self.assertFalse(self.callback_called)
    
    async def test_process_message_callback_error(self):
        """Test processing messages when callback raises error."""
        def error_callback(event, slot, signature):
            raise Exception("Callback error")
        
        # Add listener with error callback
        self.event_manager.add_listener(
            PumpFunEventType.CREATE_EVENT,
            error_callback
        )
        
        # Mock message processing
        mock_message = Mock()
        
        with patch.object(self.event_manager, '_parse_log_message') as mock_parse:
            mock_parse.return_value = {
                "event_type": PumpFunEventType.CREATE_EVENT.value,
                "mint": "11111111111111111111111111111112",
                "name": "Test",
                "symbol": "TST",
                "uri": "https://test.com",
                "user": "11111111111111111111111111111113",
                "timestamp": 1234567890,
                "slot": 12345,
                "signature": "test_signature"
            }
            
            # Should not raise exception even if callback fails
            await self.event_manager._process_message(mock_message)


class TestEventManagerLifecycle(unittest.TestCase):
    """Test EventManager lifecycle management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.event_manager = EventManager(self.mock_client, "wss://test.com")
    
    def test_stop_listening(self):
        """Test stopping event listening."""
        # Set up as if listening
        self.event_manager.is_listening = True
        self.event_manager.listen_task = Mock()
        self.event_manager.websocket_connection = Mock()
        
        self.event_manager.stop_listening()
        
        self.assertFalse(self.event_manager.is_listening)
        self.event_manager.listen_task.cancel.assert_called_once()
    
    @patch('pumpdotfun_sdk.events.connect')
    async def test_listen_loop_connection_error(self, mock_connect):
        """Test listen loop handling connection errors."""
        # Mock connection failure
        mock_connect.side_effect = Exception("Connection failed")
        
        # Should not raise exception
        await self.event_manager._listen_loop()
    
    def test_multiple_listeners_same_event(self):
        """Test multiple listeners for the same event type."""
        callback1_called = False
        callback2_called = False
        
        def callback1(event, slot, signature):
            nonlocal callback1_called
            callback1_called = True
        
        def callback2(event, slot, signature):
            nonlocal callback2_called
            callback2_called = True
        
        # Add two listeners for same event
        id1 = self.event_manager.add_listener(PumpFunEventType.CREATE_EVENT, callback1)
        id2 = self.event_manager.add_listener(PumpFunEventType.CREATE_EVENT, callback2)
        
        self.assertNotEqual(id1, id2)
        self.assertEqual(len(self.event_manager.listeners), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)

