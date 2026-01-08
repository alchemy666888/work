"""WebSocket event models"""

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class WebSocketEvent(BaseModel):
    """Base model for WebSocket events from Polymarket"""

    event_type: str = Field(alias="type", description="Type of WebSocket event")
    asset_id: Optional[str] = Field(default=None, description="Asset/token ID")
    market: Optional[str] = Field(default=None, description="Market identifier")
    timestamp: Optional[str] = Field(default=None, description="Event timestamp")

    class Config:
        populate_by_name = True
        extra = "allow"


class BestBidAskEvent(WebSocketEvent):
    """Best bid/ask price update event"""

    best_bid: Optional[str] = Field(default=None, description="Best bid price")
    best_ask: Optional[str] = Field(default=None, description="Best ask price")
    spread: Optional[str] = Field(default=None, description="Bid-ask spread")

    def get_mid_price(self) -> Optional[float]:
        """Calculate mid price from bid/ask"""
        try:
            if self.best_bid and self.best_ask:
                bid = float(self.best_bid)
                ask = float(self.best_ask)
                return (bid + ask) / 2
        except (ValueError, TypeError):
            pass
        return None


class LastTradePriceEvent(WebSocketEvent):
    """Last trade price event"""

    price: Optional[str] = Field(default=None, description="Trade price")
    size: Optional[str] = Field(default=None, description="Trade size")
    trade_id: Optional[str] = Field(default=None, description="Trade identifier")
    side: Optional[str] = Field(default=None, description="Trade side (buy/sell)")

    def get_price_float(self) -> Optional[float]:
        """Get price as float"""
        try:
            if self.price:
                return float(self.price)
        except (ValueError, TypeError):
            pass
        return None

    def get_size_float(self) -> Optional[float]:
        """Get size as float"""
        try:
            if self.size:
                return float(self.size)
        except (ValueError, TypeError):
            pass
        return None


class OrderBookEntry(BaseModel):
    """Single order book entry (bid or ask)"""

    price: str
    size: str

    class Config:
        extra = "allow"


class OrderBookEvent(WebSocketEvent):
    """Order book snapshot/update event"""

    bids: Optional[list[OrderBookEntry]] = Field(
        default=None, description="List of bid entries"
    )
    asks: Optional[list[OrderBookEntry]] = Field(
        default=None, description="List of ask entries"
    )

    @field_validator("bids", "asks", mode="before")
    @classmethod
    def parse_order_book_entries(cls, value: Any) -> Optional[list[OrderBookEntry]]:
        """Parse order book entries from various formats."""
        if value is None:
            return None
        if not isinstance(value, list):
            return None

        entries = []
        for item in value:
            if isinstance(item, dict):
                # Dict format: {'price': '0.57', 'size': '721.93'}
                entries.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # Tuple/list format: ('0.57', '721.93') or ['0.57', '721.93']
                entries.append({"price": str(item[0]), "size": str(item[1])})
            else:
                continue
        return entries

    def get_best_bid(self) -> Optional[float]:
        """Get best (highest) bid price"""
        if self.bids and len(self.bids) > 0:
            try:
                return float(self.bids[0].price)
            except (ValueError, TypeError, AttributeError):
                pass
        return None

    def get_best_ask(self) -> Optional[float]:
        """Get best (lowest) ask price"""
        if self.asks and len(self.asks) > 0:
            try:
                return float(self.asks[0].price)
            except (ValueError, TypeError, AttributeError):
                pass
        return None

    def get_mid_price(self) -> Optional[float]:
        """Calculate mid price from order book"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid is not None and best_ask is not None:
            return (best_bid + best_ask) / 2
        return None


class SubscriptionEvent(WebSocketEvent):
    """Subscription confirmation event"""

    assets_ids: Optional[list[str]] = Field(
        default=None, description="Subscribed asset IDs"
    )
    status: Optional[str] = Field(default=None, description="Subscription status")


def parse_websocket_event(data: dict) -> WebSocketEvent:
    """
    Parse WebSocket message data into appropriate event type.

    Args:
        data: Raw WebSocket message data

    Returns:
        Parsed event object of appropriate type
    """
    event_type = data.get("type", data.get("event_type", "unknown"))

    if event_type == "best_bid_ask":
        return BestBidAskEvent(**data)
    elif event_type == "last_trade_price":
        return LastTradePriceEvent(**data)
    elif event_type == "book":
        return OrderBookEvent(**data)
    elif event_type == "subscribed":
        return SubscriptionEvent(**data)
    else:
        return WebSocketEvent(**data)
