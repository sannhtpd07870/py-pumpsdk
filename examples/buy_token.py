"""
Example: Buy Token

This example demonstrates how to buy tokens from an existing
PumpFun token using the bonding curve mechanism.
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
from pumpdotfun_sdk.types import PriorityFee
from pumpdotfun_sdk.utils import format_sol_amount, sol_to_lamports


async def buy_token_example():
    """
    Example function demonstrating token purchase.
    """
    
    # Configuration
    RPC_ENDPOINT = os.getenv('RPC_ENDPOINT', 'https://api.devnet.solana.com')
    WEBSOCKET_ENDPOINT = os.getenv('WEBSOCKET_ENDPOINT', 'wss://api.devnet.solana.com')
    
    print("💰 PumpDotFun SDK - Buy Token Example")
    print("=" * 45)
    
    # Initialize the SDK
    print("📡 Initializing SDK...")
    sdk = PumpDotFunSDK(
        rpc_endpoint=RPC_ENDPOINT,
        websocket_endpoint=WEBSOCKET_ENDPOINT,
        commitment="confirmed"
    )
    
    # Create buyer keypair
    print("🔑 Generating buyer keypair...")
    buyer = Keypair()
    print(f"Buyer public key: {buyer.pubkey()}")
    
    # Token mint address (replace with actual token mint)
    # For this example, we'll use a placeholder address
    # In practice, you would get this from a token creation or discovery
    mint_address = "11111111111111111111111111111112"  # Placeholder
    mint = Pubkey.from_string(mint_address)
    
    print(f"🏷️  Target token mint: {mint}")
    
    # Purchase configuration
    buy_amounts = [0.01, 0.05, 0.1, 0.5]  # Different purchase amounts in SOL
    slippage_tolerances = [500, 1000, 1500]  # Different slippage tolerances (5%, 10%, 15%)
    
    print("\n📊 Purchase Configuration Options:")
    print("Buy amounts (SOL):", buy_amounts)
    print("Slippage tolerances (%):", [s/100 for s in slippage_tolerances])
    
    # Set up priority fees
    priority_fees = PriorityFee(
        unit_limit=200000,
        unit_price=1500  # Higher priority for faster execution
    )
    
    # Example 1: Simple buy
    await simple_buy_example(sdk, buyer, mint, priority_fees)
    
    # Example 2: Buy with different slippage tolerances
    await slippage_comparison_example(sdk, buyer, mint, priority_fees)
    
    # Example 3: Batch buying simulation
    await batch_buy_simulation(sdk, buyer, mint, priority_fees)
    
    # Example 4: Price impact analysis
    await price_impact_analysis(sdk, buyer, mint)
    
    # Clean up
    await sdk.close()
    print("\n✨ Buy token examples completed!")


async def simple_buy_example(sdk, buyer, mint, priority_fees):
    """
    Simple token purchase example.
    """
    print("\n🎯 Example 1: Simple Token Purchase")
    print("-" * 35)
    
    buy_amount_sol = 0.1
    slippage_basis_points = 500  # 5%
    
    print(f"💵 Buying {buy_amount_sol} SOL worth of tokens")
    print(f"📈 Slippage tolerance: {slippage_basis_points / 100}%")
    
    try:
        result = await sdk.buy(
            buyer=buyer,
            mint=mint,
            buy_amount_sol=buy_amount_sol,
            slippage_basis_points=slippage_basis_points,
            priority_fees=priority_fees,
            commitment="confirmed"
        )
        
        if result.success:
            print("✅ Purchase successful!")
            print(f"📄 Transaction signature: {result.signature}")
            
            # Display purchase details
            if result.results:
                expected_tokens = result.results.get('expected_tokens', 0)
                min_tokens_out = result.results.get('min_tokens_out', 0)
                
                print(f"🎯 Expected tokens: {expected_tokens:,}")
                print(f"🛡️  Minimum tokens (with slippage): {min_tokens_out:,}")
                print(f"📊 Slippage protection: {((expected_tokens - min_tokens_out) / expected_tokens * 100):.2f}%")
        else:
            print(f"❌ Purchase failed: {result.error}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")


async def slippage_comparison_example(sdk, buyer, mint, priority_fees):
    """
    Compare different slippage tolerances.
    """
    print("\n📊 Example 2: Slippage Tolerance Comparison")
    print("-" * 45)
    
    buy_amount_sol = 0.05
    slippage_options = [250, 500, 1000, 2000]  # 2.5%, 5%, 10%, 20%
    
    print(f"💵 Purchase amount: {buy_amount_sol} SOL")
    print("🔍 Testing different slippage tolerances...")
    
    for slippage_bp in slippage_options:
        slippage_pct = slippage_bp / 100
        print(f"\n   📈 Testing {slippage_pct}% slippage tolerance...")
        
        try:
            # Simulate the purchase (in practice, you wouldn't want to make multiple actual purchases)
            # This is just for demonstration of the API
            print(f"   🔄 Simulating buy with {slippage_pct}% slippage...")
            
            # In a real scenario, you might want to:
            # 1. Get current bonding curve state
            # 2. Calculate expected output
            # 3. Apply slippage tolerance
            # 4. Show the user what they would get
            
            lamports = sol_to_lamports(buy_amount_sol)
            min_tokens_with_slippage = int(lamports * (1 - slippage_bp / 10000))
            
            print(f"   ✅ Minimum tokens with {slippage_pct}% slippage: {min_tokens_with_slippage:,}")
            
        except Exception as e:
            print(f"   ❌ Error with {slippage_pct}% slippage: {e}")
    
    print("\n💡 Slippage Tips:")
    print("   - Lower slippage = more protection but higher chance of failure")
    print("   - Higher slippage = more likely to succeed but less favorable price")
    print("   - Consider market volatility when setting slippage")


async def batch_buy_simulation(sdk, buyer, mint, priority_fees):
    """
    Simulate batch buying with different amounts.
    """
    print("\n🔄 Example 3: Batch Purchase Simulation")
    print("-" * 40)
    
    purchase_amounts = [0.01, 0.02, 0.05, 0.1]
    slippage_bp = 750  # 7.5%
    
    print(f"📦 Simulating batch purchases: {purchase_amounts} SOL")
    print(f"📊 Using {slippage_bp / 100}% slippage for all purchases")
    
    total_sol_spent = 0
    total_tokens_expected = 0
    
    for i, amount in enumerate(purchase_amounts, 1):
        print(f"\n   🛒 Purchase {i}: {amount} SOL")
        
        try:
            # In practice, you might want to batch these transactions
            # or execute them with proper timing
            
            # Simulate calculation
            lamports = sol_to_lamports(amount)
            estimated_tokens = lamports * 1000  # Simplified estimation
            min_tokens = int(estimated_tokens * (1 - slippage_bp / 10000))
            
            print(f"   📈 Estimated tokens: {estimated_tokens:,}")
            print(f"   🛡️  Minimum tokens: {min_tokens:,}")
            
            total_sol_spent += amount
            total_tokens_expected += estimated_tokens
            
        except Exception as e:
            print(f"   ❌ Error in purchase {i}: {e}")
    
    print(f"\n📊 Batch Summary:")
    print(f"   💰 Total SOL to spend: {total_sol_spent} SOL")
    print(f"   🎯 Total tokens expected: {total_tokens_expected:,}")
    print(f"   📈 Average price per token: {total_sol_spent / total_tokens_expected:.8f} SOL")


async def price_impact_analysis(sdk, buyer, mint):
    """
    Analyze price impact of different purchase sizes.
    """
    print("\n📈 Example 4: Price Impact Analysis")
    print("-" * 35)
    
    purchase_sizes = [0.01, 0.1, 0.5, 1.0, 5.0]  # SOL amounts
    
    print("🔍 Analyzing price impact for different purchase sizes...")
    print("(This is a simulation - actual impact depends on bonding curve state)")
    
    print(f"\n{'Purchase (SOL)':<15} {'Est. Tokens':<15} {'Price Impact':<15} {'Effective Price':<15}")
    print("-" * 65)
    
    for purchase_sol in purchase_sizes:
        try:
            # Simulate price impact calculation
            # In practice, you would:
            # 1. Get current bonding curve reserves
            # 2. Calculate output amount
            # 3. Calculate price before and after
            # 4. Determine price impact
            
            lamports = sol_to_lamports(purchase_sol)
            
            # Simplified simulation (replace with actual bonding curve math)
            base_rate = 1000  # tokens per SOL
            impact_factor = min(purchase_sol * 0.02, 0.5)  # Max 50% impact
            effective_rate = base_rate * (1 - impact_factor)
            estimated_tokens = int(lamports * effective_rate / 1_000_000_000)
            
            price_impact_pct = impact_factor * 100
            effective_price = purchase_sol / estimated_tokens if estimated_tokens > 0 else 0
            
            print(f"{purchase_sol:<15} {estimated_tokens:<15,} {price_impact_pct:<14.2f}% {effective_price:<15.8f}")
            
        except Exception as e:
            print(f"{purchase_sol:<15} Error: {str(e)[:20]}")
    
    print("\n💡 Price Impact Tips:")
    print("   - Larger purchases typically have higher price impact")
    print("   - Consider splitting large purchases across time")
    print("   - Monitor bonding curve liquidity before large trades")
    print("   - Use appropriate slippage tolerance for your purchase size")


async def demonstrate_error_scenarios():
    """
    Demonstrate common error scenarios in token buying.
    """
    print("\n🛡️  Error Scenario Demonstrations")
    print("-" * 35)
    
    sdk = PumpDotFunSDK("https://api.devnet.solana.com")
    buyer = Keypair()
    mint = Pubkey.from_string("11111111111111111111111111111112")
    
    error_scenarios = [
        ("Zero purchase amount", 0.0, 500),
        ("Negative purchase amount", -0.1, 500),
        ("Invalid slippage (too high)", 0.1, 15000),
        ("Invalid slippage (negative)", 0.1, -100),
    ]
    
    for scenario_name, amount, slippage in error_scenarios:
        print(f"\n🧪 Testing: {scenario_name}")
        try:
            result = await sdk.buy(
                buyer=buyer,
                mint=mint,
                buy_amount_sol=amount,
                slippage_basis_points=slippage
            )
            print(f"   ⚠️  Unexpected success: {result.success}")
        except Exception as e:
            print(f"   ✅ Caught expected error: {type(e).__name__}: {e}")
    
    await sdk.close()


def print_buying_best_practices():
    """
    Print best practices for token buying.
    """
    print("\n🎯 Token Buying Best Practices")
    print("=" * 35)
    
    practices = [
        "Research the token and its bonding curve before buying",
        "Start with small amounts to test the process",
        "Use appropriate slippage tolerance (typically 5-10%)",
        "Monitor network congestion and adjust priority fees",
        "Consider price impact for larger purchases",
        "Keep track of your transactions for tax purposes",
        "Never invest more than you can afford to lose",
        "Use devnet for testing before mainnet transactions"
    ]
    
    for i, practice in enumerate(practices, 1):
        print(f"   {i}. {practice}")
    
    print(f"\n🔧 Technical Tips:")
    print(f"   - Use 'confirmed' commitment for balance between speed and security")
    print(f"   - Set reasonable timeout values for transaction confirmation")
    print(f"   - Implement retry logic for failed transactions")
    print(f"   - Monitor your SOL balance to ensure sufficient funds")


if __name__ == "__main__":
    print("🚀 Starting Buy Token Examples")
    
    # Run the main examples
    asyncio.run(buy_token_example())
    
    # Demonstrate error scenarios
    asyncio.run(demonstrate_error_scenarios())
    
    # Print best practices
    print_buying_best_practices()
    
    print("\n🏁 Buy token examples completed!")
    print("Happy trading! 💰")

