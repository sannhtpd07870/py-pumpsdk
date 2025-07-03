"""
Bonding curve calculations for PumpDotFun SDK.
"""

import math
from typing import Dict, Any, Optional
from .utils import PumpFunError


class BondingCurveCalculator:
    """
    Handles bonding curve calculations for PumpFun protocol.
    """
    
    # Constants for bonding curve calculations
    # These would need to be adjusted based on actual PumpFun parameters
    VIRTUAL_SOL_RESERVES = 30_000_000_000  # 30 SOL in lamports
    VIRTUAL_TOKEN_RESERVES = 1_073_000_000_000_000  # Virtual token reserves
    
    @staticmethod
    def get_buy_price(
        sol_amount: int,
        real_sol_reserves: int,
        real_token_reserves: int
    ) -> int:
        """
        Calculate token amount received for a given SOL amount.
        
        Args:
            sol_amount: Amount of SOL to spend (in lamports)
            real_sol_reserves: Current real SOL reserves
            real_token_reserves: Current real token reserves
            
        Returns:
            Amount of tokens to receive
        """
        if sol_amount <= 0:
            raise PumpFunError("SOL amount must be positive")
            
        # Add virtual reserves to real reserves
        virtual_sol_reserves = BondingCurveCalculator.VIRTUAL_SOL_RESERVES + real_sol_reserves
        virtual_token_reserves = BondingCurveCalculator.VIRTUAL_TOKEN_RESERVES + real_token_reserves
        
        # Calculate constant product
        k = virtual_sol_reserves * virtual_token_reserves
        
        # Calculate new SOL reserves after purchase
        new_sol_reserves = virtual_sol_reserves + sol_amount
        
        # Calculate new token reserves
        new_token_reserves = k // new_sol_reserves
        
        # Calculate tokens to receive
        tokens_out = virtual_token_reserves - new_token_reserves
        
        if tokens_out <= 0:
            raise PumpFunError("Invalid token amount calculated")
            
        return int(tokens_out)
    
    @staticmethod
    def get_sell_price(
        token_amount: int,
        real_sol_reserves: int,
        real_token_reserves: int
    ) -> int:
        """
        Calculate SOL amount received for a given token amount.
        
        Args:
            token_amount: Amount of tokens to sell
            real_sol_reserves: Current real SOL reserves
            real_token_reserves: Current real token reserves
            
        Returns:
            Amount of SOL to receive (in lamports)
        """
        if token_amount <= 0:
            raise PumpFunError("Token amount must be positive")
            
        # Add virtual reserves to real reserves
        virtual_sol_reserves = BondingCurveCalculator.VIRTUAL_SOL_RESERVES + real_sol_reserves
        virtual_token_reserves = BondingCurveCalculator.VIRTUAL_TOKEN_RESERVES + real_token_reserves
        
        # Calculate constant product
        k = virtual_sol_reserves * virtual_token_reserves
        
        # Calculate new token reserves after sale
        new_token_reserves = virtual_token_reserves + token_amount
        
        # Calculate new SOL reserves
        new_sol_reserves = k // new_token_reserves
        
        # Calculate SOL to receive
        sol_out = virtual_sol_reserves - new_sol_reserves
        
        if sol_out <= 0:
            raise PumpFunError("Invalid SOL amount calculated")
            
        return int(sol_out)
    
    @staticmethod
    def get_buy_out_price(
        real_sol_reserves: int,
        real_token_reserves: int
    ) -> int:
        """
        Calculate the price to buy out all remaining tokens.
        
        Args:
            real_sol_reserves: Current real SOL reserves
            real_token_reserves: Current real token reserves
            
        Returns:
            SOL amount needed to buy all remaining tokens
        """
        # This represents the SOL needed to reach the bonding curve completion
        # The exact calculation would depend on PumpFun's specific parameters
        
        virtual_sol_reserves = BondingCurveCalculator.VIRTUAL_SOL_RESERVES + real_sol_reserves
        virtual_token_reserves = BondingCurveCalculator.VIRTUAL_TOKEN_RESERVES + real_token_reserves
        
        # Calculate constant product
        k = virtual_sol_reserves * virtual_token_reserves
        
        # When all tokens are bought, token reserves become virtual reserves only
        final_token_reserves = BondingCurveCalculator.VIRTUAL_TOKEN_RESERVES
        
        # Calculate required SOL reserves
        required_sol_reserves = k // final_token_reserves
        
        # Calculate additional SOL needed
        additional_sol_needed = required_sol_reserves - virtual_sol_reserves
        
        return max(0, int(additional_sol_needed))
    
    @staticmethod
    def calculate_slippage(
        expected_amount: int,
        actual_amount: int
    ) -> float:
        """
        Calculate slippage percentage.
        
        Args:
            expected_amount: Expected amount
            actual_amount: Actual amount received
            
        Returns:
            Slippage as a percentage (0.0 to 100.0)
        """
        if expected_amount <= 0:
            return 0.0
            
        slippage = abs(expected_amount - actual_amount) / expected_amount * 100
        return slippage
    
    @staticmethod
    def apply_slippage_tolerance(
        amount: int,
        slippage_basis_points: int,
        is_minimum: bool = True
    ) -> int:
        """
        Apply slippage tolerance to an amount.
        
        Args:
            amount: Base amount
            slippage_basis_points: Slippage tolerance in basis points
            is_minimum: If True, calculate minimum acceptable amount
            
        Returns:
            Amount with slippage applied
        """
        slippage_multiplier = slippage_basis_points / 10000
        
        if is_minimum:
            # For minimum amounts (selling), reduce by slippage
            return int(amount * (1 - slippage_multiplier))
        else:
            # For maximum amounts (buying), increase by slippage
            return int(amount * (1 + slippage_multiplier))
    
    @staticmethod
    def get_market_cap(
        current_price_per_token: float,
        total_supply: int,
        decimals: int = 6
    ) -> float:
        """
        Calculate market cap of a token.
        
        Args:
            current_price_per_token: Current price per token in SOL
            total_supply: Total token supply
            decimals: Token decimals
            
        Returns:
            Market cap in SOL
        """
        adjusted_supply = total_supply / (10 ** decimals)
        return current_price_per_token * adjusted_supply
    
    @staticmethod
    def estimate_price_impact(
        trade_amount: int,
        reserves: int,
        is_buy: bool = True
    ) -> float:
        """
        Estimate price impact of a trade.
        
        Args:
            trade_amount: Amount to trade
            reserves: Current reserves
            is_buy: True for buy, False for sell
            
        Returns:
            Price impact as percentage
        """
        if reserves <= 0:
            return 0.0
            
        # Simple price impact estimation
        impact = (trade_amount / reserves) * 100
        
        # Price impact is typically higher for sells
        if not is_buy:
            impact *= 1.2
            
        return min(impact, 100.0)  # Cap at 100%


class BondingCurveAccount:
    """
    Represents a bonding curve account state.
    """
    
    def __init__(self, account_data: Dict[str, Any]):
        """
        Initialize bonding curve account.
        
        Args:
            account_data: Raw account data from Solana
        """
        self.virtual_token_reserves = account_data.get("virtualTokenReserves", 0)
        self.virtual_sol_reserves = account_data.get("virtualSolReserves", 0)
        self.real_token_reserves = account_data.get("realTokenReserves", 0)
        self.real_sol_reserves = account_data.get("realSolReserves", 0)
        self.token_total_supply = account_data.get("tokenTotalSupply", 0)
        self.complete = account_data.get("complete", False)
    
    def get_current_price(self) -> float:
        """
        Get current token price in SOL.
        
        Returns:
            Current price per token in SOL
        """
        if self.virtual_token_reserves <= 0:
            return 0.0
            
        return (self.virtual_sol_reserves / 1_000_000_000) / (self.virtual_token_reserves / 1_000_000)
    
    def is_complete(self) -> bool:
        """
        Check if bonding curve is complete.
        
        Returns:
            True if complete, False otherwise
        """
        return self.complete
    
    def get_progress_percentage(self) -> float:
        """
        Get completion progress as percentage.
        
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if self.token_total_supply <= 0:
            return 0.0
            
        # Calculate based on how many tokens have been bought
        tokens_bought = self.token_total_supply - self.real_token_reserves
        progress = (tokens_bought / self.token_total_supply) * 100
        
        return min(progress, 100.0)

