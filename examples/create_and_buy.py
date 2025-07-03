"""
Example: Create and Buy Token

This example demonstrates how to create a new token on PumpFun
and immediately purchase some tokens.
"""

import asyncio
import os
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# Load environment variables
load_dotenv()

# Import the SDK
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import CreateTokenMetadata, PriorityFee


async def create_and_buy_example():
    """
    Example function demonstrating token creation and purchase.
    """
    
    # Configuration
    RPC_ENDPOINT = os.getenv('RPC_ENDPOINT', 'https://api.devnet.solana.com')
    WEBSOCKET_ENDPOINT = os.getenv('WEBSOCKET_ENDPOINT', 'wss://api.devnet.solana.com')
    
    print("🚀 PumpDotFun SDK - Create and Buy Example")
    print("=" * 50)
    
    # Initialize the SDK
    print("📡 Initializing SDK...")
    sdk = PumpDotFunSDK(
        rpc_endpoint=RPC_ENDPOINT,
        websocket_endpoint=WEBSOCKET_ENDPOINT,
        commitment="confirmed"
    )
    
    # Create keypairs for creator and mint
    print("🔑 Generating keypairs...")
    creator = Keypair()
    mint = Keypair()
    
    print(f"Creator public key: {creator.pubkey()}")
    print(f"Mint public key: {mint.pubkey()}")
    
    # Define token metadata
    print("📝 Setting up token metadata...")
    metadata = CreateTokenMetadata(
        name="Example Meme Token",
        symbol="EMT",
        description="An example meme token created with PumpDotFun SDK Python. This token demonstrates the full functionality of the SDK including creation, trading, and event monitoring.",
        image="https://example.com/token-image.png",
        show_name=True,
        website="https://example-meme-token.com",
        twitter="@ExampleMemeToken",
        telegram="https://t.me/ExampleMemeToken"
    )
    
    print(f"Token Name: {metadata.name}")
    print(f"Token Symbol: {metadata.symbol}")
    print(f"Description: {metadata.description}")
    
    # Set up priority fees (optional)
    priority_fees = PriorityFee(
        unit_limit=200000,
        unit_price=1000
    )
    
    # Configuration for the purchase
    buy_amount_sol = 0.1  # Buy 0.1 SOL worth of tokens
    slippage_basis_points = 500  # 5% slippage tolerance
    
    print(f"💰 Purchase amount: {buy_amount_sol} SOL")
    print(f"📊 Slippage tolerance: {slippage_basis_points / 100}%")
    
    try:
        print("\n🔄 Creating token and making initial purchase...")
        print("This may take a few moments...")
        
        # Create and buy the token
        result = await sdk.create_and_buy(
            creator=creator,
            mint=mint,
            token_metadata=metadata,
            buy_amount_sol=buy_amount_sol,
            slippage_basis_points=slippage_basis_points,
            priority_fees=priority_fees,
            commitment="confirmed"
        )
        
        # Check the result
        if result.success:
            print("\n✅ SUCCESS!")
            print("=" * 30)
            print(f"🎉 Token created and purchased successfully!")
            print(f"📄 Create transaction signature: {result.results.get('create_signature', 'N/A')}")
            print(f"🛒 Buy transaction signature: {result.results.get('buy_signature', 'N/A')}")
            print(f"🏷️  Mint address: {result.results.get('mint', 'N/A')}")
            
            # Display token information
            token_info = result.results.get('token_metadata', {})
            print(f"\n📊 Token Information:")
            print(f"   Name: {token_info.get('name', 'N/A')}")
            print(f"   Symbol: {token_info.get('symbol', 'N/A')}")
            print(f"   Description: {token_info.get('description', 'N/A')}")
            
            print(f"\n💡 You can now:")
            print(f"   - Trade this token using the buy() and sell() methods")
            print(f"   - Monitor events for this token")
            print(f"   - Check the bonding curve status")
            
        else:
            print("\n❌ FAILED!")
            print("=" * 20)
            print(f"Error: {result.error}")
            print("\n🔍 Troubleshooting tips:")
            print("   - Check your RPC endpoint is working")
            print("   - Ensure you have sufficient SOL for the transaction")
            print("   - Verify your network connection")
            print("   - Try reducing the buy amount or increasing slippage tolerance")
            
    except Exception as e:
        print(f"\n💥 Exception occurred: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        
        # Provide specific error handling
        if "insufficient funds" in str(e).lower():
            print("\n💸 Insufficient funds error:")
            print("   - Make sure your creator account has enough SOL")
            print("   - Consider using devnet for testing")
            
        elif "slippage" in str(e).lower():
            print("\n📈 Slippage error:")
            print("   - Try increasing slippage tolerance")
            print("   - Market conditions may be volatile")
            
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            print("\n🌐 Network error:")
            print("   - Check your internet connection")
            print("   - Try a different RPC endpoint")
            print("   - Verify the endpoint is accessible")
            
    finally:
        # Clean up resources
        print("\n🧹 Cleaning up...")
        await sdk.close()
        print("✨ Done!")


async def demonstrate_error_handling():
    """
    Demonstrate various error handling scenarios.
    """
    print("\n🛡️  Error Handling Demonstration")
    print("=" * 40)
    
    sdk = PumpDotFunSDK("https://api.devnet.solana.com")
    
    creator = Keypair()
    mint = Keypair()
    
    metadata = CreateTokenMetadata(
        name="Error Demo Token",
        symbol="ERR",
        description="Token for error demonstration",
        image="https://example.com/error.png"
    )
    
    # Test 1: Invalid slippage
    print("🧪 Test 1: Invalid slippage tolerance")
    try:
        result = await sdk.create_and_buy(
            creator=creator,
            mint=mint,
            token_metadata=metadata,
            buy_amount_sol=0.1,
            slippage_basis_points=15000  # Invalid: > 100%
        )
    except Exception as e:
        print(f"   ✅ Caught expected error: {e}")
    
    # Test 2: Negative buy amount
    print("\n🧪 Test 2: Negative buy amount")
    try:
        result = await sdk.create_and_buy(
            creator=creator,
            mint=mint,
            token_metadata=metadata,
            buy_amount_sol=-1.0  # Invalid: negative
        )
    except Exception as e:
        print(f"   ✅ Caught expected error: {e}")
    
    # Test 3: Empty token name
    print("\n🧪 Test 3: Invalid metadata")
    try:
        invalid_metadata = CreateTokenMetadata(
            name="",  # Invalid: empty name
            symbol="",
            description="",
            image=""
        )
        result = await sdk.create_and_buy(
            creator=creator,
            mint=mint,
            token_metadata=invalid_metadata,
            buy_amount_sol=0.1
        )
    except Exception as e:
        print(f"   ✅ Caught expected error: {e}")
    
    await sdk.close()
    print("\n✅ Error handling demonstration complete")


def print_usage_tips():
    """
    Print usage tips and best practices.
    """
    print("\n💡 Usage Tips and Best Practices")
    print("=" * 40)
    
    tips = [
        "Always test on devnet before using mainnet",
        "Keep your private keys secure and never commit them to version control",
        "Use appropriate slippage tolerance based on market conditions",
        "Monitor gas fees and adjust priority fees accordingly",
        "Implement proper error handling in production applications",
        "Use event listeners to monitor token activity in real-time",
        "Consider batching operations for better efficiency",
        "Always clean up SDK resources when done"
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"   {i}. {tip}")
    
    print("\n📚 Additional Resources:")
    print("   - Check the README.md for comprehensive documentation")
    print("   - Explore other examples in the examples/ directory")
    print("   - Run tests to understand SDK behavior")
    print("   - Join the community for support and updates")


if __name__ == "__main__":
    print("🎯 Starting PumpDotFun SDK Example")
    
    # Run the main example
    asyncio.run(create_and_buy_example())
    
    # Demonstrate error handling
    asyncio.run(demonstrate_error_handling())
    
    # Print usage tips
    print_usage_tips()
    
    print("\n🏁 Example completed successfully!")
    print("Thank you for using PumpDotFun SDK Python! 🐍")

