"""
Main client for PumpDotFun SDK.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction, TransactionInstruction, AccountMeta
from solana.system_program import (
    CreateAccountParams,
    TransferParams,
    create_account,
    transfer,
    SYS_PROGRAM_ID,
)

from .types import (
    CreateTokenMetadata,
    PriorityFee,
    TransactionResult,
    PumpFunEventType,
    BackendType,
    EventCallback,
    DEFAULT_COMMITMENT,
    DEFAULT_SLIPPAGE_BASIS_POINTS
)
from .utils import (
    create_metadata_uri,
    validate_slippage,
    wait_for_confirmation,
    calculate_slippage_amount,
    sol_to_lamports,
    TransactionError,
    ValidationError,
    NetworkError
)
from .events import EventManager
from .bonding_curve import BondingCurveCalculator, BondingCurveAccount

logger = logging.getLogger(__name__)


class PumpDotFunSDK:
    """
    Main SDK class for interacting with PumpFun protocol.
    """
    
    def __init__(
        self,
        rpc_endpoint: str,
        websocket_endpoint: Optional[str] = None,
        commitment: str = DEFAULT_COMMITMENT,
        portal_api_url: str = "https://pumpportal.fun/api",
        portal_api_key: Optional[str] = None,
    ):
        """
        Initialize PumpDotFun SDK.

        Args:
            rpc_endpoint: Solana RPC endpoint URL
            websocket_endpoint: WebSocket endpoint for events (optional)
            commitment: Default commitment level
            portal_api_url: Base URL for PumpPortal API
            portal_api_key: Optional API key for PumpPortal
        """
        self.rpc_client = AsyncClient(rpc_endpoint, commitment=Commitment(commitment))
        self.commitment = commitment
        self.portal_api_url = portal_api_url.rstrip("/")
        self.portal_api_key = portal_api_key
        
        # Initialize event manager if websocket endpoint provided
        if websocket_endpoint:
            self.event_manager = EventManager(self.rpc_client, websocket_endpoint)
        else:
            self.event_manager = None
            
        # PumpFun program constants (these would need to be actual values)
        self.PUMP_FUN_PROGRAM_ID = PublicKey("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
        self.PUMP_FUN_AUTHORITY = PublicKey("TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM")
        
        logger.info(f"Initialized PumpDotFun SDK with endpoint: {rpc_endpoint}")
    
    async def create_and_buy(
        self,
        creator: Keypair,
        mint: Keypair,
        token_metadata: CreateTokenMetadata,
        buy_amount_sol: float,
        slippage_basis_points: int = DEFAULT_SLIPPAGE_BASIS_POINTS,
        priority_fees: Optional[PriorityFee] = None,
        commitment: str = None,
        simulate: bool = False,
        backend: BackendType = BackendType.ON_CHAIN,
    ) -> TransactionResult:
        """
        Create a new token and buy it immediately.
        
        Args:
            creator: Keypair of the token creator
            mint: Keypair for the mint account
            token_metadata: Token metadata
            buy_amount_sol: Amount of SOL to spend on buying
            slippage_basis_points: Slippage tolerance in basis points
            priority_fees: Priority fee configuration
            commitment: Transaction commitment level
            
        Returns:
            Transaction result
        """
        try:
            # Validate inputs
            if not validate_slippage(slippage_basis_points):
                raise ValidationError("Invalid slippage value")
                
            if buy_amount_sol <= 0:
                raise ValidationError("Buy amount must be positive")
            
            commitment = commitment or self.commitment
            buy_amount_lamports = sol_to_lamports(buy_amount_sol)
            
            logger.info(f"Creating and buying token: {token_metadata.symbol}")
            
            # Step 1: Create the token
            create_result = await self._create_token(
                creator, mint, token_metadata, commitment, simulate, backend
            )

            if not create_result.success:
                return create_result

            # Step 2: Buy the token
            buy_result = await self.buy(
                creator,
                mint.public_key,
                buy_amount_sol,
                slippage_basis_points,
                priority_fees,
                commitment,
                simulate=simulate,
                backend=backend,
            )
            
            # Combine results
            return TransactionResult(
                success=buy_result.success,
                signature=buy_result.signature,
                error=buy_result.error,
                results={
                    "create_signature": create_result.signature,
                    "buy_signature": buy_result.signature,
                    "mint": str(mint.public_key),
                    "token_metadata": token_metadata.__dict__
                }
            )
            
        except Exception as e:
            logger.error(f"Error in create_and_buy: {e}")
            return TransactionResult(
                success=False,
                error=str(e)
            )
    
    async def buy(
        self,
        buyer: Keypair,
        mint: PublicKey,
        buy_amount_sol: float,
        slippage_basis_points: int = DEFAULT_SLIPPAGE_BASIS_POINTS,
        priority_fees: Optional[PriorityFee] = None,
        commitment: str = None,
        simulate: bool = False,
        backend: BackendType = BackendType.ON_CHAIN,
    ) -> TransactionResult:
        """
        Buy tokens from PumpFun.
        
        Args:
            buyer: Keypair of the buyer
            mint: Public key of the token mint
            buy_amount_sol: Amount of SOL to spend
            slippage_basis_points: Slippage tolerance in basis points
            priority_fees: Priority fee configuration
            commitment: Transaction commitment level
            
        Returns:
            Transaction result
        """
        try:
            # Validate inputs
            if not validate_slippage(slippage_basis_points):
                raise ValidationError("Invalid slippage value")
                
            if buy_amount_sol <= 0:
                raise ValidationError("Buy amount must be positive")
            
            commitment = commitment or self.commitment
            buy_amount_lamports = sol_to_lamports(buy_amount_sol)

            logger.info(f"Buying {buy_amount_sol} SOL worth of {mint}")

            if backend == BackendType.PUMP_PORTAL:
                payload = {
                    "mint": str(mint),
                    "amount": buy_amount_lamports,
                    "slippage": slippage_basis_points,
                }
                if simulate:
                    payload["simulate"] = True
                try:
                    resp = await self._portal_request("post", "trade/buy", payload)
                    return TransactionResult(
                        success=resp.get("success", True),
                        signature=resp.get("signature"),
                        results=resp,
                    )
                except Exception as e:
                    return TransactionResult(success=False, error=str(e))

            if simulate:
                transaction = Transaction(fee_payer=buyer.public_key)
                transaction.add(
                    transfer(
                        TransferParams(
                            from_pubkey=buyer.public_key,
                            to_pubkey=mint,
                            lamports=buy_amount_lamports,
                        )
                    )
                )

                signature = await self._send_transaction(transaction, [buyer])
                confirmed = await wait_for_confirmation(
                    self.rpc_client, signature, commitment
                )
                if not confirmed:
                    raise TransactionError("Transaction not confirmed within timeout")

                return TransactionResult(
                    success=True,
                    signature=signature,
                    results={
                        "mint": str(mint),
                        "buy_amount_sol": buy_amount_sol,
                    },
                )

            # Simulated path skipped; placeholder for full implementation
            bonding_curve_account = await self._get_bonding_curve_account(mint)
            expected_tokens = BondingCurveCalculator.get_buy_price(
                buy_amount_lamports,
                bonding_curve_account.real_sol_reserves,
                bonding_curve_account.real_token_reserves,
            )
            min_tokens_out = calculate_slippage_amount(
                expected_tokens, slippage_basis_points, is_minimum=True
            )
            transaction = await self._build_buy_transaction(
                buyer,
                mint,
                buy_amount_lamports,
                min_tokens_out,
                priority_fees,
            )
            signature = await self._send_transaction(transaction, [buyer])
            confirmed = await wait_for_confirmation(
                self.rpc_client, signature, commitment
            )
            if not confirmed:
                raise TransactionError("Transaction not confirmed within timeout")
            return TransactionResult(
                success=True,
                signature=signature,
                results={
                    "mint": str(mint),
                    "buy_amount_sol": buy_amount_sol,
                    "expected_tokens": expected_tokens,
                    "min_tokens_out": min_tokens_out,
                },
            )
            
        except Exception as e:
            logger.error(f"Error in buy: {e}")
            return TransactionResult(
                success=False,
                error=str(e)
            )
    
    async def sell(
        self,
        seller: Keypair,
        mint: PublicKey,
        sell_token_amount: int,
        slippage_basis_points: int = DEFAULT_SLIPPAGE_BASIS_POINTS,
        priority_fees: Optional[PriorityFee] = None,
        commitment: str = None,
        mint_authority: Optional[Keypair] = None,
        simulate: bool = False,
        backend: BackendType = BackendType.ON_CHAIN,
    ) -> TransactionResult:
        """
        Sell tokens to PumpFun.
        
        Args:
            seller: Keypair of the seller
            mint: Public key of the token mint
            sell_token_amount: Amount of tokens to sell
            slippage_basis_points: Slippage tolerance in basis points
            priority_fees: Priority fee configuration
            commitment: Transaction commitment level
            
        Returns:
            Transaction result
        """
        try:
            # Validate inputs
            if not validate_slippage(slippage_basis_points):
                raise ValidationError("Invalid slippage value")
                
            if sell_token_amount <= 0:
                raise ValidationError("Sell amount must be positive")
            
            commitment = commitment or self.commitment

            logger.info(f"Selling {sell_token_amount} tokens of {mint}")

            if backend == BackendType.PUMP_PORTAL:
                payload = {
                    "mint": str(mint),
                    "amount": sell_token_amount,
                    "slippage": slippage_basis_points,
                }
                if simulate:
                    payload["simulate"] = True
                try:
                    resp = await self._portal_request("post", "trade/sell", payload)
                    return TransactionResult(
                        success=resp.get("success", True),
                        signature=resp.get("signature"),
                        results=resp,
                    )
                except Exception as e:
                    return TransactionResult(success=False, error=str(e))

            if simulate:
                if not mint_authority:
                    raise ValidationError("mint_authority required for simulation")
                transaction = Transaction(fee_payer=seller.public_key)
                transaction.add(
                    transfer(
                        TransferParams(
                            from_pubkey=mint_authority.public_key,
                            to_pubkey=seller.public_key,
                            lamports=sell_token_amount,
                        )
                    )
                )
                signature = await self._send_transaction(
                    transaction, [seller, mint_authority]
                )
                confirmed = await wait_for_confirmation(
                    self.rpc_client, signature, commitment
                )
                if not confirmed:
                    raise TransactionError("Transaction not confirmed within timeout")
                return TransactionResult(
                    success=True,
                    signature=signature,
                    results={
                        "mint": str(mint),
                        "sell_token_amount": sell_token_amount,
                    },
                )

            # Simulated path skipped; placeholder for full implementation
            bonding_curve_account = await self._get_bonding_curve_account(mint)
            expected_sol = BondingCurveCalculator.get_sell_price(
                sell_token_amount,
                bonding_curve_account.real_sol_reserves,
                bonding_curve_account.real_token_reserves,
            )
            min_sol_out = calculate_slippage_amount(
                expected_sol, slippage_basis_points, is_minimum=True
            )
            transaction = await self._build_sell_transaction(
                seller,
                mint,
                sell_token_amount,
                min_sol_out,
                priority_fees,
            )
            signature = await self._send_transaction(transaction, [seller])
            confirmed = await wait_for_confirmation(
                self.rpc_client, signature, commitment
            )
            if not confirmed:
                raise TransactionError("Transaction not confirmed within timeout")
            return TransactionResult(
                success=True,
                signature=signature,
                results={
                    "mint": str(mint),
                    "sell_token_amount": sell_token_amount,
                    "expected_sol": expected_sol,
                    "min_sol_out": min_sol_out,
                },
            )
            
        except Exception as e:
            logger.error(f"Error in sell: {e}")
            return TransactionResult(
                success=False,
                error=str(e)
            )
    
    def add_event_listener(
        self,
        event_type: PumpFunEventType,
        callback: EventCallback
    ) -> int:
        """
        Add an event listener.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function
            
        Returns:
            Listener ID
        """
        if not self.event_manager:
            raise NetworkError("WebSocket endpoint not configured for events")
            
        return self.event_manager.add_listener(event_type, callback)
    
    def remove_event_listener(self, event_id: int) -> None:
        """
        Remove an event listener.
        
        Args:
            event_id: ID of the listener to remove
        """
        if not self.event_manager:
            raise NetworkError("WebSocket endpoint not configured for events")
            
        self.event_manager.remove_listener(event_id)
    
    async def start_event_listening(self) -> None:
        """Start listening for events."""
        if not self.event_manager:
            raise NetworkError("WebSocket endpoint not configured for events")
            
        await self.event_manager.start_listening()
    
    def stop_event_listening(self) -> None:
        """Stop listening for events."""
        if self.event_manager:
            self.event_manager.stop_listening()
    
    # Private helper methods
    
    async def _create_token(
        self,
        creator: Keypair,
        mint: Keypair,
        metadata: CreateTokenMetadata,
        commitment: str,
        simulate: bool = False,
        backend: BackendType = BackendType.ON_CHAIN,
    ) -> TransactionResult:
        """Create a new token."""
        try:
            if backend == BackendType.PUMP_PORTAL:
                payload = {
                    "name": metadata.name,
                    "symbol": metadata.symbol,
                    "description": metadata.description,
                    "image": metadata.image,
                    "mint": str(mint.public_key),
                    "creator": str(creator.public_key),
                }
                if simulate:
                    payload["simulate"] = True
                try:
                    resp = await self._portal_request("post", "token/create", payload)
                    return TransactionResult(
                        success=resp.get("success", True),
                        signature=resp.get("signature"),
                        results=resp,
                    )
                except Exception as e:
                    return TransactionResult(success=False, error=str(e))

            transaction = Transaction(fee_payer=creator.public_key)

            if simulate:
                rent = await self.rpc_client.get_minimum_balance_for_rent_exemption(0)
                lamports = rent.value + 1_000_000
                transaction.add(
                    create_account(
                        CreateAccountParams(
                            from_pubkey=creator.public_key,
                            new_account_pubkey=mint.public_key,
                            lamports=lamports,
                            space=0,
                            program_id=SYS_PROGRAM_ID,
                        )
                    )
                )
            else:
                instruction = TransactionInstruction(
                    program_id=self.PUMP_FUN_PROGRAM_ID,
                    data=b"create",
                    keys=[
                        AccountMeta(pubkey=creator.public_key, is_signer=True, is_writable=True),
                        AccountMeta(pubkey=mint.public_key, is_signer=True, is_writable=True),
                    ],
                )
                transaction.add(instruction)

            signature = await self._send_transaction(transaction, [creator, mint])

            confirmed = await wait_for_confirmation(
                self.rpc_client, signature, commitment
            )

            return TransactionResult(
                success=confirmed,
                signature=signature if confirmed else None,
                error=None if confirmed else "Token creation failed",
                results={"mint": str(mint.public_key)},
            )

        except Exception as e:
            return TransactionResult(success=False, error=str(e))
    
    async def _build_buy_transaction(
        self,
        buyer: Keypair,
        mint: PublicKey,
        sol_amount: int,
        min_tokens_out: int,
        priority_fees: Optional[PriorityFee]
    ) -> Transaction:
        """Build buy transaction."""
        transaction = Transaction()

        instruction = TransactionInstruction(
            program_id=self.PUMP_FUN_PROGRAM_ID,
            data=b"buy",
            keys=[
                AccountMeta(pubkey=buyer.public_key, is_signer=True, is_writable=True),
                AccountMeta(pubkey=mint, is_signer=False, is_writable=True),
            ],
        )
        transaction.add(instruction)
        return transaction
    
    async def _build_sell_transaction(
        self,
        seller: Keypair,
        mint: PublicKey,
        token_amount: int,
        min_sol_out: int,
        priority_fees: Optional[PriorityFee]
    ) -> Transaction:
        """Build sell transaction."""
        transaction = Transaction()

        instruction = TransactionInstruction(
            program_id=self.PUMP_FUN_PROGRAM_ID,
            data=b"sell",
            keys=[
                AccountMeta(pubkey=seller.public_key, is_signer=True, is_writable=True),
                AccountMeta(pubkey=mint, is_signer=False, is_writable=True),
            ],
        )
        transaction.add(instruction)
        return transaction
    
    async def _send_transaction(
        self,
        transaction: Transaction,
        signers: list[Keypair]
    ) -> str:
        """Send transaction to Solana."""
        try:
            # Get recent blockhash
            recent_blockhash = await self.rpc_client.get_latest_blockhash()
            transaction.recent_blockhash = str(recent_blockhash.value.blockhash)
            
            # Send transaction
            response = await self.rpc_client.send_transaction(transaction, *signers)
            
            if hasattr(response, 'value'):
                return response.value
            else:
                raise TransactionError("Failed to send transaction")
                
        except Exception as e:
            raise TransactionError(f"Transaction failed: {e}")

    async def _portal_request(self, method: str, endpoint: str, json: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the PumpPortal API."""
        url = f"{self.portal_api_url}/{endpoint.lstrip('/') }"
        headers = {}
        if self.portal_api_key:
            headers["X-API-KEY"] = self.portal_api_key
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _get_bonding_curve_account(self, mint: PublicKey) -> BondingCurveAccount:
        """Get bonding curve account for a mint."""
        try:
            # Derive bonding curve account address
            bonding_curve_address = self._derive_bonding_curve_address(mint)
            
            # Fetch account data
            account_info = await self.rpc_client.get_account_info(bonding_curve_address)
            
            if not account_info.value:
                raise NetworkError("Bonding curve account not found")
            
            # Parse account data
            account_data = self._parse_bonding_curve_data(account_info.value.data)
            
            return BondingCurveAccount(account_data)
            
        except Exception as e:
            raise NetworkError(f"Failed to get bonding curve account: {e}")
    
    def _derive_bonding_curve_address(self, mint: PublicKey) -> PublicKey:
        """Derive bonding curve account address."""
        # This would implement the actual derivation logic
        # based on PumpFun's program
        seeds = [b"bonding-curve", bytes(mint)]
        address, _ = PublicKey.find_program_address(seeds, self.PUMP_FUN_PROGRAM_ID)
        return address
    
    def _parse_bonding_curve_data(self, data: bytes) -> Dict[str, Any]:
        """Parse bonding curve account data."""
        # This would implement actual parsing based on PumpFun's account structure
        # Placeholder implementation
        return {
            "virtualTokenReserves": 1_073_000_000_000_000,
            "virtualSolReserves": 30_000_000_000,
            "realTokenReserves": 800_000_000_000_000,
            "realSolReserves": 0,
            "tokenTotalSupply": 1_000_000_000_000_000,
            "complete": False
        }
    
    async def close(self) -> None:
        """Close the SDK and cleanup resources."""
        if self.event_manager:
            self.event_manager.stop_listening()
            
        await self.rpc_client.close()
        logger.info("PumpDotFun SDK closed")

