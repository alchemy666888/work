"""Market state tracking"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from .market import Market


@dataclass
class MarketState:
    """
    Tracks the state and history of a market outcome.

    This class maintains price history, trade history, and calculates
    various metrics for a specific market outcome.
    """

    market: Market
    outcome: str
    is_current: bool = True

    # Price tracking
    price_history: list[tuple[datetime, float]] = field(default_factory=list)
    current_price: Optional[float] = None
    first_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

    # Volume tracking
    trade_history: list[dict] = field(default_factory=list)
    total_volume: float = 0.0

    # Best bid/ask
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None

    # Timestamps
    last_update: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def update_price(self, price: float, timestamp: Optional[datetime] = None):
        """
        Update price and track history.

        Args:
            price: New price value
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Update price history
        self.price_history.append((timestamp, price))

        # Keep only last 1000 price points
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]

        # Update current price
        self.current_price = price

        # Track first price
        if self.first_price is None:
            self.first_price = price

        # Update min/max
        if self.min_price is None or price < self.min_price:
            self.min_price = price
        if self.max_price is None or price > self.max_price:
            self.max_price = price

        self.last_update = timestamp

    def update_bid_ask(self, bid: Optional[float], ask: Optional[float]):
        """
        Update best bid and ask prices.

        Args:
            bid: Best bid price
            ask: Best ask price
        """
        if bid is not None:
            self.best_bid = bid
        if ask is not None:
            self.best_ask = ask

        # Calculate mid price and update
        if self.best_bid is not None and self.best_ask is not None:
            mid_price = (self.best_bid + self.best_ask) / 2
            self.update_price(mid_price)

    def add_trade(self, size: float, price: float, timestamp: Optional[datetime] = None):
        """
        Record a trade and update volume.

        Args:
            size: Trade size
            price: Trade price
            timestamp: Optional trade timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()

        trade = {
            "timestamp": timestamp,
            "size": size,
            "price": price,
        }

        self.trade_history.append(trade)

        # Keep only last 500 trades
        if len(self.trade_history) > 500:
            self.trade_history = self.trade_history[-500:]

        # Update total volume
        self.total_volume += size

        # Update price from trade
        self.update_price(price, timestamp)

    def get_probability(self) -> Optional[float]:
        """
        Calculate implied probability from price.

        In Polymarket, price represents probability (0-1 scale).

        Returns:
            Probability as percentage (0-100)
        """
        if self.current_price is None:
            return None

        # Normalize to percentage
        if self.current_price <= 1:
            return self.current_price * 100
        return self.current_price

    def get_price_change_pct(self) -> Optional[float]:
        """
        Calculate percentage change from first price.

        Returns:
            Percentage change or None if not enough data
        """
        if self.first_price is None or self.current_price is None:
            return None

        if self.first_price == 0:
            return None

        return ((self.current_price - self.first_price) / self.first_price) * 100

    def get_spread(self) -> Optional[float]:
        """
        Calculate bid-ask spread.

        Returns:
            Spread as percentage of mid price
        """
        if self.best_bid is None or self.best_ask is None:
            return None

        mid = (self.best_bid + self.best_ask) / 2
        if mid == 0:
            return None

        return ((self.best_ask - self.best_bid) / mid) * 100

    def get_price_range(self) -> Optional[float]:
        """
        Calculate price range (max - min).

        Returns:
            Price range or None
        """
        if self.min_price is None or self.max_price is None:
            return None
        return self.max_price - self.min_price

    def get_recent_volume(self, seconds: int = 300) -> float:
        """
        Get volume in recent time window.

        Args:
            seconds: Time window in seconds

        Returns:
            Total volume in time window
        """
        cutoff = datetime.now()
        from datetime import timedelta

        cutoff = cutoff - timedelta(seconds=seconds)

        recent_volume = sum(
            trade["size"]
            for trade in self.trade_history
            if trade["timestamp"] >= cutoff
        )
        return recent_volume

    def get_trade_count(self, seconds: Optional[int] = None) -> int:
        """
        Get number of trades, optionally within time window.

        Args:
            seconds: Optional time window in seconds

        Returns:
            Number of trades
        """
        if seconds is None:
            return len(self.trade_history)

        from datetime import timedelta

        cutoff = datetime.now() - timedelta(seconds=seconds)
        return sum(1 for trade in self.trade_history if trade["timestamp"] >= cutoff)

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        return {
            "market_id": self.market.id if self.market else None,
            "outcome": self.outcome,
            "is_current": self.is_current,
            "current_price": self.current_price,
            "first_price": self.first_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "total_volume": self.total_volume,
            "best_bid": self.best_bid,
            "best_ask": self.best_ask,
            "trade_count": len(self.trade_history),
            "probability": self.get_probability(),
            "price_change_pct": self.get_price_change_pct(),
            "spread": self.get_spread(),
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }
