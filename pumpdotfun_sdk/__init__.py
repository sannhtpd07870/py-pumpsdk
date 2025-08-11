"""
PumpDotFun SDK for Python

A Python SDK for interacting with the PumpFun protocol on Solana.
"""

from .client import PumpDotFunSDK
from .types import (
    CreateTokenMetadata,
    PriorityFee,
    TransactionResult,
    PumpFunEventType,
    BackendType,
    CreateEvent,
    TradeEvent,
    CompleteEvent
)

__version__ = "1.0.0"
__author__ = "Manus AI"

__all__ = [
    "PumpDotFunSDK",
    "CreateTokenMetadata",
    "PriorityFee",
    "TransactionResult",
    "PumpFunEventType",
    "BackendType",
    "CreateEvent",
    "TradeEvent",
    "CompleteEvent"
]

