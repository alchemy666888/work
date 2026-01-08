"""Volume tracking and analysis"""

import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class Trade:
    """Single trade record"""
    timestamp: float
    size: float
    price: float
    side: str = "unknown"  # 'buy', 'sell', or 'unknown'


class VolumeTracker:
    """
    Track trading volume and analyze patterns.

    Maintains trade history and calculates volume metrics.
    """

    def __init__(self, window_size: int = 500):
        """
        Initialize volume tracker.

        Args:
            window_size: Maximum number of trades to keep
        """
        self.trades: list[Trade] = []
        self.window_size = window_size
        self.total_volume: float = 0.0
        self.volume_by_side: dict[str, float] = {
            "buy": 0.0,
            "sell": 0.0,
            "unknown": 0.0,
        }

    def add_trade(
        self,
        size: float,
        price: float,
        side: str = "unknown",
        timestamp: Optional[float] = None,
    ):
        """
        Record a trade.

        Args:
            size: Trade size
            price: Trade price
            side: Trade side ('buy', 'sell', or 'unknown')
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        trade = Trade(
            timestamp=timestamp,
            size=size,
            price=price,
            side=side,
        )

        self.trades.append(trade)
        self.total_volume += size

        if side in self.volume_by_side:
            self.volume_by_side[side] += size

        # Trim to window size
        if len(self.trades) > self.window_size:
            removed = self.trades.pop(0)
            # Note: We don't subtract from total_volume to keep lifetime total
            if removed.side in self.volume_by_side:
                self.volume_by_side[removed.side] -= removed.size

    def get_volume_in_window(self, window_seconds: int = 300) -> float:
        """
        Get total volume in recent time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Total volume in window
        """
        cutoff = time.time() - window_seconds
        return sum(t.size for t in self.trades if t.timestamp >= cutoff)

    def get_trade_count_in_window(self, window_seconds: int = 300) -> int:
        """
        Get number of trades in recent time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Number of trades
        """
        cutoff = time.time() - window_seconds
        return sum(1 for t in self.trades if t.timestamp >= cutoff)

    def get_average_trade_size(self, window_seconds: Optional[int] = None) -> Optional[float]:
        """
        Calculate average trade size.

        Args:
            window_seconds: Optional time window (None for all trades)

        Returns:
            Average trade size or None
        """
        if window_seconds is None:
            trades = self.trades
        else:
            cutoff = time.time() - window_seconds
            trades = [t for t in self.trades if t.timestamp >= cutoff]

        if not trades:
            return None

        return sum(t.size for t in trades) / len(trades)

    def get_volume_weighted_price(self, window_seconds: int = 300) -> Optional[float]:
        """
        Calculate volume-weighted average price (VWAP).

        Args:
            window_seconds: Time window in seconds

        Returns:
            VWAP or None
        """
        cutoff = time.time() - window_seconds
        window_trades = [t for t in self.trades if t.timestamp >= cutoff]

        if not window_trades:
            return None

        total_volume = sum(t.size for t in window_trades)
        if total_volume == 0:
            return None

        weighted_sum = sum(t.size * t.price for t in window_trades)
        return weighted_sum / total_volume

    def detect_volume_spike(
        self,
        multiplier: float = 2.0,
        window_seconds: int = 60,
        baseline_seconds: int = 300,
    ) -> bool:
        """
        Detect if recent volume is significantly higher than baseline.

        Args:
            multiplier: How many times higher volume must be
            window_seconds: Recent window to check
            baseline_seconds: Baseline period for comparison

        Returns:
            True if volume spike detected
        """
        recent_volume = self.get_volume_in_window(window_seconds)
        baseline_volume = self.get_volume_in_window(baseline_seconds)

        # Adjust baseline to same time scale
        baseline_per_window = (baseline_volume / baseline_seconds) * window_seconds

        if baseline_per_window == 0:
            return False

        return recent_volume >= baseline_per_window * multiplier

    def get_buy_sell_ratio(self, window_seconds: int = 300) -> Optional[float]:
        """
        Calculate buy/sell volume ratio in time window.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Ratio (>1 = more buying) or None
        """
        cutoff = time.time() - window_seconds
        window_trades = [t for t in self.trades if t.timestamp >= cutoff]

        buy_volume = sum(t.size for t in window_trades if t.side == "buy")
        sell_volume = sum(t.size for t in window_trades if t.side == "sell")

        if sell_volume == 0:
            return None if buy_volume == 0 else float("inf")

        return buy_volume / sell_volume

    def get_total_volume(self) -> float:
        """Get total lifetime volume."""
        return self.total_volume

    def get_trade_count(self) -> int:
        """Get total number of trades stored."""
        return len(self.trades)

    def get_last_trade(self) -> Optional[Trade]:
        """Get most recent trade."""
        if not self.trades:
            return None
        return self.trades[-1]

    def get_volume_rate(self, window_seconds: int = 60) -> float:
        """
        Calculate volume rate (volume per second).

        Args:
            window_seconds: Time window in seconds

        Returns:
            Volume per second
        """
        volume = self.get_volume_in_window(window_seconds)
        return volume / window_seconds

    def clear(self):
        """Clear all trade history."""
        self.trades.clear()
        self.total_volume = 0.0
        self.volume_by_side = {
            "buy": 0.0,
            "sell": 0.0,
            "unknown": 0.0,
        }

    def to_dict(self) -> dict:
        """Export tracker state as dictionary."""
        return {
            "total_volume": self.total_volume,
            "trade_count": len(self.trades),
            "volume_5m": self.get_volume_in_window(300),
            "volume_1m": self.get_volume_in_window(60),
            "trades_5m": self.get_trade_count_in_window(300),
            "trades_1m": self.get_trade_count_in_window(60),
            "avg_trade_size": self.get_average_trade_size(),
            "vwap_5m": self.get_volume_weighted_price(300),
            "buy_sell_ratio": self.get_buy_sell_ratio(),
            "volume_rate": self.get_volume_rate(),
        }
