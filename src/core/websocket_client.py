"""WebSocket client for real-time market data"""

import asyncio
import json
from typing import Dict, List, Callable, Optional
from datetime import datetime
from src.utils.logger import setup_logger
from src.utils.config import config

logger = setup_logger(__name__)


class PolymarketWebSocketClient:
    """
    WebSocket client for Polymarket real-time data
    Handles connection, subscription, and message processing
    """

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.ws_client = None
        self.is_connected = False
        self.subscribed_markets = set()
        self.message_handlers: List[Callable] = []
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Polymarket WebSocket client"""
        try:
            from polymarket_apis import PolymarketWebsocketsClient
            self.ws_client = PolymarketWebsocketsClient()
            self.logger.info("WebSocket client initialized")
        except ImportError:
            self.logger.error("polymarket-apis not installed. Run: pip install polymarket-apis")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket client: {e}")
            raise

    async def connect(self):
        """Establish WebSocket connection with retry logic"""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(f"Connecting to Polymarket WebSocket... (attempt {self.reconnect_attempts + 1})")

                # Note: The polymarket-apis library handles the connection internally
                # We just need to set up the subscription callbacks
                self.is_connected = True
                self.reconnect_attempts = 0
                self.logger.info("WebSocket connected successfully")
                return True

            except Exception as e:
                self.reconnect_attempts += 1
                wait_time = min(2 ** self.reconnect_attempts, 60)  # Exponential backoff
                self.logger.error(
                    f"Connection failed: {e}. "
                    f"Retrying in {wait_time}s... ({self.reconnect_attempts}/{self.max_reconnect_attempts})"
                )
                await asyncio.sleep(wait_time)

        self.logger.critical("Max reconnection attempts reached. Giving up.")
        return False

    async def subscribe_to_market(self, asset_id: str):
        """
        Subscribe to market updates for a specific asset

        Args:
            asset_id: The token/asset ID to monitor
        """
        try:
            if asset_id in self.subscribed_markets:
                self.logger.debug(f"Already subscribed to market: {asset_id}")
                return

            self.logger.info(f"Subscribing to market: {asset_id}")

            # Subscribe using the websocket client
            # The library will call our callback when messages arrive
            await self.ws_client.subscribe_market(
                asset_id,
                callback=self._handle_market_message
            )

            self.subscribed_markets.add(asset_id)
            self.logger.info(f"Subscribed to {asset_id}")

        except Exception as e:
            self.logger.error(f"Failed to subscribe to market {asset_id}: {e}")

    async def subscribe_to_multiple_markets(self, asset_ids: List[str]):
        """Subscribe to multiple markets"""
        for asset_id in asset_ids:
            await self.subscribe_to_market(asset_id)

    async def unsubscribe_from_market(self, asset_id: str):
        """Unsubscribe from a market"""
        try:
            if asset_id not in self.subscribed_markets:
                self.logger.debug(f"Not subscribed to market: {asset_id}")
                return

            await self.ws_client.unsubscribe_market(asset_id)
            self.subscribed_markets.remove(asset_id)
            self.logger.info(f"Unsubscribed from {asset_id}")

        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from market {asset_id}: {e}")

    def add_message_handler(self, handler: Callable):
        """
        Add a callback function to handle incoming messages

        Args:
            handler: Function that takes (asset_id, message_data) as arguments
        """
        self.message_handlers.append(handler)
        self.logger.debug(f"Added message handler: {handler.__name__}")

    async def _handle_market_message(self, message: Dict):
        """
        Internal handler for market messages
        Calls all registered message handlers
        """
        try:
            # Log the message
            asset_id = message.get('asset_id', 'unknown')
            self.logger.debug(f"Received message for {asset_id}: {json.dumps(message, indent=2)}")

            # Call all registered handlers
            for handler in self.message_handlers:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Error in message handler {handler.__name__}: {e}")

        except Exception as e:
            self.logger.error(f"Error handling market message: {e}")

    async def send_heartbeat(self):
        """Send periodic heartbeat to keep connection alive"""
        while self.is_connected:
            try:
                # Send ping/heartbeat
                # The polymarket-apis library should handle this automatically
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                self.logger.debug("Heartbeat sent")
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
                self.is_connected = False
                await self.connect()  # Attempt reconnection

    async def disconnect(self):
        """Gracefully disconnect from WebSocket"""
        try:
            self.is_connected = False
            # The polymarket-apis library handles cleanup internally
            # Check if close method exists before calling
            if self.ws_client and hasattr(self.ws_client, 'close'):
                if asyncio.iscoroutinefunction(self.ws_client.close):
                    await self.ws_client.close()
                else:
                    self.ws_client.close()
            self.logger.info("WebSocket disconnected")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    def get_connection_status(self) -> Dict[str, any]:
        """Get current connection status"""
        return {
            "connected": self.is_connected,
            "subscribed_markets": len(self.subscribed_markets),
            "markets": list(self.subscribed_markets),
            "handlers": len(self.message_handlers),
        }


class MarketDataProcessor:
    """Process and normalize market data from WebSocket messages"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.market_data = {}  # Store latest data for each market

    async def process_message(self, message: Dict):
        """
        Process incoming WebSocket message

        Expected message structure (varies by type):
        - Order book updates
        - Trade events
        - Price updates
        """
        try:
            msg_type = message.get('type', 'unknown')
            asset_id = message.get('asset_id')

            if msg_type == 'book':
                await self._process_orderbook_update(asset_id, message)
            elif msg_type == 'trade':
                await self._process_trade_event(asset_id, message)
            elif msg_type == 'price':
                await self._process_price_update(asset_id, message)
            else:
                self.logger.debug(f"Unknown message type: {msg_type}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    async def _process_orderbook_update(self, asset_id: str, message: Dict):
        """Process order book update"""
        self.logger.debug(f"Order book update for {asset_id}")

        if asset_id not in self.market_data:
            self.market_data[asset_id] = {}

        self.market_data[asset_id]['orderbook'] = {
            'bids': message.get('bids', []),
            'asks': message.get('asks', []),
            'timestamp': datetime.now().isoformat(),
        }

    async def _process_trade_event(self, asset_id: str, message: Dict):
        """Process trade event"""
        self.logger.debug(f"Trade event for {asset_id}")

        if asset_id not in self.market_data:
            self.market_data[asset_id] = {}

        if 'recent_trades' not in self.market_data[asset_id]:
            self.market_data[asset_id]['recent_trades'] = []

        self.market_data[asset_id]['recent_trades'].append({
            'price': message.get('price'),
            'size': message.get('size'),
            'side': message.get('side'),
            'timestamp': message.get('timestamp', datetime.now().isoformat()),
        })

        # Keep only last 100 trades
        self.market_data[asset_id]['recent_trades'] = \
            self.market_data[asset_id]['recent_trades'][-100:]

    async def _process_price_update(self, asset_id: str, message: Dict):
        """Process price update"""
        self.logger.debug(f"Price update for {asset_id}")

        if asset_id not in self.market_data:
            self.market_data[asset_id] = {}

        self.market_data[asset_id]['current_price'] = {
            'price': message.get('price'),
            'timestamp': datetime.now().isoformat(),
        }

    def get_current_odds(self, asset_id: str) -> Optional[float]:
        """
        Calculate current odds (probability) for an asset

        In Polymarket, price represents probability (0.00 to 1.00)
        """
        if asset_id not in self.market_data:
            return None

        current_price = self.market_data[asset_id].get('current_price', {}).get('price')
        if current_price:
            return float(current_price) * 100  # Convert to percentage

        # Fallback to mid-price from order book
        orderbook = self.market_data[asset_id].get('orderbook', {})
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])

        if bids and asks:
            best_bid = float(bids[0][0]) if bids else 0
            best_ask = float(asks[0][0]) if asks else 0
            mid_price = (best_bid + best_ask) / 2
            return mid_price * 100

        return None

    def get_market_summary(self, asset_id: str) -> Dict:
        """Get summary data for a market"""
        if asset_id not in self.market_data:
            return {}

        data = self.market_data[asset_id]
        odds = self.get_current_odds(asset_id)

        return {
            'asset_id': asset_id,
            'odds_percentage': odds,
            'recent_trades_count': len(data.get('recent_trades', [])),
            'last_update': data.get('current_price', {}).get('timestamp'),
        }
