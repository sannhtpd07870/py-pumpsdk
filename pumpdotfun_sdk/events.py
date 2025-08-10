"""
Event handling for PumpDotFun SDK.
"""

import asyncio
import logging
import inspect
import time
from typing import Dict, Callable, Any, Optional, List
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.publickey import PublicKey
from .types import PumpFunEventType, CreateEvent, TradeEvent, CompleteEvent, EventCallback
from .utils import PumpFunError

logger = logging.getLogger(__name__)


class EventManager:
    """
    Manages events from the Solana blockchain for PumpFun protocol.
    """
    
    def __init__(self, rpc_client: AsyncClient, websocket_url: str):
        """
        Initialize event manager.
        
        Args:
            rpc_client: Solana RPC client
            websocket_url: WebSocket URL for real-time events
        """
        self.rpc_client = rpc_client
        self.websocket_url = websocket_url
        self.listeners: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1
        self.is_listening = False
        self.websocket_connection = None
        self.listen_task = None
        
    def add_listener(
        self,
        event_type: PumpFunEventType,
        callback: EventCallback
    ) -> int:
        """
        Add an event listener.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to execute when event occurs
            
        Returns:
            Listener ID
        """
        listener_id = self.next_id
        self.next_id += 1
        
        self.listeners[listener_id] = {
            "event_type": event_type,
            "callback": callback
        }
        
        logger.info(f"Added event listener {listener_id} for {event_type.value}")
        return listener_id
    
    def remove_listener(self, listener_id: int) -> None:
        """
        Remove an event listener.
        
        Args:
            listener_id: ID of the listener to remove
        """
        if listener_id in self.listeners:
            del self.listeners[listener_id]
            logger.info(f"Removed event listener {listener_id}")
        else:
            logger.warning(f"Listener {listener_id} not found")
    
    async def start_listening(self) -> None:
        """
        Start listening for events from the blockchain.
        """
        if self.is_listening:
            logger.warning("Already listening for events")
            return
            
        self.is_listening = True
        self.listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Started listening for PumpFun events")
    
    def stop_listening(self) -> None:
        """
        Stop listening for events.
        """
        self.is_listening = False
        
        if self.listen_task:
            self.listen_task.cancel()

        if self.websocket_connection:
            close_method = self.websocket_connection.close
            if inspect.iscoroutinefunction(close_method):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(close_method())
                except RuntimeError:
                    asyncio.run(close_method())
            else:
                close_method()
            
        logger.info("Stopped listening for events")
    
    async def _listen_loop(self) -> None:
        """
        Main event listening loop.
        """
        try:
            async with connect(self.websocket_url) as websocket:
                self.websocket_connection = websocket
                
                # Subscribe to program logs for PumpFun program
                await websocket.logs_subscribe(
                    filter_={"mentions": [self._get_pump_fun_program_id()]}
                )
                
                async for message in websocket:
                    if not self.is_listening:
                        break
                        
                    await self._process_message(message)
                    
        except Exception as e:
            logger.error(f"Error in event listening loop: {e}")
            if self.is_listening:
                # Attempt to reconnect after a delay
                await asyncio.sleep(5)
                if self.is_listening:
                    await self.start_listening()
    
    async def _process_message(self, message: Any) -> None:
        """
        Process incoming WebSocket message.
        
        Args:
            message: WebSocket message
        """
        try:
            # Parse the message and extract event information
            event_data = self._parse_log_message(message)
            
            if event_data:
                event_type = event_data.get("event_type")
                slot = event_data.get("slot", 0)
                signature = event_data.get("signature", "")
                
                # Notify relevant listeners
                for listener_id, listener in self.listeners.items():
                    if listener["event_type"].value == event_type:
                        try:
                            event_obj = self._create_event_object(event_type, event_data)
                            listener["callback"](event_obj, slot, signature)
                        except Exception as e:
                            logger.error(f"Error in event callback {listener_id}: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing event message: {e}")
    
    def _parse_log_message(self, message: Any) -> Optional[Dict[str, Any]]:
        """
        Parse log message to extract event data.
        
        Args:
            message: Raw log message
            
        Returns:
            Parsed event data or None
        """
        # This would need to be implemented based on the actual
        # log format from PumpFun program
        try:
            result = None
            if isinstance(message, dict):
                result = message.get('result')
            else:
                result = getattr(message, 'result', None)

            if result:
                logs = (
                    result.get('logs', [])
                    if isinstance(result, dict)
                    else getattr(result, 'logs', [])
                )

                for log in logs:
                    if 'Program log:' in log:
                        log_data = log.split('Program log: ', 1)[1]

                        if 'CreateEvent' in log_data:
                            return self._parse_create_event(log_data)
                        elif 'TradeEvent' in log_data:
                            return self._parse_trade_event(log_data)
                        elif 'CompleteEvent' in log_data:
                            return self._parse_complete_event(log_data)
                            
        except Exception as e:
            logger.error(f"Error parsing log message: {e}")
            
        return None
    
    def _parse_create_event(self, log_data: str) -> Dict[str, Any]:
        """Parse create event from log data."""
        # Implementation would depend on actual log format
        return {
            "event_type": PumpFunEventType.CREATE_EVENT.value,
            "mint": "placeholder",  # Would extract from actual log
            "name": "placeholder",
            "symbol": "placeholder",
            "uri": "placeholder",
            "user": "placeholder",
            "timestamp": int(time.time())
        }
    
    def _parse_trade_event(self, log_data: str) -> Dict[str, Any]:
        """Parse trade event from log data."""
        return {
            "event_type": PumpFunEventType.TRADE_EVENT.value,
            "mint": "placeholder",
            "user": "placeholder",
            "is_buy": True,
            "sol_amount": 0,
            "token_amount": 0,
            "timestamp": int(time.time())
        }
    
    def _parse_complete_event(self, log_data: str) -> Dict[str, Any]:
        """Parse complete event from log data."""
        return {
            "event_type": PumpFunEventType.COMPLETE_EVENT.value,
            "mint": "placeholder",
            "user": "placeholder",
            "timestamp": int(time.time())
        }
    
    def _create_event_object(self, event_type: str, event_data: Dict[str, Any]) -> Any:
        """
        Create appropriate event object from event data.
        
        Args:
            event_type: Type of event
            event_data: Event data dictionary
            
        Returns:
            Event object
        """
        if event_type == PumpFunEventType.CREATE_EVENT.value:
            return CreateEvent(
                mint=PublicKey(event_data["mint"]),
                name=event_data["name"],
                symbol=event_data["symbol"],
                uri=event_data["uri"],
                user=PublicKey(event_data["user"]),
                timestamp=event_data["timestamp"]
            )
        elif event_type == PumpFunEventType.TRADE_EVENT.value:
            return TradeEvent(
                mint=PublicKey(event_data["mint"]),
                user=PublicKey(event_data["user"]),
                is_buy=event_data["is_buy"],
                sol_amount=event_data["sol_amount"],
                token_amount=event_data["token_amount"],
                timestamp=event_data["timestamp"]
            )
        elif event_type == PumpFunEventType.COMPLETE_EVENT.value:
            return CompleteEvent(
                mint=PublicKey(event_data["mint"]),
                user=PublicKey(event_data["user"]),
                timestamp=event_data["timestamp"]
            )
        else:
            raise PumpFunError(f"Unknown event type: {event_type}")
    
    def _get_pump_fun_program_id(self) -> str:
        """
        Get the PumpFun program ID.
        
        Returns:
            Program ID as string
        """
        # This would be the actual PumpFun program ID
        return "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"  # Placeholder

