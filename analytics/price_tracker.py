"""Price tracking and analysis"""

import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PricePoint:
    """Single price data point"""
    timestamp: float
    price: float


class PriceTracker:
    """
    Track price history and calculate analytics.

    Maintains a rolling window of price data for analysis.
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize price tracker.

        Args:
            window_size: Maximum number of price points to keep
        """
        self.prices: list[PricePoint] = []
        self.window_size = window_size
        self.first_price: Optional[float] = None

    def add_price(self, price: float, timestamp: Optional[float] = None):
        """
        Record a price point.

        Args:
            price: Price value
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        # Record first price
        if self.first_price is None:
            self.first_price = price

        # Add to history
        self.prices.append(PricePoint(timestamp=timestamp, price=price))

        # Trim to window size
        if len(self.prices) > self.window_size:
            self.prices = self.prices[-self.window_size:]

    def get_current_price(self) -> Optional[float]:
        """Get the most recent price."""
        if not self.prices:
            return None
        return self.prices[-1].price

    def get_moving_average(self, window_seconds: int = 60) -> Optional[float]:
        """
        Calculate moving average over time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Moving average or None if not enough data
        """
        if not self.prices:
            return None

        cutoff = time.time() - window_seconds
        window_prices = [p.price for p in self.prices if p.timestamp >= cutoff]

        if not window_prices:
            return None

        return sum(window_prices) / len(window_prices)

    def detect_rapid_change(
        self,
        threshold_pct: float = 5.0,
        window_seconds: int = 30,
    ) -> bool:
        """
        Detect if price changed more than threshold in time window.

        Args:
            threshold_pct: Percentage threshold
            window_seconds: Time window in seconds

        Returns:
            True if rapid change detected
        """
        if len(self.prices) < 2:
            return False

        cutoff = time.time() - window_seconds
        window_prices = [p for p in self.prices if p.timestamp >= cutoff]

        if len(window_prices) < 2:
            return False

        # Get first and last prices in window
        first_price = window_prices[0].price
        last_price = window_prices[-1].price

        if first_price == 0:
            return False

        change_pct = abs((last_price - first_price) / first_price) * 100
        return change_pct >= threshold_pct

    def get_price_change(self) -> Optional[float]:
        """
        Get absolute price change from first recorded price.

        Returns:
            Price change or None
        """
        current = self.get_current_price()
        if current is None or self.first_price is None:
            return None
        return current - self.first_price

    def get_price_change_pct(self) -> Optional[float]:
        """
        Get percentage price change from first recorded price.

        Returns:
            Percentage change or None
        """
        current = self.get_current_price()
        if current is None or self.first_price is None or self.first_price == 0:
            return None
        return ((current - self.first_price) / self.first_price) * 100

    def get_min_price(self) -> Optional[float]:
        """Get minimum price in history."""
        if not self.prices:
            return None
        return min(p.price for p in self.prices)

    def get_max_price(self) -> Optional[float]:
        """Get maximum price in history."""
        if not self.prices:
            return None
        return max(p.price for p in self.prices)

    def get_price_range(self) -> Optional[float]:
        """Get price range (max - min)."""
        min_price = self.get_min_price()
        max_price = self.get_max_price()
        if min_price is None or max_price is None:
            return None
        return max_price - min_price

    def get_volatility(self, window_seconds: int = 60) -> Optional[float]:
        """
        Calculate price volatility (standard deviation) over time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Volatility or None
        """
        if len(self.prices) < 2:
            return None

        cutoff = time.time() - window_seconds
        window_prices = [p.price for p in self.prices if p.timestamp >= cutoff]

        if len(window_prices) < 2:
            return None

        mean = sum(window_prices) / len(window_prices)
        variance = sum((p - mean) ** 2 for p in window_prices) / len(window_prices)
        return variance ** 0.5

    def get_trend(self, window_seconds: int = 60) -> Optional[str]:
        """
        Determine price trend over time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            'up', 'down', 'stable', or None
        """
        change_pct = self.get_recent_change_pct(window_seconds)
        if change_pct is None:
            return None

        if change_pct > 1.0:
            return "up"
        elif change_pct < -1.0:
            return "down"
        else:
            return "stable"

    def get_recent_change_pct(self, window_seconds: int = 60) -> Optional[float]:
        """
        Get percentage change over recent time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Percentage change or None
        """
        if len(self.prices) < 2:
            return None

        cutoff = time.time() - window_seconds
        window_prices = [p for p in self.prices if p.timestamp >= cutoff]

        if len(window_prices) < 2:
            return None

        first_price = window_prices[0].price
        last_price = window_prices[-1].price

        if first_price == 0:
            return None

        return ((last_price - first_price) / first_price) * 100

    def get_price_points_count(self) -> int:
        """Get number of price points stored."""
        return len(self.prices)

    def clear(self):
        """Clear all price history."""
        self.prices.clear()
        self.first_price = None

    def to_dict(self) -> dict:
        """Export tracker state as dictionary."""
        return {
            "current_price": self.get_current_price(),
            "first_price": self.first_price,
            "min_price": self.get_min_price(),
            "max_price": self.get_max_price(),
            "price_range": self.get_price_range(),
            "change_pct": self.get_price_change_pct(),
            "moving_avg_60s": self.get_moving_average(60),
            "volatility_60s": self.get_volatility(60),
            "trend": self.get_trend(),
            "data_points": len(self.prices),
        }


def calculate_probability(price: float) -> float:
    """
    Convert price to probability percentage.

    In Polymarket, prices are typically 0-1 representing probability.

    Args:
        price: Price value

    Returns:
        Probability as percentage (0-100)
    """
    # Normalize to percentage
    if price <= 1:
        return price * 100
    return price
