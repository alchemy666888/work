"""Alert system for market monitoring"""

import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from models.market_state import MarketState
from utils.logger import log_alert


class AlertType(Enum):
    """Types of alerts"""
    PRICE_SWING = "price_swing"
    VOLUME_SPIKE = "volume_spike"
    SPREAD_WIDENING = "spread_widening"
    MARKET_CLOSING = "market_closing"
    PROBABILITY_FLIP = "probability_flip"
    NEW_MARKET = "new_market"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"


@dataclass
class Alert:
    """Represents a market alert"""
    alert_type: AlertType
    message: str
    timestamp: datetime
    severity: str  # 'info', 'warning', 'critical'
    market_slug: str = ""
    outcome: str = ""
    data: dict = field(default_factory=dict)

    def __str__(self):
        return f"[{self.severity.upper()}] {self.alert_type.value}: {self.message}"


class AlertManager:
    """
    Manages alert detection and triggering.

    Monitors market states and triggers alerts based on conditions.
    """

    def __init__(
        self,
        price_swing_threshold: float = 5.0,
        price_swing_window: int = 30,
        volume_spike_multiplier: float = 2.0,
        market_closing_alert: int = 120,
        cooldown_seconds: int = 60,
    ):
        """
        Initialize alert manager.

        Args:
            price_swing_threshold: Percentage threshold for price swing alerts
            price_swing_window: Time window for price swing detection (seconds)
            volume_spike_multiplier: Volume multiplier for spike detection
            market_closing_alert: Seconds before close to alert
            cooldown_seconds: Minimum time between same alert types
        """
        self.price_swing_threshold = price_swing_threshold
        self.price_swing_window = price_swing_window
        self.volume_spike_multiplier = volume_spike_multiplier
        self.market_closing_alert = market_closing_alert
        self.cooldown_seconds = cooldown_seconds

        self.alerts: list[Alert] = []
        self.last_alert_time: dict[str, float] = {}
        self.previous_probabilities: dict[str, float] = {}

    def check_alerts(self, state: MarketState) -> list[Alert]:
        """
        Check all alert conditions for a market state.

        Args:
            state: MarketState to check

        Returns:
            List of triggered alerts
        """
        triggered = []

        # Check price swing
        alert = self._check_price_swing(state)
        if alert:
            triggered.append(alert)

        # Check probability flip
        alert = self._check_probability_flip(state)
        if alert:
            triggered.append(alert)

        # Check market closing
        alert = self._check_market_closing(state)
        if alert:
            triggered.append(alert)

        return triggered

    def _check_price_swing(self, state: MarketState) -> Optional[Alert]:
        """Check for significant price swings."""
        change_pct = state.get_price_change_pct()
        if change_pct is None:
            return None

        if abs(change_pct) < self.price_swing_threshold:
            return None

        # Check cooldown
        key = f"price_swing_{state.market.slug if state.market else 'unknown'}_{state.outcome}"
        if not self._check_cooldown(key):
            return None

        direction = "up" if change_pct > 0 else "down"
        severity = "warning" if abs(change_pct) < 10 else "critical"

        alert = Alert(
            alert_type=AlertType.PRICE_SWING,
            message=f"Price swung {direction} by {abs(change_pct):.2f}%",
            timestamp=datetime.now(),
            severity=severity,
            market_slug=state.market.slug if state.market else "",
            outcome=state.outcome,
            data={
                "change_pct": change_pct,
                "current_price": state.current_price,
                "first_price": state.first_price,
            },
        )

        self._trigger_alert(alert)
        return alert

    def _check_probability_flip(self, state: MarketState) -> Optional[Alert]:
        """Check if probability crossed 50% threshold."""
        prob = state.get_probability()
        if prob is None:
            return None

        key = f"prob_{state.market.slug if state.market else 'unknown'}_{state.outcome}"
        prev_prob = self.previous_probabilities.get(key)

        # Store current probability
        self.previous_probabilities[key] = prob

        if prev_prob is None:
            return None

        # Check if crossed 50%
        crossed = (prev_prob < 50 and prob >= 50) or (prev_prob >= 50 and prob < 50)
        if not crossed:
            return None

        # Check cooldown
        cooldown_key = f"prob_flip_{key}"
        if not self._check_cooldown(cooldown_key):
            return None

        direction = "above" if prob >= 50 else "below"
        alert = Alert(
            alert_type=AlertType.PROBABILITY_FLIP,
            message=f"Probability flipped {direction} 50% (now {prob:.1f}%)",
            timestamp=datetime.now(),
            severity="warning",
            market_slug=state.market.slug if state.market else "",
            outcome=state.outcome,
            data={
                "previous_prob": prev_prob,
                "current_prob": prob,
            },
        )

        self._trigger_alert(alert)
        return alert

    def _check_market_closing(self, state: MarketState) -> Optional[Alert]:
        """Check if market is closing soon."""
        if not state.market or not state.market.close_date:
            return None

        from datetime import timezone

        now = datetime.now(timezone.utc)
        close_date = state.market.close_date

        # Ensure timezone-aware
        if close_date.tzinfo is None:
            close_date = close_date.replace(tzinfo=timezone.utc)

        remaining = (close_date - now).total_seconds()

        if remaining <= 0 or remaining > self.market_closing_alert:
            return None

        # Check cooldown
        key = f"closing_{state.market.slug}"
        if not self._check_cooldown(key):
            return None

        minutes = int(remaining / 60)
        seconds = int(remaining % 60)

        alert = Alert(
            alert_type=AlertType.MARKET_CLOSING,
            message=f"Market closing in {minutes}m {seconds}s",
            timestamp=datetime.now(),
            severity="info",
            market_slug=state.market.slug,
            outcome=state.outcome,
            data={
                "remaining_seconds": remaining,
                "close_date": close_date.isoformat(),
            },
        )

        self._trigger_alert(alert)
        return alert

    def _check_cooldown(self, key: str) -> bool:
        """
        Check if alert is in cooldown period.

        Args:
            key: Unique key for this alert type

        Returns:
            True if alert can be triggered (not in cooldown)
        """
        last_time = self.last_alert_time.get(key, 0)
        current_time = time.time()

        if current_time - last_time < self.cooldown_seconds:
            return False

        self.last_alert_time[key] = current_time
        return True

    def _trigger_alert(self, alert: Alert):
        """
        Trigger an alert and display it.

        Args:
            alert: Alert to trigger
        """
        self.alerts.append(alert)

        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        # Display alert with Rich
        self._display_alert(alert)

    def _display_alert(self, alert: Alert):
        """Log alert to file without interrupting terminal."""
        log_alert(
            severity=alert.severity,
            message=alert.message,
            alert_type=alert.alert_type.value,
            market_slug=alert.market_slug,
            outcome=alert.outcome,
            **alert.data,
        )

    def create_connection_alert(self, connected: bool) -> Alert:
        """Create connection status alert."""
        if connected:
            alert = Alert(
                alert_type=AlertType.CONNECTION_RESTORED,
                message="WebSocket connection restored",
                timestamp=datetime.now(),
                severity="info",
            )
        else:
            alert = Alert(
                alert_type=AlertType.CONNECTION_LOST,
                message="WebSocket connection lost",
                timestamp=datetime.now(),
                severity="critical",
            )

        self._trigger_alert(alert)
        return alert

    def create_new_market_alert(self, market_slug: str, question: str) -> Alert:
        """Create alert for new market discovered."""
        alert = Alert(
            alert_type=AlertType.NEW_MARKET,
            message=f"New market: {question[:50]}",
            timestamp=datetime.now(),
            severity="info",
            market_slug=market_slug,
            data={"question": question},
        )

        self._trigger_alert(alert)
        return alert

    def get_recent_alerts(self, limit: int = 10) -> list[Alert]:
        """Get most recent alerts."""
        return self.alerts[-limit:]

    def get_alerts_by_type(self, alert_type: AlertType) -> list[Alert]:
        """Get alerts of specific type."""
        return [a for a in self.alerts if a.alert_type == alert_type]

    def get_critical_alerts(self) -> list[Alert]:
        """Get all critical alerts."""
        return [a for a in self.alerts if a.severity == "critical"]

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()
        self.last_alert_time.clear()
