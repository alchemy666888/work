#!/usr/bin/env python3
"""
Polymarket BTC Up/Down 15m Event Monitor
Main application entry point
"""

import asyncio
import sys
from datetime import datetime
from src.core.market_discovery import MarketDiscovery
from src.core.websocket_client import PolymarketWebSocketClient, MarketDataProcessor
from src.alerts.alert_system import AlertSystem
from src.ui.terminal_dashboard import TerminalDashboard, SimpleTerminalDisplay
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BTCMonitor:
    """Main BTC Market Monitor application"""

    def __init__(self, use_rich_ui: bool = True):
        self.logger = setup_logger(__name__)
        self.market_discovery = MarketDiscovery()
        self.ws_client = PolymarketWebSocketClient()
        self.data_processor = MarketDataProcessor()
        self.alert_system = AlertSystem()

        # UI setup
        self.use_rich_ui = use_rich_ui and config.monitoring.enable_terminal_ui
        if self.use_rich_ui:
            self.dashboard = TerminalDashboard()
        else:
            self.simple_display = SimpleTerminalDisplay()

        self.monitored_markets = {}
        self.running = False

    async def initialize(self):
        """Initialize the monitor"""
        self.logger.info("🚀 Initializing Polymarket BTC Monitor...")

        # Discover BTC markets
        self.logger.info("🔍 Discovering BTC 15-minute markets...")
        try:
            markets = await self.market_discovery.find_btc_15m_markets()

            if not markets:
                self.logger.warning("⚠️  No BTC 15-minute markets found!")
                self.logger.info("📋 Searching for any BTC markets...")

                # Fallback: search for any BTC markets
                all_btc_markets = await self.market_discovery.search_btc_markets()
                active_markets = self.market_discovery.filter_active_markets(all_btc_markets)

                if active_markets:
                    self.logger.info(f"Found {len(active_markets)} active BTC markets")
                    self.market_discovery.display_market_summary(active_markets[:5])

                    # Use the first few markets for demonstration
                    markets = active_markets[:3]
                else:
                    self.logger.error("❌ No BTC markets found at all!")
                    return False

            self.logger.info(f"✅ Found {len(markets)} markets to monitor")

            # Store market info
            for market in markets:
                market_id = market.get('id')
                self.monitored_markets[market_id] = market

                # Create alert for new market
                await self.alert_system.check_new_market(market)

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to discover markets: {e}")
            return False

    async def start_monitoring(self):
        """Start the monitoring process"""
        self.logger.info("📡 Starting WebSocket monitoring...")

        # Connect to WebSocket
        connected = await self.ws_client.connect()
        if not connected:
            self.logger.error("❌ Failed to connect to WebSocket")
            return

        # Register message handler
        self.ws_client.add_message_handler(self.handle_market_update)

        # Subscribe to markets
        for market_id in self.monitored_markets.keys():
            # Note: In practice, you'd subscribe using token IDs not market IDs
            # This is a simplified example
            self.logger.info(f"📊 Subscribing to market: {market_id}")
            # await self.ws_client.subscribe_to_market(market_id)

        self.running = True
        self.logger.info("✅ Monitoring started!")

        # Start heartbeat
        asyncio.create_task(self.ws_client.send_heartbeat())

        # Start update loop
        if self.use_rich_ui:
            await self.run_dashboard()
        else:
            await self.run_simple_display()

    async def handle_market_update(self, message: dict):
        """Handle incoming market updates from WebSocket"""
        try:
            # Process the message
            await self.data_processor.process_message(message)

            # Get market data
            asset_id = message.get('asset_id')
            if asset_id:
                # Check for price changes
                odds = self.data_processor.get_current_odds(asset_id)
                if odds is not None:
                    market_question = self.monitored_markets.get(asset_id, {}).get('question', 'Unknown')
                    await self.alert_system.check_price_change(asset_id, market_question, odds)

        except Exception as e:
            self.logger.error(f"Error handling market update: {e}")

    async def update_dashboard_data(self):
        """Update data for dashboard display"""
        for market_id, market in self.monitored_markets.items():
            # Get latest data from processor
            summary = self.data_processor.get_market_summary(market_id)

            # Calculate up/down odds (simplified)
            up_odds = summary.get('odds_percentage', 50)
            down_odds = 100 - up_odds

            # Update dashboard data
            dashboard_data = {
                'question': market.get('question', 'Unknown'),
                'up_odds': up_odds,
                'down_odds': down_odds,
                'volume': market.get('volume', 0),
                'liquidity': market.get('liquidity', 0),
                'end_time': self.format_time_remaining(market.get('endDate', ''))
            }

            if self.use_rich_ui:
                self.dashboard.update_market_data(market_id, dashboard_data)
            else:
                # For simple display, just store
                pass

        # Update alerts
        recent_alerts = self.alert_system.get_recent_alerts(limit=10)
        for alert in recent_alerts:
            alert_dict = {
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp
            }
            if self.use_rich_ui:
                self.dashboard.add_alert(alert_dict)

    async def run_dashboard(self):
        """Run the rich terminal dashboard"""
        await self.dashboard.run(update_callback=self.update_dashboard_data)

    async def run_simple_display(self):
        """Run simple terminal display"""
        try:
            while self.running:
                # Update data
                await self.update_dashboard_data()

                # Display
                markets_data = []
                for market_id, market in self.monitored_markets.items():
                    summary = self.data_processor.get_market_summary(market_id)
                    up_odds = summary.get('odds_percentage', 50)

                    markets_data.append({
                        'question': market.get('question'),
                        'up_odds': up_odds,
                        'down_odds': 100 - up_odds,
                        'volume': market.get('volume', 0),
                        'liquidity': market.get('liquidity', 0),
                        'end_time': self.format_time_remaining(market.get('endDate', ''))
                    })

                alerts = self.alert_system.get_recent_alerts(limit=5)
                alert_dicts = [
                    {
                        'severity': a.severity,
                        'message': a.message,
                        'timestamp': a.timestamp
                    }
                    for a in alerts
                ]

                self.simple_display.display_summary(markets_data, alert_dicts)

                # Wait before next update
                await asyncio.sleep(config.monitoring.update_interval)

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")

    def format_time_remaining(self, end_date_str: str) -> str:
        """Format time remaining until market ends"""
        try:
            if not end_date_str:
                return "Unknown"

            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            now = datetime.now(end_date.tzinfo)
            remaining = end_date - now

            if remaining.total_seconds() < 0:
                return "Ended"

            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)

            if hours > 24:
                days = hours // 24
                return f"{days}d {hours % 24}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"

        except Exception:
            return "Unknown"

    async def shutdown(self):
        """Gracefully shutdown the monitor"""
        self.logger.info("🛑 Shutting down...")
        self.running = False
        await self.ws_client.disconnect()
        self.logger.info("✅ Shutdown complete")


async def main():
    """Main entry point"""
    logger.info("="*80)
    logger.info("  Polymarket BTC Up/Down 15m Event Monitor")
    logger.info("="*80)

    # Check if rich UI should be used
    use_rich = config.monitoring.enable_terminal_ui

    # Create and run monitor
    monitor = BTCMonitor(use_rich_ui=use_rich)

    try:
        # Initialize
        initialized = await monitor.initialize()
        if not initialized:
            logger.error("Failed to initialize monitor")
            return 1

        # Start monitoring
        await monitor.start_monitoring()

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    finally:
        await monitor.shutdown()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
