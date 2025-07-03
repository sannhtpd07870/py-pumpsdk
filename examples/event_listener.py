"""
Example: Event Listener

This example demonstrates how to listen for real-time events
from the PumpFun protocol, including token creation, trades,
and bonding curve completion events.
"""

import asyncio
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the SDK
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pumpdotfun_sdk import PumpDotFunSDK
from pumpdotfun_sdk.types import PumpFunEventType
from pumpdotfun_sdk.utils import format_sol_amount


class EventTracker:
    """
    Helper class to track and display events.
    """
    
    def __init__(self):
        self.events_received = 0
        self.create_events = 0
        self.trade_events = 0
        self.complete_events = 0
        self.start_time = time.time()
        self.recent_tokens = []
        self.trading_volume = 0
    
    def log_event(self, event_type: str, details: str = ""):
        """Log an event with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event_type}: {details}")
        self.events_received += 1
    
    def get_stats(self):
        """Get current statistics."""
        runtime = time.time() - self.start_time
        return {
            "runtime": runtime,
            "total_events": self.events_received,
            "create_events": self.create_events,
            "trade_events": self.trade_events,
            "complete_events": self.complete_events,
            "events_per_minute": (self.events_received / runtime * 60) if runtime > 0 else 0,
            "trading_volume": self.trading_volume
        }
    
    def print_stats(self):
        """Print current statistics."""
        stats = self.get_stats()
        print(f"\n📊 Event Statistics:")
        print(f"   ⏱️  Runtime: {stats['runtime']:.1f} seconds")
        print(f"   📈 Total events: {stats['total_events']}")
        print(f"   🆕 Create events: {stats['create_events']}")
        print(f"   💱 Trade events: {stats['trade_events']}")
        print(f"   ✅ Complete events: {stats['complete_events']}")
        print(f"   📊 Events/minute: {stats['events_per_minute']:.1f}")
        print(f"   💰 Trading volume: {format_sol_amount(stats['trading_volume'])} SOL")


# Global event tracker
tracker = EventTracker()


def on_create_event(event, slot, signature):
    """
    Handle token creation events.
    """
    tracker.create_events += 1
    tracker.recent_tokens.append({
        'mint': str(event.mint),
        'name': event.name,
        'symbol': event.symbol,
        'timestamp': event.timestamp
    })
    
    # Keep only recent 10 tokens
    if len(tracker.recent_tokens) > 10:
        tracker.recent_tokens.pop(0)
    
    details = f"🆕 NEW TOKEN: {event.name} ({event.symbol}) | Mint: {str(event.mint)[:8]}... | Creator: {str(event.user)[:8]}..."
    tracker.log_event("CREATE", details)
    
    # Display additional info for interesting tokens
    if len(event.name) > 20 or "MEME" in event.name.upper():
        print(f"   🔥 Interesting token detected!")
        print(f"   📝 Description might be worth checking")


def on_trade_event(event, slot, signature):
    """
    Handle trade events.
    """
    tracker.trade_events += 1
    tracker.trading_volume += event.sol_amount
    
    action = "🟢 BUY" if event.is_buy else "🔴 SELL"
    sol_amount = format_sol_amount(event.sol_amount)
    token_amount = f"{event.token_amount:,}"
    
    details = f"{action} | {sol_amount} SOL ↔ {token_amount} tokens | Mint: {str(event.mint)[:8]}... | Trader: {str(event.user)[:8]}..."
    tracker.log_event("TRADE", details)
    
    # Highlight large trades
    if event.sol_amount > 1_000_000_000:  # > 1 SOL
        print(f"   🐋 LARGE TRADE DETECTED! {sol_amount} SOL")
    
    # Track buy/sell ratio
    if hasattr(tracker, 'buy_count'):
        if event.is_buy:
            tracker.buy_count += 1
        else:
            tracker.sell_count += 1
    else:
        tracker.buy_count = 1 if event.is_buy else 0
        tracker.sell_count = 0 if event.is_buy else 1


def on_complete_event(event, slot, signature):
    """
    Handle bonding curve completion events.
    """
    tracker.complete_events += 1
    
    details = f"🎉 CURVE COMPLETED! | Mint: {str(event.mint)[:8]}... | Completer: {str(event.user)[:8]}..."
    tracker.log_event("COMPLETE", details)
    
    print(f"   🚀 Token graduated to full AMM!")
    print(f"   💎 This token has reached maximum bonding curve!")


async def basic_event_listening_example():
    """
    Basic example of listening to all event types.
    """
    print("🎧 Basic Event Listening Example")
    print("=" * 40)
    
    # Configuration
    RPC_ENDPOINT = os.getenv('RPC_ENDPOINT', 'https://api.mainnet-beta.solana.com')
    WEBSOCKET_ENDPOINT = os.getenv('WEBSOCKET_ENDPOINT', 'wss://api.mainnet-beta.solana.com')
    
    # Initialize SDK with WebSocket support
    sdk = PumpDotFunSDK(
        rpc_endpoint=RPC_ENDPOINT,
        websocket_endpoint=WEBSOCKET_ENDPOINT
    )
    
    print(f"📡 Connected to: {RPC_ENDPOINT}")
    print(f"🔌 WebSocket: {WEBSOCKET_ENDPOINT}")
    
    # Add event listeners
    print("\n🎯 Adding event listeners...")
    
    create_listener = sdk.add_event_listener(
        PumpFunEventType.CREATE_EVENT,
        on_create_event
    )
    print(f"✅ Create event listener added (ID: {create_listener})")
    
    trade_listener = sdk.add_event_listener(
        PumpFunEventType.TRADE_EVENT,
        on_trade_event
    )
    print(f"✅ Trade event listener added (ID: {trade_listener})")
    
    complete_listener = sdk.add_event_listener(
        PumpFunEventType.COMPLETE_EVENT,
        on_complete_event
    )
    print(f"✅ Complete event listener added (ID: {complete_listener})")
    
    # Start listening
    print("\n🚀 Starting event monitoring...")
    print("Press Ctrl+C to stop\n")
    
    try:
        await sdk.start_event_listening()
        
        # Monitor for specified duration
        monitoring_duration = 60  # seconds
        print(f"👂 Listening for events for {monitoring_duration} seconds...")
        
        for i in range(monitoring_duration):
            await asyncio.sleep(1)
            
            # Print periodic updates
            if (i + 1) % 10 == 0:
                print(f"\n⏰ {monitoring_duration - i - 1} seconds remaining...")
                tracker.print_stats()
                
                # Show recent tokens
                if tracker.recent_tokens:
                    print(f"\n🆕 Recent tokens:")
                    for token in tracker.recent_tokens[-3:]:
                        print(f"   • {token['name']} ({token['symbol']}) - {token['mint'][:8]}...")
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        sdk.remove_event_listener(create_listener)
        sdk.remove_event_listener(trade_listener)
        sdk.remove_event_listener(complete_listener)
        sdk.stop_event_listening()
        await sdk.close()
        
        # Final statistics
        print("\n📊 Final Statistics:")
        tracker.print_stats()
        
        if hasattr(tracker, 'buy_count') and hasattr(tracker, 'sell_count'):
            total_trades = tracker.buy_count + tracker.sell_count
            if total_trades > 0:
                buy_ratio = tracker.buy_count / total_trades * 100
                print(f"   📈 Buy/Sell ratio: {buy_ratio:.1f}% buys, {100-buy_ratio:.1f}% sells")


async def filtered_event_listening_example():
    """
    Example of listening to specific events with filtering.
    """
    print("\n🔍 Filtered Event Listening Example")
    print("=" * 40)
    
    sdk = PumpDotFunSDK(
        "https://api.mainnet-beta.solana.com",
        "wss://api.mainnet-beta.solana.com"
    )
    
    # Track specific metrics
    large_trades = []
    new_tokens_with_keywords = []
    
    def on_large_trade(event, slot, signature):
        """Filter for large trades only."""
        if event.sol_amount > 5_000_000_000:  # > 5 SOL
            large_trades.append({
                'sol_amount': event.sol_amount,
                'is_buy': event.is_buy,
                'mint': str(event.mint),
                'timestamp': time.time()
            })
            
            action = "BUY" if event.is_buy else "SELL"
            sol_amount = format_sol_amount(event.sol_amount)
            print(f"🐋 WHALE ALERT: {action} {sol_amount} SOL | Mint: {str(event.mint)[:8]}...")
    
    def on_interesting_token(event, slot, signature):
        """Filter for tokens with interesting names."""
        keywords = ['MEME', 'DOGE', 'PEPE', 'MOON', 'ROCKET', 'DIAMOND']
        
        if any(keyword in event.name.upper() for keyword in keywords):
            new_tokens_with_keywords.append({
                'name': event.name,
                'symbol': event.symbol,
                'mint': str(event.mint),
                'timestamp': event.timestamp
            })
            
            print(f"🔥 TRENDING TOKEN: {event.name} ({event.symbol}) | Mint: {str(event.mint)[:8]}...")
    
    # Add filtered listeners
    trade_listener = sdk.add_event_listener(PumpFunEventType.TRADE_EVENT, on_large_trade)
    create_listener = sdk.add_event_listener(PumpFunEventType.CREATE_EVENT, on_interesting_token)
    
    print("🎯 Listening for:")
    print("   🐋 Large trades (> 5 SOL)")
    print("   🔥 Tokens with trending keywords")
    
    try:
        await sdk.start_event_listening()
        await asyncio.sleep(30)  # Listen for 30 seconds
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        sdk.remove_event_listener(trade_listener)
        sdk.remove_event_listener(create_listener)
        sdk.stop_event_listening()
        await sdk.close()
        
        # Report findings
        print(f"\n📊 Filtered Results:")
        print(f"   🐋 Large trades detected: {len(large_trades)}")
        print(f"   🔥 Interesting tokens: {len(new_tokens_with_keywords)}")
        
        if large_trades:
            total_volume = sum(trade['sol_amount'] for trade in large_trades)
            print(f"   💰 Total whale volume: {format_sol_amount(total_volume)} SOL")


async def event_analytics_example():
    """
    Example of collecting and analyzing event data.
    """
    print("\n📈 Event Analytics Example")
    print("=" * 30)
    
    sdk = PumpDotFunSDK(
        "https://api.mainnet-beta.solana.com",
        "wss://api.mainnet-beta.solana.com"
    )
    
    # Analytics data structures
    analytics = {
        'tokens_created': 0,
        'total_volume': 0,
        'unique_traders': set(),
        'hourly_activity': {},
        'token_symbols': {},
        'large_trades': 0
    }
    
    def analyze_create_event(event, slot, signature):
        """Analyze token creation patterns."""
        analytics['tokens_created'] += 1
        
        # Track symbol patterns
        symbol_len = len(event.symbol)
        if symbol_len not in analytics['token_symbols']:
            analytics['token_symbols'][symbol_len] = 0
        analytics['token_symbols'][symbol_len] += 1
        
        # Track hourly activity
        hour = datetime.now().hour
        if hour not in analytics['hourly_activity']:
            analytics['hourly_activity'][hour] = 0
        analytics['hourly_activity'][hour] += 1
    
    def analyze_trade_event(event, slot, signature):
        """Analyze trading patterns."""
        analytics['total_volume'] += event.sol_amount
        analytics['unique_traders'].add(str(event.user))
        
        if event.sol_amount > 1_000_000_000:  # > 1 SOL
            analytics['large_trades'] += 1
    
    # Add analytics listeners
    create_listener = sdk.add_event_listener(PumpFunEventType.CREATE_EVENT, analyze_create_event)
    trade_listener = sdk.add_event_listener(PumpFunEventType.TRADE_EVENT, analyze_trade_event)
    
    print("📊 Collecting analytics data...")
    
    try:
        await sdk.start_event_listening()
        await asyncio.sleep(45)  # Collect data for 45 seconds
        
    finally:
        sdk.remove_event_listener(create_listener)
        sdk.remove_event_listener(trade_listener)
        sdk.stop_event_listening()
        await sdk.close()
        
        # Display analytics
        print(f"\n📈 Analytics Results:")
        print(f"   🆕 Tokens created: {analytics['tokens_created']}")
        print(f"   💰 Total volume: {format_sol_amount(analytics['total_volume'])} SOL")
        print(f"   👥 Unique traders: {len(analytics['unique_traders'])}")
        print(f"   🐋 Large trades: {analytics['large_trades']}")
        
        if analytics['hourly_activity']:
            most_active_hour = max(analytics['hourly_activity'], key=analytics['hourly_activity'].get)
            print(f"   ⏰ Most active hour: {most_active_hour}:00 ({analytics['hourly_activity'][most_active_hour]} events)")
        
        if analytics['token_symbols']:
            common_symbol_length = max(analytics['token_symbols'], key=analytics['token_symbols'].get)
            print(f"   📝 Most common symbol length: {common_symbol_length} characters")


def print_event_monitoring_tips():
    """
    Print tips for effective event monitoring.
    """
    print("\n💡 Event Monitoring Tips")
    print("=" * 25)
    
    tips = [
        "Use mainnet for real data, devnet for testing",
        "Implement proper error handling for WebSocket disconnections",
        "Consider rate limiting when processing high-frequency events",
        "Store important events in a database for historical analysis",
        "Use filters to focus on events relevant to your use case",
        "Monitor WebSocket connection health and implement reconnection logic",
        "Be mindful of memory usage when storing event data",
        "Consider using multiple event listeners for different analysis purposes"
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"   {i}. {tip}")
    
    print(f"\n🔧 Technical Considerations:")
    print(f"   - WebSocket connections can be unstable; implement retry logic")
    print(f"   - Event order is not guaranteed; use timestamps for sequencing")
    print(f"   - Some events might be missed during high network activity")
    print(f"   - Consider using event signatures for deduplication")


async def demonstrate_error_handling():
    """
    Demonstrate error handling in event monitoring.
    """
    print("\n🛡️  Event Monitoring Error Handling")
    print("-" * 35)
    
    # Test with invalid WebSocket endpoint
    print("🧪 Testing invalid WebSocket endpoint...")
    try:
        sdk = PumpDotFunSDK(
            "https://api.mainnet-beta.solana.com",
            "wss://invalid-endpoint.com"
        )
        
        def dummy_callback(event, slot, signature):
            pass
        
        listener_id = sdk.add_event_listener(PumpFunEventType.TRADE_EVENT, dummy_callback)
        await sdk.start_event_listening()
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"   ✅ Caught expected error: {type(e).__name__}: {e}")
    
    finally:
        try:
            sdk.stop_event_listening()
            await sdk.close()
        except:
            pass
    
    print("✅ Error handling demonstration complete")


if __name__ == "__main__":
    print("🎧 Starting Event Listening Examples")
    print("=" * 40)
    
    # Run examples
    try:
        # Basic event listening
        asyncio.run(basic_event_listening_example())
        
        # Filtered event listening
        asyncio.run(filtered_event_listening_example())
        
        # Event analytics
        asyncio.run(event_analytics_example())
        
        # Error handling demonstration
        asyncio.run(demonstrate_error_handling())
        
    except KeyboardInterrupt:
        print("\n⏹️  Examples stopped by user")
    
    # Print tips
    print_event_monitoring_tips()
    
    print("\n🏁 Event listening examples completed!")
    print("Happy monitoring! 👂")

