"""
Automated Market Maker (AMM) functionality for PumpDotFun SDK.
"""

import math
from typing import Dict, Any, Optional, Tuple
from solana.publickey import PublicKey
from .utils import PumpFunError


class AMMCalculator:
    """
    Handles AMM calculations and liquidity management for PumpFun protocol.
    """
    
    # AMM Constants (these would be based on actual PumpFun parameters)
    FEE_BASIS_POINTS = 100  # 1% fee
    MINIMUM_LIQUIDITY = 1000
    
    @staticmethod
    def calculate_constant_product(
        reserve_a: int,
        reserve_b: int
    ) -> int:
        """
        Calculate constant product (k = x * y).
        
        Args:
            reserve_a: Reserve amount of token A
            reserve_b: Reserve amount of token B
            
        Returns:
            Constant product value
        """
        return reserve_a * reserve_b
    
    @staticmethod
    def get_amount_out(
        amount_in: int,
        reserve_in: int,
        reserve_out: int,
        fee_basis_points: int = None
    ) -> int:
        """
        Calculate output amount for a given input amount.
        
        Args:
            amount_in: Input amount
            reserve_in: Input token reserves
            reserve_out: Output token reserves
            fee_basis_points: Fee in basis points
            
        Returns:
            Output amount after fees
        """
        if amount_in <= 0:
            raise PumpFunError("Input amount must be positive")
            
        if reserve_in <= 0 or reserve_out <= 0:
            raise PumpFunError("Reserves must be positive")
        
        fee_bp = fee_basis_points or AMMCalculator.FEE_BASIS_POINTS
        
        # Apply fee to input amount
        amount_in_with_fee = amount_in * (10000 - fee_bp)
        
        # Calculate output using constant product formula
        numerator = amount_in_with_fee * reserve_out
        denominator = (reserve_in * 10000) + amount_in_with_fee
        
        amount_out = numerator // denominator
        
        if amount_out <= 0:
            raise PumpFunError("Insufficient output amount")
            
        return amount_out
    
    @staticmethod
    def get_amount_in(
        amount_out: int,
        reserve_in: int,
        reserve_out: int,
        fee_basis_points: int = None
    ) -> int:
        """
        Calculate input amount needed for a desired output amount.
        
        Args:
            amount_out: Desired output amount
            reserve_in: Input token reserves
            reserve_out: Output token reserves
            fee_basis_points: Fee in basis points
            
        Returns:
            Required input amount including fees
        """
        if amount_out <= 0:
            raise PumpFunError("Output amount must be positive")
            
        if reserve_in <= 0 or reserve_out <= 0:
            raise PumpFunError("Reserves must be positive")
            
        if amount_out >= reserve_out:
            raise PumpFunError("Output amount exceeds reserves")
        
        fee_bp = fee_basis_points or AMMCalculator.FEE_BASIS_POINTS
        
        # Calculate input using constant product formula
        numerator = reserve_in * amount_out * 10000
        denominator = (reserve_out - amount_out) * (10000 - fee_bp)
        
        amount_in = (numerator // denominator) + 1  # Add 1 for rounding
        
        return amount_in
    
    @staticmethod
    def calculate_price_impact(
        amount_in: int,
        reserve_in: int,
        reserve_out: int
    ) -> float:
        """
        Calculate price impact of a trade.
        
        Args:
            amount_in: Input amount
            reserve_in: Input token reserves
            reserve_out: Output token reserves
            
        Returns:
            Price impact as percentage
        """
        if reserve_in <= 0 or reserve_out <= 0:
            return 0.0
            
        # Price before trade
        price_before = reserve_out / reserve_in
        
        # Calculate amount out
        amount_out = AMMCalculator.get_amount_out(amount_in, reserve_in, reserve_out)
        
        # Price after trade
        new_reserve_in = reserve_in + amount_in
        new_reserve_out = reserve_out - amount_out
        
        if new_reserve_in <= 0 or new_reserve_out <= 0:
            return 100.0  # Maximum impact
            
        price_after = new_reserve_out / new_reserve_in
        
        # Calculate impact
        price_impact = abs(price_after - price_before) / price_before * 100
        
        return min(price_impact, 100.0)
    
    @staticmethod
    def calculate_liquidity_value(
        token_a_amount: int,
        token_b_amount: int,
        total_supply: int,
        user_lp_tokens: int
    ) -> Tuple[int, int]:
        """
        Calculate user's share of liquidity pool.
        
        Args:
            token_a_amount: Total token A in pool
            token_b_amount: Total token B in pool
            total_supply: Total LP token supply
            user_lp_tokens: User's LP tokens
            
        Returns:
            Tuple of (user_token_a_share, user_token_b_share)
        """
        if total_supply <= 0 or user_lp_tokens <= 0:
            return (0, 0)
            
        share_ratio = user_lp_tokens / total_supply
        
        user_token_a = int(token_a_amount * share_ratio)
        user_token_b = int(token_b_amount * share_ratio)
        
        return (user_token_a, user_token_b)
    
    @staticmethod
    def calculate_lp_tokens_to_mint(
        token_a_amount: int,
        token_b_amount: int,
        token_a_reserves: int,
        token_b_reserves: int,
        total_supply: int
    ) -> int:
        """
        Calculate LP tokens to mint for liquidity provision.
        
        Args:
            token_a_amount: Token A amount to add
            token_b_amount: Token B amount to add
            token_a_reserves: Current token A reserves
            token_b_reserves: Current token B reserves
            total_supply: Current LP token supply
            
        Returns:
            LP tokens to mint
        """
        if total_supply == 0:
            # Initial liquidity
            liquidity = int(math.sqrt(token_a_amount * token_b_amount))
            return max(liquidity - AMMCalculator.MINIMUM_LIQUIDITY, 0)
        
        # Calculate based on proportion
        liquidity_a = (token_a_amount * total_supply) // token_a_reserves
        liquidity_b = (token_b_amount * total_supply) // token_b_reserves
        
        return min(liquidity_a, liquidity_b)
    
    @staticmethod
    def calculate_optimal_swap_amount(
        user_amount_a: int,
        user_amount_b: int,
        reserve_a: int,
        reserve_b: int
    ) -> Tuple[int, int]:
        """
        Calculate optimal amounts to swap before adding liquidity.
        
        Args:
            user_amount_a: User's token A amount
            user_amount_b: User's token B amount
            reserve_a: Pool's token A reserves
            reserve_b: Pool's token B reserves
            
        Returns:
            Tuple of (optimal_amount_a, optimal_amount_b)
        """
        if reserve_a <= 0 or reserve_b <= 0:
            return (user_amount_a, user_amount_b)
            
        # Current pool ratio
        pool_ratio = reserve_b / reserve_a
        
        # User's current ratio
        if user_amount_a <= 0:
            return (0, user_amount_b)
        if user_amount_b <= 0:
            return (user_amount_a, 0)
            
        user_ratio = user_amount_b / user_amount_a
        
        if abs(user_ratio - pool_ratio) < 0.01:  # Already optimal
            return (user_amount_a, user_amount_b)
        
        # Calculate optimal distribution
        total_value_in_a = user_amount_a + (user_amount_b / pool_ratio)
        optimal_amount_a = int(total_value_in_a / (1 + pool_ratio))
        optimal_amount_b = int(optimal_amount_a * pool_ratio)
        
        return (optimal_amount_a, optimal_amount_b)


class LiquidityPool:
    """
    Represents a liquidity pool in the AMM.
    """
    
    def __init__(
        self,
        token_a_mint: PublicKey,
        token_b_mint: PublicKey,
        reserve_a: int = 0,
        reserve_b: int = 0,
        total_supply: int = 0,
        fee_basis_points: int = 100
    ):
        """
        Initialize liquidity pool.
        
        Args:
            token_a_mint: Token A mint address
            token_b_mint: Token B mint address
            reserve_a: Initial token A reserves
            reserve_b: Initial token B reserves
            total_supply: Initial LP token supply
            fee_basis_points: Trading fee in basis points
        """
        self.token_a_mint = token_a_mint
        self.token_b_mint = token_b_mint
        self.reserve_a = reserve_a
        self.reserve_b = reserve_b
        self.total_supply = total_supply
        self.fee_basis_points = fee_basis_points
        self.k = self.reserve_a * self.reserve_b  # Constant product
    
    def get_price(self, token_a_to_b: bool = True) -> float:
        """
        Get current price of token A in terms of token B (or vice versa).
        
        Args:
            token_a_to_b: If True, get price of A in B; if False, get price of B in A
            
        Returns:
            Current price
        """
        if self.reserve_a <= 0 or self.reserve_b <= 0:
            return 0.0
            
        if token_a_to_b:
            return self.reserve_b / self.reserve_a
        else:
            return self.reserve_a / self.reserve_b
    
    def simulate_swap(
        self,
        amount_in: int,
        token_a_to_b: bool = True
    ) -> Dict[str, Any]:
        """
        Simulate a swap without executing it.
        
        Args:
            amount_in: Input amount
            token_a_to_b: If True, swap A to B; if False, swap B to A
            
        Returns:
            Simulation results
        """
        if token_a_to_b:
            reserve_in, reserve_out = self.reserve_a, self.reserve_b
        else:
            reserve_in, reserve_out = self.reserve_b, self.reserve_a
            
        amount_out = AMMCalculator.get_amount_out(
            amount_in, reserve_in, reserve_out, self.fee_basis_points
        )
        
        price_impact = AMMCalculator.calculate_price_impact(
            amount_in, reserve_in, reserve_out
        )
        
        # Calculate effective price
        effective_price = amount_out / amount_in if amount_in > 0 else 0
        
        return {
            "amount_out": amount_out,
            "price_impact": price_impact,
            "effective_price": effective_price,
            "fee_amount": amount_in * self.fee_basis_points // 10000
        }
    
    def update_reserves(
        self,
        new_reserve_a: int,
        new_reserve_b: int
    ) -> None:
        """
        Update pool reserves.
        
        Args:
            new_reserve_a: New token A reserves
            new_reserve_b: New token B reserves
        """
        self.reserve_a = new_reserve_a
        self.reserve_b = new_reserve_b
        self.k = self.reserve_a * self.reserve_b
    
    def get_pool_info(self) -> Dict[str, Any]:
        """
        Get comprehensive pool information.
        
        Returns:
            Pool information dictionary
        """
        return {
            "token_a_mint": str(self.token_a_mint),
            "token_b_mint": str(self.token_b_mint),
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
            "total_supply": self.total_supply,
            "fee_basis_points": self.fee_basis_points,
            "price_a_to_b": self.get_price(True),
            "price_b_to_a": self.get_price(False),
            "constant_product": self.k
        }


class AMMManager:
    """
    Manages multiple AMM pools and routing.
    """
    
    def __init__(self):
        """Initialize AMM manager."""
        self.pools: Dict[str, LiquidityPool] = {}
    
    def add_pool(
        self,
        pool_id: str,
        pool: LiquidityPool
    ) -> None:
        """
        Add a liquidity pool.
        
        Args:
            pool_id: Unique pool identifier
            pool: LiquidityPool instance
        """
        self.pools[pool_id] = pool
    
    def get_pool(self, pool_id: str) -> Optional[LiquidityPool]:
        """
        Get a liquidity pool by ID.
        
        Args:
            pool_id: Pool identifier
            
        Returns:
            LiquidityPool instance or None
        """
        return self.pools.get(pool_id)
    
    def find_best_route(
        self,
        token_in: PublicKey,
        token_out: PublicKey,
        amount_in: int
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best route for a swap across multiple pools.
        
        Args:
            token_in: Input token mint
            token_out: Output token mint
            amount_in: Input amount
            
        Returns:
            Best route information or None
        """
        best_route = None
        best_amount_out = 0
        
        # Direct route
        for pool_id, pool in self.pools.items():
            if ((pool.token_a_mint == token_in and pool.token_b_mint == token_out) or
                (pool.token_b_mint == token_in and pool.token_a_mint == token_out)):
                
                token_a_to_b = pool.token_a_mint == token_in
                simulation = pool.simulate_swap(amount_in, token_a_to_b)
                
                if simulation["amount_out"] > best_amount_out:
                    best_amount_out = simulation["amount_out"]
                    best_route = {
                        "type": "direct",
                        "pools": [pool_id],
                        "amount_out": simulation["amount_out"],
                        "price_impact": simulation["price_impact"],
                        "route": [str(token_in), str(token_out)]
                    }
        
        # TODO: Implement multi-hop routing for indirect swaps
        
        return best_route
    
    def get_all_pools_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information for all pools.
        
        Returns:
            Dictionary of pool information
        """
        return {
            pool_id: pool.get_pool_info()
            for pool_id, pool in self.pools.items()
        }

