# PumpDotFun SDK Python

A comprehensive Python SDK for interacting with the PumpFun protocol on Solana blockchain. This SDK provides a complete implementation of all PumpFun functionality, including token creation, trading, and event monitoring.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

PumpDotFun SDK Python is a faithful recreation of the original TypeScript PumpDotFun SDK, built specifically for Python developers who want to interact with the PumpFun protocol on Solana. The SDK maintains full compatibility with the original API while leveraging Python's strengths and ecosystem.

The PumpFun protocol is a decentralized platform for creating and trading meme tokens on Solana, featuring an innovative bonding curve mechanism that allows for fair token launches and automated market making. This SDK provides developers with all the tools necessary to build applications that interact with PumpFun's smart contracts.

## Features

### Core Functionality
- **Token Creation**: Create new tokens with metadata and automatic bonding curve setup
- **Token Trading**: Buy and sell tokens through the bonding curve mechanism
- **Event Monitoring**: Real-time event listening for token creation, trades, and curve completion
- **Slippage Protection**: Built-in slippage tolerance and price impact calculations
- **Priority Fees**: Support for priority fees to ensure transaction inclusion

### Advanced Features
- **Bonding Curve Mathematics**: Complete implementation of PumpFun's bonding curve calculations
- **AMM Integration**: Automated Market Maker functionality for liquidity management
- **Global Account Management**: Access to protocol-wide statistics and configuration
- **Async/Await Support**: Full asynchronous operation for optimal performance
- **Error Handling**: Comprehensive error handling with custom exception types
- **Type Safety**: Full type annotations for better development experience

### Developer Experience
- **Comprehensive Documentation**: Detailed API documentation with examples
- **Unit Tests**: Extensive test suite covering all functionality
- **Examples**: Ready-to-use examples for common use cases
- **Type Hints**: Complete type annotations for IDE support
- **Logging**: Built-in logging for debugging and monitoring

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from PyPI (Coming Soon)

```bash
pip install pumpdotfun-sdk-py
```

### Install from Source

```bash
git clone https://github.com/your-repo/pumpdotfun-sdk-py.git
cd pumpdotfun-sdk-py
pip install -r requirements.txt
pip install -e .
```

### Dependencies

The SDK requires the following main dependencies:

- `solana==0.28.1` - Solana Python client (stable version for reliability)
- `websockets` - WebSocket client for real-time events
- `httpx` - HTTP client for RPC calls

## Quick Start

### Basic Setup

```python
import asyncio
from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import CreateTokenMetadata
from solana.keypair import Keypair

# Initialize the SDK
sdk = PumpDotFunSDK(
    rpc_endpoint="https://api.mainnet-beta.solana.com",
    websocket_endpoint="wss://api.mainnet-beta.solana.com"
)

# Create keypairs
creator = Keypair()
mint = Keypair()

# Define token metadata
metadata = CreateTokenMetadata(
    name="My Awesome Token",
    symbol="MAT",
    description="An awesome token created with PumpDotFun SDK",
    image="https://example.com/token-image.png",
    website="https://myawesometoken.com",
    twitter="@myawesometoken"
)

async def main():
    # Create and buy a token
    result = await sdk.create_and_buy(
        creator=creator,
        mint=mint,
        token_metadata=metadata,
        buy_amount_sol=1.0,  # Buy 1 SOL worth of tokens
        slippage_basis_points=500  # 5% slippage tolerance
    )
    
    if result.success:
        print(f"Token created and purchased! Signature: {result.signature}")
        print(f"Mint address: {result.results['mint']}")
    else:
        print(f"Transaction failed: {result.error}")

# Run the example
asyncio.run(main())
```

### Event Monitoring

```python
from pumpdotfun_sdk.types import PumpFunEventType

def on_trade_event(event, slot, signature):
    print(f"Trade detected: {event.sol_amount} SOL for {event.token_amount} tokens")
    print(f"Buy: {event.is_buy}, User: {event.user}")

async def monitor_events():
    # Add event listener
    listener_id = sdk.add_event_listener(
        PumpFunEventType.TRADE_EVENT,
        on_trade_event
    )
    
    # Start listening
    await sdk.start_event_listening()
    
    # Keep the program running
    await asyncio.sleep(60)  # Listen for 60 seconds
    
    # Clean up
    sdk.remove_event_listener(listener_id)
    sdk.stop_event_listening()

asyncio.run(monitor_events())
```

## API Reference

### PumpDotFunSDK Class

The main SDK class that provides all functionality for interacting with PumpFun.

#### Constructor

```python
PumpDotFunSDK(
    rpc_endpoint: str,
    websocket_endpoint: Optional[str] = None,
    commitment: str = "confirmed"
)
```

**Parameters:**
- `rpc_endpoint`: Solana RPC endpoint URL
- `websocket_endpoint`: WebSocket endpoint for real-time events (optional)
- `commitment`: Default commitment level for transactions

#### Methods

##### create_and_buy()

Creates a new token and immediately purchases a specified amount.

```python
async def create_and_buy(
    creator: Keypair,
    mint: Keypair,
    token_metadata: CreateTokenMetadata,
    buy_amount_sol: float,
    slippage_basis_points: int = 500,
    priority_fees: Optional[PriorityFee] = None,
    commitment: str = None
) -> TransactionResult
```

**Parameters:**
- `creator`: Keypair of the token creator
- `mint`: Keypair for the mint account
- `token_metadata`: Token metadata including name, symbol, description, and image
- `buy_amount_sol`: Amount of SOL to spend on initial purchase
- `slippage_basis_points`: Slippage tolerance in basis points (default: 500 = 5%)
- `priority_fees`: Priority fee configuration (optional)
- `commitment`: Transaction commitment level (optional)

**Returns:** `TransactionResult` object containing success status, signature, and additional data

##### buy()

Purchases tokens from an existing PumpFun token.

```python
async def buy(
    buyer: Keypair,
    mint: PublicKey,
    buy_amount_sol: float,
    slippage_basis_points: int = 500,
    priority_fees: Optional[PriorityFee] = None,
    commitment: str = None
) -> TransactionResult
```

**Parameters:**
- `buyer`: Keypair of the buyer
- `mint`: Public key of the token mint
- `buy_amount_sol`: Amount of SOL to spend
- `slippage_basis_points`: Slippage tolerance in basis points
- `priority_fees`: Priority fee configuration (optional)
- `commitment`: Transaction commitment level (optional)

**Returns:** `TransactionResult` object

##### sell()

Sells tokens back to the bonding curve.

```python
async def sell(
    seller: Keypair,
    mint: PublicKey,
    sell_token_amount: int,
    slippage_basis_points: int = 500,
    priority_fees: Optional[PriorityFee] = None,
    commitment: str = None
) -> TransactionResult
```

**Parameters:**
- `seller`: Keypair of the seller
- `mint`: Public key of the token mint
- `sell_token_amount`: Amount of tokens to sell (in raw units)
- `slippage_basis_points`: Slippage tolerance in basis points
- `priority_fees`: Priority fee configuration (optional)
- `commitment`: Transaction commitment level (optional)

**Returns:** `TransactionResult` object

##### Event Management

```python
def add_event_listener(
    event_type: PumpFunEventType,
    callback: EventCallback
) -> int

def remove_event_listener(event_id: int) -> None

async def start_event_listening() -> None

def stop_event_listening() -> None
```

### Type Definitions

#### CreateTokenMetadata

```python
@dataclass
class CreateTokenMetadata:
    name: str
    symbol: str
    description: str
    image: str
    show_name: bool = True
    created_on: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    website: Optional[str] = None
```

#### TransactionResult

```python
@dataclass
class TransactionResult:
    success: bool
    signature: Optional[str] = None
    error: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
```

#### PumpFunEventType

```python
class PumpFunEventType(Enum):
    CREATE_EVENT = "createEvent"
    TRADE_EVENT = "tradeEvent"
    COMPLETE_EVENT = "completeEvent"
```

## Examples

The SDK includes comprehensive examples demonstrating various use cases:

### Token Creation Example

```python
# examples/create_and_buy.py
import asyncio
from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import CreateTokenMetadata
from solana.keypair import Keypair

async def create_token_example():
    sdk = PumpDotFunSDK("https://api.devnet.solana.com")
    
    creator = Keypair()
    mint = Keypair()
    
    metadata = CreateTokenMetadata(
        name="Example Token",
        symbol="EXAMPLE",
        description="A token created for demonstration",
        image="https://example.com/image.png"
    )
    
    result = await sdk.create_and_buy(
        creator=creator,
        mint=mint,
        token_metadata=metadata,
        buy_amount_sol=0.1
    )
    
    print(f"Result: {result.success}")
    if result.success:
        print(f"Mint: {result.results['mint']}")

asyncio.run(create_token_example())
```

### Trading Example

```python
# examples/buy_token.py
import asyncio
from pumpdotfun_sdk import PumpDotFunSDK
from solana.keypair import Keypair
from solana.publickey import PublicKey

async def buy_token_example():
    sdk = PumpDotFunSDK("https://api.devnet.solana.com")
    
    buyer = Keypair()
    mint = Pubkey.from_string("YourTokenMintAddressHere")
    
    result = await sdk.buy(
        buyer=buyer,
        mint=mint,
        buy_amount_sol=0.5,
        slippage_basis_points=1000  # 10% slippage
    )
    
    print(f"Purchase result: {result.success}")

asyncio.run(buy_token_example())
```

### Event Monitoring Example

```python
# examples/event_listener.py
import asyncio
from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import PumpFunEventType

def on_create_event(event, slot, signature):
    print(f"New token created: {event.name} ({event.symbol})")
    print(f"Mint: {event.mint}")

def on_trade_event(event, slot, signature):
    action = "BUY" if event.is_buy else "SELL"
    print(f"{action}: {event.sol_amount} SOL for {event.token_amount} tokens")

async def monitor_events():
    sdk = PumpDotFunSDK(
        "https://api.mainnet-beta.solana.com",
        "wss://api.mainnet-beta.solana.com"
    )
    
    # Add listeners
    create_listener = sdk.add_event_listener(
        PumpFunEventType.CREATE_EVENT,
        on_create_event
    )
    
    trade_listener = sdk.add_event_listener(
        PumpFunEventType.TRADE_EVENT,
        on_trade_event
    )
    
    # Start monitoring
    await sdk.start_event_listening()
    
    # Monitor for 5 minutes
    await asyncio.sleep(300)
    
    # Cleanup
    sdk.remove_event_listener(create_listener)
    sdk.remove_event_listener(trade_listener)
    sdk.stop_event_listening()

asyncio.run(monitor_events())
```

## Testing

The SDK includes a comprehensive test suite covering all functionality.

### Running Tests

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test module
python -m unittest tests.test_client -v

# Run specific test class
python -m unittest tests.test_utils.TestValidationUtils -v

# Run specific test method
python -m unittest tests.test_utils.TestValidationUtils.test_validate_slippage_valid_values -v
```

### Test Coverage

The test suite includes:

- **Unit Tests**: Testing individual components and functions
- **Integration Tests**: Testing component interactions
- **Mock Tests**: Testing with simulated blockchain responses
- **Error Handling Tests**: Testing error conditions and edge cases
- **Async Tests**: Testing asynchronous functionality

### Test Structure

```
tests/
├── __init__.py
├── test_client.py      # Main SDK functionality tests
├── test_utils.py       # Utility function tests
├── test_events.py      # Event handling tests
└── test_bonding_curve.py  # Bonding curve calculation tests
```

## Error Handling

The SDK provides comprehensive error handling with custom exception types:

### Exception Hierarchy

```python
PumpFunError                    # Base exception
├── TransactionError           # Transaction-related errors
├── ValidationError            # Input validation errors
└── NetworkError              # Network and RPC errors
```

### Example Error Handling

```python
from pumpdotfun_sdk.utils import TransactionError, ValidationError

try:
    result = await sdk.buy(buyer, mint, -1.0)  # Invalid amount
except ValidationError as e:
    print(f"Validation error: {e}")
except TransactionError as e:
    print(f"Transaction failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Solana RPC Configuration
RPC_ENDPOINT=https://api.mainnet-beta.solana.com
WEBSOCKET_ENDPOINT=wss://api.mainnet-beta.solana.com

# Private key for transactions (base58 encoded)
PRIVATE_KEY=your_base58_encoded_private_key_here

# Default settings
COMMITMENT=confirmed
DEFAULT_SLIPPAGE=500
```

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set SDK log level
logging.getLogger('pumpdotfun_sdk').setLevel(logging.DEBUG)
```

## Performance Considerations

### Async Best Practices

The SDK is built with async/await patterns for optimal performance:

```python
# Good: Use async context
async def main():
    sdk = PumpDotFunSDK(endpoint)
    result = await sdk.buy(...)
    await sdk.close()  # Clean up resources

# Better: Use multiple concurrent operations
async def batch_operations():
    tasks = [
        sdk.buy(buyer1, mint, 1.0),
        sdk.buy(buyer2, mint, 2.0),
        sdk.buy(buyer3, mint, 0.5)
    ]
    results = await asyncio.gather(*tasks)
```

### Connection Management

```python
# Reuse SDK instance for multiple operations
sdk = PumpDotFunSDK(endpoint)

try:
    # Perform multiple operations
    result1 = await sdk.buy(...)
    result2 = await sdk.sell(...)
finally:
    # Always clean up
    await sdk.close()
```

## Contributing

We welcome contributions to the PumpDotFun SDK Python! Please follow these guidelines:

### Development Setup

```bash
git clone https://github.com/your-repo/pumpdotfun-sdk-py.git
cd pumpdotfun-sdk-py
pip install -r requirements.txt
pip install -e .
```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add unit tests for new functionality

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

For support, questions, or feature requests:

- Create an issue on GitHub
- Join our Discord community
- Check the documentation wiki

## Acknowledgments

- Original PumpDotFun SDK TypeScript implementation
- Solana Python ecosystem contributors
- PumpFun protocol developers

---

**Disclaimer**: This SDK is for educational and development purposes. Always test thoroughly on devnet before using on mainnet. Trading cryptocurrencies involves risk of loss.

