#!/usr/bin/env python3
"""
Polymarket BTC Up/Down 15m Event Monitor
Main application entry point
"""

import asyncio
import signal
import sys
from datetime import datetime, timezone
from typing import Set

from rich.console import Console
from rich.live import Live

from config import config
from api.gamma_api import GammaAPIClient
from ws.websocket_client import PolymarketWebSocket
from models.market import Market
from models.market_state import MarketState
from models.events import (
    WebSocketEvent,
    BestBidAskEvent,
    LastTradePriceEvent,
    OrderBookEvent,
)
from analytics.alerts import AlertManager
from utils.time_utils import generate_current_and_next_slugs, get_current_interval_info
from utils.formatting import (
    create_market_table,
    print_startup_banner,
    console,
)
from utils.logger import setup_logger, logger
from web.server import WebServer


# Initialize logger
setup_logger(config.log_level)


class BTCMonitor:
    """Main BTC Market Monitor application"""

    def __init__(self):
        self.ws_client = PolymarketWebSocket(
            url=config.ws_url,
            ping_interval=config.ping_interval,
            reconnect_base_delay=config.reconnect_base_delay,
            max_reconnect_delay=config.max_reconnect_delay,
        )
        self.alert_manager = AlertManager(
            price_swing_threshold=config.price_swing_threshold,
            price_swing_window=config.price_swing_window,
            volume_spike_multiplier=config.volume_spike_multiplier,
            market_closing_alert=config.market_closing_alert,
        )

        # Market state tracking: asset_id -> MarketState
        self.market_states: dict[str, MarketState] = {}

        # Market metadata: market_id -> Market
        self.markets: dict[str, Market] = {}

        # Current and next market references for rolling
        self.current_market: Market | None = None
        self.next_market: Market | None = None

        # Web server for dashboard
        self.web_server = WebServer(
            host=config.web_host,
            port=config.web_port,
            get_state=self.get_web_state,
        )

        self.running = False

    async def discover_markets(self) -> tuple[Market | None, Market | None]:
        """
        Fetch current and next BTC markets.

        Returns:
            Tuple of (current_market, next_market)
        """
        slugs = generate_current_and_next_slugs(config.base_slug)

        async with GammaAPIClient(config.gamma_api_base) as api:
            # Try to fetch by slug
            logger.info(f"Fetching market: {slugs['current']}")
            current_market = await api.get_market_by_slug(slugs["current"])

            logger.info(f"Fetching market: {slugs['next']}")
            next_market = await api.get_market_by_slug(slugs["next"])

            # Fallback: search for any BTC 15m markets
            if not current_market and not next_market:
                logger.warning("Slug-based lookup failed, searching for BTC markets...")
                btc_markets = await api.find_btc_15m_markets()

                if btc_markets:
                    current_market = btc_markets[0]
                    if len(btc_markets) > 1:
                        next_market = btc_markets[1]

            return current_market, next_market

    def setup_market_states(self, current_market: Market | None, next_market: Market | None):
        """
        Create MarketState objects for each market outcome.

        Args:
            current_market: Current interval market
            next_market: Next interval market
        """
        # Store market references for rolling
        self.current_market = current_market
        self.next_market = next_market

        for market, is_current in [(current_market, True), (next_market, False)]:
            if not market:
                continue

            self.markets[market.id] = market

            # Create states for UP and DOWN outcomes
            up_token = market.get_up_token_id()
            down_token = market.get_down_token_id()

            if up_token:
                self.market_states[up_token] = MarketState(
                    market=market,
                    outcome="UP",
                    is_current=is_current,
                )
                # Set initial price if available
                up_price = market.get_up_price()
                if up_price is not None:
                    self.market_states[up_token].update_price(up_price)

            if down_token:
                self.market_states[down_token] = MarketState(
                    market=market,
                    outcome="DOWN",
                    is_current=is_current,
                )
                # Set initial price if available
                down_price = market.get_down_price()
                if down_price is not None:
                    self.market_states[down_token].update_price(down_price)

            # Alert for new market
            self.alert_manager.create_new_market_alert(
                market.slug, market.question
            )

    def get_market_asset_ids(self, market: Market) -> list[str]:
        """Get asset IDs for a market."""
        ids = []
        up_token = market.get_up_token_id()
        down_token = market.get_down_token_id()
        if up_token:
            ids.append(up_token)
        if down_token:
            ids.append(down_token)
        return ids

    async def check_and_roll_markets(self) -> bool:
        """
        Check if current market has ended and roll to next.

        Returns:
            True if markets were rolled
        """
        if not self.current_market or not self.current_market.close_date:
            return False

        now = datetime.now(timezone.utc)
        close_date = self.current_market.close_date

        # Ensure timezone-aware
        if close_date.tzinfo is None:
            close_date = close_date.replace(tzinfo=timezone.utc)

        # Check if current market has ended
        if now < close_date:
            return False

        logger.info(f"Market {self.current_market.slug} has ended, rolling to next...")

        # Get old asset IDs to unsubscribe
        old_asset_ids = self.get_market_asset_ids(self.current_market)

        # Remove old market states
        for asset_id in old_asset_ids:
            if asset_id in self.market_states:
                del self.market_states[asset_id]
        if self.current_market.id in self.markets:
            del self.markets[self.current_market.id]

        # Unsubscribe from old assets
        if old_asset_ids:
            await self.ws_client.unsubscribe(old_asset_ids)

        # Roll: next becomes current
        self.current_market = self.next_market

        # Update is_current flag for the rolled market
        if self.current_market:
            for asset_id in self.get_market_asset_ids(self.current_market):
                if asset_id in self.market_states:
                    self.market_states[asset_id].is_current = True

        # Fetch new next market
        async with GammaAPIClient(config.gamma_api_base) as api:
            slugs = generate_current_and_next_slugs(config.base_slug)
            logger.info(f"Fetching new next market: {slugs['next']}")
            self.next_market = await api.get_market_by_slug(slugs["next"])

        # Add new next market if found
        if self.next_market:
            self.markets[self.next_market.id] = self.next_market
            new_asset_ids = []

            up_token = self.next_market.get_up_token_id()
            down_token = self.next_market.get_down_token_id()

            if up_token:
                self.market_states[up_token] = MarketState(
                    market=self.next_market,
                    outcome="UP",
                    is_current=False,
                )
                up_price = self.next_market.get_up_price()
                if up_price is not None:
                    self.market_states[up_token].update_price(up_price)
                new_asset_ids.append(up_token)

            if down_token:
                self.market_states[down_token] = MarketState(
                    market=self.next_market,
                    outcome="DOWN",
                    is_current=False,
                )
                down_price = self.next_market.get_down_price()
                if down_price is not None:
                    self.market_states[down_token].update_price(down_price)
                new_asset_ids.append(down_token)

            # Subscribe to new assets
            if new_asset_ids:
                await self.ws_client.subscribe(new_asset_ids)

            # Alert for new market
            self.alert_manager.create_new_market_alert(
                self.next_market.slug, self.next_market.question
            )

            logger.info(f"Rolled to new markets - current: {self.current_market.slug if self.current_market else 'None'}, next: {self.next_market.slug}")
        else:
            logger.warning("No next market available yet")

        return True

    def get_asset_ids(self) -> Set[str]:
        """Get all asset IDs to subscribe to."""
        return set(self.market_states.keys())

    def get_web_state(self) -> dict:
        """Get current state for web dashboard."""
        states = {}
        for asset_id, state in self.market_states.items():
            market = state.market
            states[asset_id] = {
                "asset_id": asset_id,
                "outcome": state.outcome,
                "is_current": state.is_current,
                "current_price": state.current_price,
                "first_price": state.first_price,
                "best_bid": state.best_bid,
                "best_ask": state.best_ask,
                "trade_count": state.trade_count,
                "total_volume": state.total_volume,
                "price_change_pct": state.get_price_change_pct(),
                "market_slug": market.slug if market else None,
                "question": market.question if market else None,
                "close_date": market.close_date.isoformat() if market and market.close_date else None,
            }

        markets = {}
        for market_id, market in self.markets.items():
            markets[market_id] = {
                "id": market_id,
                "slug": market.slug,
                "question": market.question,
                "close_date": market.close_date.isoformat() if market.close_date else None,
            }

        return {
            "states": states,
            "markets": markets,
            "connected": self.ws_client.is_connected(),
        }

    async def handle_market_event(self, event: WebSocketEvent):
        """
        Process WebSocket events and update market states.

        Args:
            event: Parsed WebSocket event
        """
        asset_id = event.asset_id
        if not asset_id or asset_id not in self.market_states:
            return

        state = self.market_states[asset_id]

        if isinstance(event, BestBidAskEvent):
            # Update bid/ask prices
            mid_price = event.get_mid_price()
            if mid_price is not None:
                state.update_price(mid_price)

                try:
                    bid = float(event.best_bid) if event.best_bid else None
                    ask = float(event.best_ask) if event.best_ask else None
                    state.update_bid_ask(bid, ask)
                except (ValueError, TypeError):
                    pass

        elif isinstance(event, LastTradePriceEvent):
            # Record trade
            price = event.get_price_float()
            size = event.get_size_float()
            if price is not None and size is not None:
                state.add_trade(size, price)

        elif isinstance(event, OrderBookEvent):
            # Update from order book
            mid_price = event.get_mid_price()
            if mid_price is not None:
                state.update_price(mid_price)

            state.update_bid_ask(event.get_best_bid(), event.get_best_ask())

        # Check for alerts
        self.alert_manager.check_alerts(state)

    async def run_live_dashboard(self):
        """Run a live-updating terminal dashboard."""
        roll_check_interval = 5  # Check every 5 seconds
        last_roll_check = 0

        try:
            with Live(
                create_market_table(self.market_states),
                console=console,
                refresh_per_second=config.refresh_rate,
            ) as live:
                while self.running:
                    live.update(create_market_table(self.market_states))

                    # Periodically check if we need to roll to next market
                    now = asyncio.get_event_loop().time()
                    if now - last_roll_check >= roll_check_interval:
                        last_roll_check = now
                        try:
                            await self.check_and_roll_markets()
                        except Exception as e:
                            logger.error(f"Error checking market roll: {e}")

                    await asyncio.sleep(1 / config.refresh_rate)
        except asyncio.CancelledError:
            pass

    async def initialize(self) -> bool:
        """
        Initialize the monitor.

        Returns:
            True if initialization successful
        """
        logger.info("Initializing Polymarket BTC Monitor...")

        # Discover markets
        logger.info("Discovering BTC 15-minute markets...")
        current_market, next_market = await self.discover_markets()

        if not current_market and not next_market:
            logger.error("No BTC markets found!")
            return False

        # Setup market states
        self.setup_market_states(current_market, next_market)

        logger.info(f"Monitoring {len(self.market_states)} outcomes")
        return True

    async def start(self):
        """Start the monitoring process."""
        self.running = True

        # Get asset IDs to subscribe
        asset_ids = self.get_asset_ids()
        if not asset_ids:
            logger.error("No assets to subscribe to")
            return

        logger.info(f"Subscribing to {len(asset_ids)} assets")

        # Start web server
        await self.web_server.start()

        # Start dashboard in background
        dashboard_task = asyncio.create_task(self.run_live_dashboard())

        try:
            # Connect to WebSocket (this runs until disconnected)
            await self.ws_client.connect(asset_ids, self.handle_market_event)
        except asyncio.CancelledError:
            pass
        finally:
            dashboard_task.cancel()
            try:
                await dashboard_task
            except asyncio.CancelledError:
                pass

    async def shutdown(self):
        """Gracefully shutdown the monitor."""
        logger.info("Shutting down...")
        self.running = False
        await self.web_server.stop()
        await self.ws_client.disconnect()
        logger.info("Shutdown complete")


async def main():
    """Main entry point."""
    print_startup_banner()

    # Display interval info
    interval_info = get_current_interval_info()
    logger.info(f"Current interval: {interval_info['current_timestamp']}")
    logger.info(f"Progress: {interval_info['progress_percent']}%")
    logger.info(f"Remaining: {interval_info['remaining_seconds']}s")
    logger.info(f"Web dashboard: http://localhost:{config.web_port}")

    # Create monitor
    monitor = BTCMonitor()

    # Setup signal handlers (Unix only - Windows uses KeyboardInterrupt)
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(monitor.shutdown())

    try:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    except NotImplementedError:
        # Signal handlers not supported on Windows
        pass

    try:
        # Initialize
        initialized = await monitor.initialize()
        if not initialized:
            logger.error("Failed to initialize monitor")
            return 1

        # Start monitoring
        await monitor.start()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        await monitor.shutdown()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(0)
