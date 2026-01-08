"""WebSocket client for Polymarket real-time market data"""

import asyncio
import json
from typing import Callable, Optional, Set
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from models.events import parse_websocket_event, WebSocketEvent
from utils.logger import logger


class PolymarketWebSocket:
    """
    WebSocket client for Polymarket CLOB real-time data.

    Usage:
        ws_client = PolymarketWebSocket()
        await ws_client.connect(asset_ids, on_message_callback)
    """

    def __init__(
        self,
        url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market",
        ping_interval: int = 10,
        reconnect_base_delay: int = 1,
        max_reconnect_delay: int = 30,
    ):
        self.url = url
        self.ping_interval = ping_interval
        self.reconnect_base_delay = reconnect_base_delay
        self.max_reconnect_delay = max_reconnect_delay

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.retry_count = 0
        self.subscribed_assets: Set[str] = set()

        self._ping_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

    async def connect(
        self,
        asset_ids: Set[str],
        on_message: Callable[[WebSocketEvent], None],
    ):
        """
        Connect to WebSocket and handle messages.

        Args:
            asset_ids: Set of asset/token IDs to subscribe to
            on_message: Callback function for incoming messages
        """
        self.running = True

        while self.running:
            try:
                logger.info(f"Connecting to WebSocket: {self.url}")

                async with websockets.connect(
                    self.url,
                    ping_interval=None,  # We handle pings manually
                    ping_timeout=30,
                    close_timeout=10,
                ) as ws:
                    self.ws = ws
                    self.retry_count = 0
                    logger.info("WebSocket connected successfully")

                    # Subscribe to assets
                    await self.subscribe(list(asset_ids))

                    # Start ping loop
                    self._ping_task = asyncio.create_task(self._ping_loop())

                    # Handle messages
                    await self._message_loop(on_message)

            except ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            # Cleanup
            if self._ping_task:
                self._ping_task.cancel()
                self._ping_task = None

            if not self.running:
                break

            # Reconnect with backoff
            await self._reconnect_delay()

    async def subscribe(self, asset_ids: list[str]):
        """
        Send subscription message for asset IDs.

        Args:
            asset_ids: List of asset/token IDs to subscribe to
        """
        if not self.ws or not asset_ids:
            return

        # Build subscription message
        # Polymarket WebSocket expects a specific format
        subscribe_msg = {
            "type": "subscribe",
            "assets_ids": asset_ids,
        }

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            self.subscribed_assets.update(asset_ids)
            logger.info(f"Subscribed to {len(asset_ids)} assets")
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")

    async def unsubscribe(self, asset_ids: list[str]):
        """
        Unsubscribe from asset IDs.

        Args:
            asset_ids: List of asset/token IDs to unsubscribe from
        """
        if not self.ws or not asset_ids:
            return

        unsubscribe_msg = {
            "type": "unsubscribe",
            "assets_ids": asset_ids,
        }

        try:
            await self.ws.send(json.dumps(unsubscribe_msg))
            self.subscribed_assets.difference_update(asset_ids)
            logger.info(f"Unsubscribed from {len(asset_ids)} assets")
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")

    async def _ping_loop(self):
        """Send periodic PING messages to keep connection alive."""
        try:
            while self.running and self.ws:
                await asyncio.sleep(self.ping_interval)
                if self.ws:
                    try:
                        # Send custom ping message
                        ping_msg = {"type": "ping"}
                        await self.ws.send(json.dumps(ping_msg))
                        logger.debug("Ping sent")
                    except Exception as e:
                        logger.warning(f"Ping failed: {e}")
                        break
        except asyncio.CancelledError:
            pass

    async def _message_loop(self, on_message: Callable[[WebSocketEvent], None]):
        """
        Process incoming WebSocket messages.

        Args:
            on_message: Callback for each message
        """
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)

                    # Handle pong messages
                    msg_type = data.get("type", "")
                    if msg_type == "pong":
                        logger.debug("Pong received")
                        continue

                    # Parse and dispatch event
                    event = parse_websocket_event(data)
                    await self._handle_message(event, on_message)

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            pass

    async def _handle_message(
        self,
        event: WebSocketEvent,
        on_message: Callable[[WebSocketEvent], None],
    ):
        """
        Handle parsed WebSocket event.

        Args:
            event: Parsed WebSocket event
            on_message: Callback function
        """
        try:
            # Call callback (can be sync or async)
            if asyncio.iscoroutinefunction(on_message):
                await on_message(event)
            else:
                on_message(event)
        except Exception as e:
            logger.error(f"Error in message handler: {e}")

    async def _reconnect_delay(self):
        """Calculate and apply reconnection delay with exponential backoff."""
        self.retry_count += 1
        delay = min(
            self.reconnect_base_delay * (2 ** (self.retry_count - 1)),
            self.max_reconnect_delay,
        )
        logger.info(f"Reconnecting in {delay}s (attempt {self.retry_count})")
        await asyncio.sleep(delay)

    async def disconnect(self):
        """Gracefully disconnect from WebSocket."""
        self.running = False

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

        logger.info("WebSocket disconnected")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.ws is not None and self.ws.open

    def get_subscribed_assets(self) -> Set[str]:
        """Get set of subscribed asset IDs."""
        return self.subscribed_assets.copy()

    def get_status(self) -> dict:
        """Get connection status information."""
        return {
            "connected": self.is_connected(),
            "running": self.running,
            "retry_count": self.retry_count,
            "subscribed_assets": len(self.subscribed_assets),
            "assets": list(self.subscribed_assets),
        }
