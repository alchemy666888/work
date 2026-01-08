"""Tests for analytics modules"""

import pytest
import time

from analytics.price_tracker import PriceTracker, calculate_probability
from analytics.volume_tracker import VolumeTracker
from analytics.alerts import AlertManager, AlertType, Alert
from models.market import Market
from models.market_state import MarketState


class TestPriceTracker:
    """Tests for PriceTracker"""

    def test_add_price(self):
        """Test adding price points"""
        tracker = PriceTracker()

        tracker.add_price(0.50)
        assert tracker.get_current_price() == 0.50
        assert tracker.first_price == 0.50

        tracker.add_price(0.55)
        assert tracker.get_current_price() == 0.55
        assert tracker.first_price == 0.50

    def test_price_change(self):
        """Test price change calculation"""
        tracker = PriceTracker()

        tracker.add_price(0.50)
        tracker.add_price(0.55)

        assert tracker.get_price_change() == 0.05
        assert tracker.get_price_change_pct() == pytest.approx(10.0, rel=0.01)

    def test_min_max_price(self):
        """Test min/max tracking"""
        tracker = PriceTracker()

        tracker.add_price(0.50)
        tracker.add_price(0.45)
        tracker.add_price(0.60)
        tracker.add_price(0.55)

        assert tracker.get_min_price() == 0.45
        assert tracker.get_max_price() == 0.60
        assert tracker.get_price_range() == 0.15

    def test_window_size_limit(self):
        """Test that window size is enforced"""
        tracker = PriceTracker(window_size=5)

        for i in range(10):
            tracker.add_price(float(i))

        assert tracker.get_price_points_count() == 5

    def test_moving_average(self):
        """Test moving average calculation"""
        tracker = PriceTracker()

        # Add prices with current timestamp
        now = time.time()
        for i in range(5):
            tracker.add_price(float(i + 1), now - (4 - i))

        avg = tracker.get_moving_average(window_seconds=60)
        assert avg == 3.0  # (1+2+3+4+5)/5

    def test_detect_rapid_change(self):
        """Test rapid change detection"""
        tracker = PriceTracker()

        now = time.time()
        tracker.add_price(0.50, now - 10)
        tracker.add_price(0.60, now)  # 20% change

        assert tracker.detect_rapid_change(threshold_pct=5.0, window_seconds=30) is True
        assert tracker.detect_rapid_change(threshold_pct=25.0, window_seconds=30) is False

    def test_clear(self):
        """Test clearing tracker"""
        tracker = PriceTracker()

        tracker.add_price(0.50)
        tracker.add_price(0.55)
        tracker.clear()

        assert tracker.get_current_price() is None
        assert tracker.first_price is None
        assert tracker.get_price_points_count() == 0


class TestCalculateProbability:
    """Tests for probability calculation"""

    def test_normalize_decimal(self):
        """Test normalizing decimal price to percentage"""
        assert calculate_probability(0.55) == 55.0
        assert calculate_probability(0.0) == 0.0
        assert calculate_probability(1.0) == 100.0

    def test_already_percentage(self):
        """Test price already in percentage form"""
        assert calculate_probability(55) == 55
        assert calculate_probability(100) == 100


class TestVolumeTracker:
    """Tests for VolumeTracker"""

    def test_add_trade(self):
        """Test adding trades"""
        tracker = VolumeTracker()

        tracker.add_trade(100, 0.50)
        assert tracker.get_total_volume() == 100
        assert tracker.get_trade_count() == 1

        tracker.add_trade(200, 0.55)
        assert tracker.get_total_volume() == 300
        assert tracker.get_trade_count() == 2

    def test_volume_by_side(self):
        """Test volume tracking by side"""
        tracker = VolumeTracker()

        tracker.add_trade(100, 0.50, side="buy")
        tracker.add_trade(50, 0.50, side="sell")

        ratio = tracker.get_buy_sell_ratio(window_seconds=3600)
        assert ratio == 2.0  # 100/50

    def test_average_trade_size(self):
        """Test average trade size calculation"""
        tracker = VolumeTracker()

        tracker.add_trade(100, 0.50)
        tracker.add_trade(200, 0.55)
        tracker.add_trade(300, 0.60)

        avg = tracker.get_average_trade_size()
        assert avg == 200.0

    def test_vwap(self):
        """Test VWAP calculation"""
        tracker = VolumeTracker()

        now = time.time()
        tracker.add_trade(100, 0.50, timestamp=now)
        tracker.add_trade(200, 0.60, timestamp=now)

        vwap = tracker.get_volume_weighted_price(window_seconds=60)
        # VWAP = (100*0.50 + 200*0.60) / 300 = 170/300 ≈ 0.567
        assert vwap == pytest.approx(0.567, rel=0.01)

    def test_last_trade(self):
        """Test getting last trade"""
        tracker = VolumeTracker()

        tracker.add_trade(100, 0.50)
        tracker.add_trade(200, 0.55)

        last = tracker.get_last_trade()
        assert last is not None
        assert last.size == 200
        assert last.price == 0.55

    def test_clear(self):
        """Test clearing tracker"""
        tracker = VolumeTracker()

        tracker.add_trade(100, 0.50)
        tracker.clear()

        assert tracker.get_total_volume() == 0.0
        assert tracker.get_trade_count() == 0


class TestAlertManager:
    """Tests for AlertManager"""

    def test_create_alert_manager(self):
        """Test creating alert manager"""
        manager = AlertManager(
            price_swing_threshold=5.0,
            cooldown_seconds=1,
        )

        assert manager.price_swing_threshold == 5.0

    def test_price_swing_alert(self):
        """Test price swing alert detection"""
        manager = AlertManager(
            price_swing_threshold=5.0,
            cooldown_seconds=0,  # Disable cooldown for testing
        )

        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        # Set initial price
        state.update_price(0.50)
        state.first_price = 0.50

        # Update to trigger alert (12% change)
        state.update_price(0.56)

        # Check alerts
        alerts = manager.check_alerts(state)

        # Should detect price swing
        price_alerts = [a for a in alerts if a.alert_type == AlertType.PRICE_SWING]
        assert len(price_alerts) > 0

    def test_new_market_alert(self):
        """Test new market alert creation"""
        manager = AlertManager()

        alert = manager.create_new_market_alert("test-slug", "Test Question")

        assert alert.alert_type == AlertType.NEW_MARKET
        assert "Test Question" in alert.message

    def test_connection_alert(self):
        """Test connection status alerts"""
        manager = AlertManager()

        # Test connection lost
        alert = manager.create_connection_alert(connected=False)
        assert alert.alert_type == AlertType.CONNECTION_LOST
        assert alert.severity == "critical"

        # Test connection restored
        alert = manager.create_connection_alert(connected=True)
        assert alert.alert_type == AlertType.CONNECTION_RESTORED
        assert alert.severity == "info"

    def test_get_recent_alerts(self):
        """Test getting recent alerts"""
        manager = AlertManager()

        # Create some alerts
        for i in range(5):
            manager.create_new_market_alert(f"slug-{i}", f"Market {i}")

        recent = manager.get_recent_alerts(limit=3)
        assert len(recent) == 3

    def test_get_alerts_by_type(self):
        """Test filtering alerts by type"""
        manager = AlertManager()

        manager.create_new_market_alert("slug-1", "Market 1")
        manager.create_connection_alert(connected=False)
        manager.create_new_market_alert("slug-2", "Market 2")

        new_market_alerts = manager.get_alerts_by_type(AlertType.NEW_MARKET)
        assert len(new_market_alerts) == 2

        connection_alerts = manager.get_alerts_by_type(AlertType.CONNECTION_LOST)
        assert len(connection_alerts) == 1

    def test_clear_alerts(self):
        """Test clearing alerts"""
        manager = AlertManager()

        manager.create_new_market_alert("slug-1", "Market 1")
        manager.clear_alerts()

        assert len(manager.alerts) == 0
