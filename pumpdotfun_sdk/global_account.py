"""
Global account management for PumpDotFun SDK.
"""

import struct
import base64
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from .utils import PumpFunError, NetworkError


@dataclass
class GlobalAccountData:
    """
    Represents the global account data structure.
    """
    initialized: bool
    authority: PublicKey
    fee_recipient: PublicKey
    initial_virtual_token_reserves: int
    initial_virtual_sol_reserves: int
    initial_real_token_reserves: int
    token_total_supply: int
    fee_basis_points: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "initialized": self.initialized,
            "authority": str(self.authority),
            "fee_recipient": str(self.fee_recipient),
            "initial_virtual_token_reserves": self.initial_virtual_token_reserves,
            "initial_virtual_sol_reserves": self.initial_virtual_sol_reserves,
            "initial_real_token_reserves": self.initial_real_token_reserves,
            "token_total_supply": self.token_total_supply,
            "fee_basis_points": self.fee_basis_points
        }


class GlobalAccountManager:
    """
    Manages interactions with PumpFun's global account.
    """
    
    def __init__(self, rpc_client: AsyncClient, program_id: PublicKey):
        """
        Initialize global account manager.
        
        Args:
            rpc_client: Solana RPC client
            program_id: PumpFun program ID
        """
        self.rpc_client = rpc_client
        self.program_id = program_id
        self._global_account_address = None
        self._cached_data = None
        self._cache_timestamp = 0
        
        # Cache settings
        self.CACHE_DURATION = 30  # seconds
    
    def get_global_account_address(self) -> PublicKey:
        """
        Get the global account address.
        
        Returns:
            Global account public key
        """
        if not self._global_account_address:
            # Derive global account address using PDA
            seeds = [b"global"]
            address, _ = PublicKey.find_program_address(seeds, self.program_id)
            self._global_account_address = address
            
        return self._global_account_address
    
    async def fetch_global_account_data(
        self,
        force_refresh: bool = False
    ) -> GlobalAccountData:
        """
        Fetch global account data from Solana.
        
        Args:
            force_refresh: Force refresh cached data
            
        Returns:
            Global account data
        """
        import time
        current_time = time.time()
        
        # Check cache
        if (not force_refresh and 
            self._cached_data and 
            current_time - self._cache_timestamp < self.CACHE_DURATION):
            return self._cached_data
        
        try:
            global_account_address = self.get_global_account_address()
            account_info = await self.rpc_client.get_account_info(global_account_address)

            if not account_info.value:
                raise NetworkError("Global account not found")

            raw_data = account_info.value.data
            if isinstance(raw_data, (list, tuple)):
                raw_data = base64.b64decode(raw_data[0])
            elif isinstance(raw_data, str):
                raw_data = base64.b64decode(raw_data)

            data = self._parse_global_account_data(raw_data)
            
            # Update cache
            self._cached_data = data
            self._cache_timestamp = current_time
            
            return data
            
        except Exception as e:
            raise NetworkError(f"Failed to fetch global account data: {e}")
    
    def _parse_global_account_data(self, raw_data: bytes) -> GlobalAccountData:
        """
        Parse raw global account data.
        
        Args:
            raw_data: Raw account data bytes
            
        Returns:
            Parsed global account data
        """
        try:
            # This is a placeholder implementation
            # The actual parsing would depend on PumpFun's account structure
            
            # Assuming a simple structure for demonstration
            if len(raw_data) < 100:  # Minimum expected size
                raise PumpFunError("Invalid global account data size")
            
            # Parse fields (this would need to match actual PumpFun structure)
            offset = 0
            
            # Discriminator (8 bytes)
            offset += 8
            
            # Initialized flag (1 byte)
            initialized = bool(raw_data[offset])
            offset += 1
            
            # Authority (32 bytes)
            authority = PublicKey(raw_data[offset:offset + 32])
            offset += 32
            
            # Fee recipient (32 bytes)
            fee_recipient = PublicKey(raw_data[offset:offset + 32])
            offset += 32
            
            # Various reserves and supply values (8 bytes each)
            initial_virtual_token_reserves = struct.unpack('<Q', raw_data[offset:offset + 8])[0]
            offset += 8
            
            initial_virtual_sol_reserves = struct.unpack('<Q', raw_data[offset:offset + 8])[0]
            offset += 8
            
            initial_real_token_reserves = struct.unpack('<Q', raw_data[offset:offset + 8])[0]
            offset += 8
            
            token_total_supply = struct.unpack('<Q', raw_data[offset:offset + 8])[0]
            offset += 8
            
            # Fee basis points (2 bytes)
            fee_basis_points = struct.unpack('<H', raw_data[offset:offset + 2])[0]
            
            return GlobalAccountData(
                initialized=initialized,
                authority=authority,
                fee_recipient=fee_recipient,
                initial_virtual_token_reserves=initial_virtual_token_reserves,
                initial_virtual_sol_reserves=initial_virtual_sol_reserves,
                initial_real_token_reserves=initial_real_token_reserves,
                token_total_supply=token_total_supply,
                fee_basis_points=fee_basis_points
            )
            
        except Exception as e:
            raise PumpFunError(f"Failed to parse global account data: {e}")
    
    async def get_program_statistics(self) -> Dict[str, Any]:
        """
        Get program-wide statistics.
        
        Returns:
            Program statistics
        """
        try:
            global_data = await self.fetch_global_account_data()
            
            # Calculate additional statistics
            stats = {
                "program_initialized": global_data.initialized,
                "authority": str(global_data.authority),
                "fee_recipient": str(global_data.fee_recipient),
                "default_fee_basis_points": global_data.fee_basis_points,
                "default_virtual_token_reserves": global_data.initial_virtual_token_reserves,
                "default_virtual_sol_reserves": global_data.initial_virtual_sol_reserves,
                "default_real_token_reserves": global_data.initial_real_token_reserves,
                "default_token_total_supply": global_data.token_total_supply,
                "fee_percentage": global_data.fee_basis_points / 100,  # Convert to percentage
            }
            
            return stats
            
        except Exception as e:
            raise NetworkError(f"Failed to get program statistics: {e}")
    
    async def get_fee_structure(self) -> Dict[str, Any]:
        """
        Get current fee structure.
        
        Returns:
            Fee structure information
        """
        try:
            global_data = await self.fetch_global_account_data()
            
            return {
                "fee_basis_points": global_data.fee_basis_points,
                "fee_percentage": global_data.fee_basis_points / 100,
                "fee_recipient": str(global_data.fee_recipient),
                "description": f"Trading fee of {global_data.fee_basis_points / 100}% goes to {global_data.fee_recipient}"
            }
            
        except Exception as e:
            raise NetworkError(f"Failed to get fee structure: {e}")
    
    async def validate_program_state(self) -> bool:
        """
        Validate that the program is in a valid state.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            global_data = await self.fetch_global_account_data()
            
            # Basic validation checks
            if not global_data.initialized:
                return False
                
            if global_data.fee_basis_points > 10000:  # Max 100%
                return False
                
            if global_data.initial_virtual_token_reserves <= 0:
                return False
                
            if global_data.initial_virtual_sol_reserves <= 0:
                return False
                
            return True
            
        except Exception:
            return False
    
    def clear_cache(self) -> None:
        """Clear cached global account data."""
        self._cached_data = None
        self._cache_timestamp = 0


class ProgramConfigManager:
    """
    Manages program configuration and constants.
    """
    
    def __init__(self, global_account_manager: GlobalAccountManager):
        """
        Initialize program config manager.
        
        Args:
            global_account_manager: Global account manager instance
        """
        self.global_manager = global_account_manager
        self._config_cache = {}
    
    async def get_bonding_curve_config(self) -> Dict[str, Any]:
        """
        Get bonding curve configuration.
        
        Returns:
            Bonding curve configuration
        """
        if "bonding_curve" not in self._config_cache:
            global_data = await self.global_manager.fetch_global_account_data()
            
            self._config_cache["bonding_curve"] = {
                "virtual_token_reserves": global_data.initial_virtual_token_reserves,
                "virtual_sol_reserves": global_data.initial_virtual_sol_reserves,
                "real_token_reserves": global_data.initial_real_token_reserves,
                "token_total_supply": global_data.token_total_supply,
                "completion_threshold": global_data.initial_virtual_sol_reserves,  # When curve completes
            }
        
        return self._config_cache["bonding_curve"]
    
    async def get_trading_config(self) -> Dict[str, Any]:
        """
        Get trading configuration.
        
        Returns:
            Trading configuration
        """
        if "trading" not in self._config_cache:
            global_data = await self.global_manager.fetch_global_account_data()
            
            self._config_cache["trading"] = {
                "fee_basis_points": global_data.fee_basis_points,
                "fee_recipient": str(global_data.fee_recipient),
                "minimum_trade_amount": 1000,  # Minimum lamports
                "maximum_slippage": 5000,  # 50% in basis points
            }
        
        return self._config_cache["trading"]
    
    async def get_token_creation_config(self) -> Dict[str, Any]:
        """
        Get token creation configuration.
        
        Returns:
            Token creation configuration
        """
        if "token_creation" not in self._config_cache:
            global_data = await self.global_manager.fetch_global_account_data()
            
            self._config_cache["token_creation"] = {
                "authority": str(global_data.authority),
                "default_decimals": 6,
                "metadata_required_fields": ["name", "symbol", "description", "image"],
                "maximum_name_length": 32,
                "maximum_symbol_length": 10,
                "maximum_description_length": 500,
            }
        
        return self._config_cache["token_creation"]
    
    def clear_config_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache.clear()
    
    async def refresh_all_configs(self) -> None:
        """Refresh all cached configurations."""
        self.clear_config_cache()
        await self.get_bonding_curve_config()
        await self.get_trading_config()
        await self.get_token_creation_config()


class AccountMonitor:
    """
    Monitors global account changes.
    """
    
    def __init__(self, global_account_manager: GlobalAccountManager):
        """
        Initialize account monitor.
        
        Args:
            global_account_manager: Global account manager instance
        """
        self.global_manager = global_account_manager
        self.monitoring = False
        self.callbacks = []
    
    def add_change_callback(self, callback) -> None:
        """
        Add callback for account changes.
        
        Args:
            callback: Function to call when account changes
        """
        self.callbacks.append(callback)
    
    async def start_monitoring(self, interval: int = 30) -> None:
        """
        Start monitoring global account changes.
        
        Args:
            interval: Check interval in seconds
        """
        import asyncio
        
        self.monitoring = True
        last_data = None
        
        while self.monitoring:
            try:
                current_data = await self.global_manager.fetch_global_account_data(force_refresh=True)
                
                if last_data and current_data != last_data:
                    # Account changed, notify callbacks
                    for callback in self.callbacks:
                        try:
                            await callback(current_data, last_data)
                        except Exception as e:
                            print(f"Error in change callback: {e}")
                
                last_data = current_data
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"Error monitoring global account: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.monitoring = False

