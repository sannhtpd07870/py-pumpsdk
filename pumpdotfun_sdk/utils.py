"""
Utility functions for PumpDotFun SDK.
"""

import json
import base64
import time
import logging
from typing import Dict, Any, Optional
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment as SolanaCommitment
from .types import CreateTokenMetadata, LAMPORTS_PER_SOL

logger = logging.getLogger(__name__)


def create_metadata_uri(metadata: CreateTokenMetadata) -> str:
    """
    Create metadata URI for a token.
    
    Args:
        metadata: Token metadata
        
    Returns:
        JSON string representation of metadata
    """
    metadata_dict = {
        "name": metadata.name,
        "symbol": metadata.symbol,
        "description": metadata.description,
        "image": metadata.image,
        "showName": metadata.show_name,
        "createdOn": metadata.created_on or str(int(time.time())),
    }
    
    # Add optional social links
    if metadata.twitter:
        metadata_dict["twitter"] = metadata.twitter
    if metadata.telegram:
        metadata_dict["telegram"] = metadata.telegram
    if metadata.website:
        metadata_dict["website"] = metadata.website
        
    return json.dumps(metadata_dict)


def validate_slippage(slippage_basis_points: int) -> bool:
    """
    Validate slippage value.
    
    Args:
        slippage_basis_points: Slippage in basis points
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= slippage_basis_points <= 10000  # 0% to 100%


def format_sol_amount(lamports: int) -> float:
    """
    Convert lamports to SOL.
    
    Args:
        lamports: Amount in lamports
        
    Returns:
        Amount in SOL
    """
    return lamports / LAMPORTS_PER_SOL


def format_token_amount(raw_amount: int, decimals: int) -> float:
    """
    Convert raw token amount to formatted amount.
    
    Args:
        raw_amount: Raw token amount
        decimals: Number of decimal places
        
    Returns:
        Formatted token amount
    """
    return raw_amount / (10 ** decimals)


def sol_to_lamports(sol_amount: float) -> int:
    """
    Convert SOL to lamports.
    
    Args:
        sol_amount: Amount in SOL
        
    Returns:
        Amount in lamports
    """
    return int(sol_amount * LAMPORTS_PER_SOL)


async def wait_for_confirmation(
    rpc_client: AsyncClient,
    signature: str,
    commitment: str = "confirmed",
    timeout: int = 60
) -> bool:
    """
    Wait for transaction confirmation.
    
    Args:
        rpc_client: Solana RPC client
        signature: Transaction signature
        commitment: Commitment level
        timeout: Timeout in seconds
        
    Returns:
        True if confirmed, False if timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = await rpc_client.get_signature_statuses([signature])
            
            if response.value and response.value[0]:
                status = response.value[0]
                if status.confirmation_status and status.confirmation_status.value >= SolanaCommitment(commitment).value:
                    return True
                    
        except Exception as e:
            logger.warning(f"Error checking transaction status: {e}")
            
        await asyncio.sleep(1)
        
    return False


def calculate_slippage_amount(
    expected_amount: int,
    slippage_basis_points: int,
    is_minimum: bool = True
) -> int:
    """
    Calculate slippage amount.
    
    Args:
        expected_amount: Expected amount
        slippage_basis_points: Slippage in basis points
        is_minimum: If True, calculate minimum amount; if False, calculate maximum
        
    Returns:
        Amount with slippage applied
    """
    slippage_multiplier = slippage_basis_points / 10000
    
    if is_minimum:
        return int(expected_amount * (1 - slippage_multiplier))
    else:
        return int(expected_amount * (1 + slippage_multiplier))


def encode_instruction_data(data: Dict[str, Any]) -> bytes:
    """
    Encode instruction data for Solana transactions.
    
    Args:
        data: Instruction data dictionary
        
    Returns:
        Encoded bytes
    """
    # This would need to be implemented based on the specific
    # instruction format used by PumpFun
    return json.dumps(data).encode('utf-8')


def decode_account_data(data: str) -> Dict[str, Any]:
    """
    Decode account data from base64.
    
    Args:
        data: Base64 encoded account data
        
    Returns:
        Decoded data dictionary
    """
    try:
        decoded_bytes = base64.b64decode(data)
        # This would need specific parsing based on PumpFun's account structure
        return {"raw_data": decoded_bytes}
    except Exception as e:
        logger.error(f"Error decoding account data: {e}")
        return {}


class PumpFunError(Exception):
    """Base exception for PumpFun SDK."""
    pass


class TransactionError(PumpFunError):
    """Transaction-related error."""
    pass


class ValidationError(PumpFunError):
    """Data validation error."""
    pass


class NetworkError(PumpFunError):
    """Network-related error."""
    pass

