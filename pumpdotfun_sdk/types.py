"""
Type definitions for PumpDotFun SDK.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from enum import Enum
from solana.publickey import PublicKey


@dataclass
class CreateTokenMetadata:
    """Metadata for creating a new token."""
    name: str
    symbol: str
    description: str
    image: str
    show_name: bool = True
    created_on: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    website: Optional[str] = None


@dataclass
class PriorityFee:
    """Priority fee configuration."""
    unit_limit: Optional[int] = None
    unit_price: Optional[int] = None


@dataclass
class TransactionResult:
    """Result of a transaction."""
    success: bool
    signature: Optional[str] = None
    error: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class PumpFunEventType(Enum):
    """PumpFun event types."""
    CREATE_EVENT = "createEvent"
    TRADE_EVENT = "tradeEvent"
    COMPLETE_EVENT = "completeEvent"


class BackendType(Enum):
    """Available backends for executing trades."""
    PUMP_PORTAL = "pump_portal"
    ON_CHAIN = "on_chain"


@dataclass
class CreateEvent:
    """Token creation event."""
    mint: PublicKey
    name: str
    symbol: str
    uri: str
    user: PublicKey
    timestamp: int


@dataclass
class TradeEvent:
    """Trade event."""
    mint: PublicKey
    user: PublicKey
    is_buy: bool
    sol_amount: int
    token_amount: int
    timestamp: int


@dataclass
class CompleteEvent:
    """Completion event."""
    mint: PublicKey
    user: PublicKey
    timestamp: int


# Type aliases
EventCallback = Callable[[Any, int, str], None]
Commitment = str
Finality = str

# Constants
DEFAULT_COMMITMENT = "confirmed"
DEFAULT_FINALITY = "confirmed"
DEFAULT_SLIPPAGE_BASIS_POINTS = 500
LAMPORTS_PER_SOL = 1_000_000_000

