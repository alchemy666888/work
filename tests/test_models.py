"""Tests for data models"""

import pytest
from datetime import datetime, timezone

from models.market import Market
from models.events import (
    WebSocketEvent,
    BestBidAskEvent,
    LastTradePriceEvent,
    OrderBookEvent,
    parse_websocket_event,
)
from models.market_state import MarketState


class TestMarketModel:
    """Tests for Market model"""

    def test_market_creation(self):
        """Test basic market creation"""
        market = Market(
            id="test-id",
            slug="btc-updown-15m-123456",
            question="Will BTC go up in 15 minutes?",
            active=True,
            closed=False,
            clob_token_ids=["token1", "token2"],
            outcomes=["Up", "Down"],
            outcome_prices=["0.55", "0.45"],
        )

        assert market.id == "test-id"
        assert market.active is True
        assert market.closed is False

    def test_get_up_token_id(self):
        """Test getting UP token ID"""
        market = Market(
            id="test",
            slug="test-slug",
            question="Test",
            clob_token_ids=["up-token", "down-token"],
        )

        assert market.get_up_token_id() == "up-token"

    def test_get_down_token_id(self):
        """Test getting DOWN token ID"""
        market = Market(
            id="test",
            slug="test-slug",
            question="Test",
            clob_token_ids=["up-token", "down-token"],
        )

        assert market.get_down_token_id() == "down-token"

    def test_get_prices(self):
        """Test getting outcome prices"""
        market = Market(
            id="test",
            slug="test-slug",
            question="Test",
            outcome_prices=["0.55", "0.45"],
        )

        assert market.get_up_price() == 0.55
        assert market.get_down_price() == 0.45

    def test_is_btc_15m_market(self):
        """Test BTC 15m market detection"""
        btc_market = Market(
            id="test",
            slug="btc-updown-15min",
            question="Will BTC go up in the next 15 minutes?",
        )
        assert btc_market.is_btc_15m_market() is True

        non_btc_market = Market(
            id="test",
            slug="eth-updown",
            question="Will ETH go up?",
        )
        assert non_btc_market.is_btc_15m_market() is False


class TestWebSocketEvents:
    """Tests for WebSocket event models"""

    def test_parse_best_bid_ask_event(self):
        """Test parsing best bid/ask event"""
        data = {
            "type": "best_bid_ask",
            "asset_id": "token123",
            "best_bid": "0.50",
            "best_ask": "0.52",
        }

        event = parse_websocket_event(data)
        assert isinstance(event, BestBidAskEvent)
        assert event.best_bid == "0.50"
        assert event.best_ask == "0.52"

    def test_best_bid_ask_mid_price(self):
        """Test mid price calculation"""
        event = BestBidAskEvent(
            event_type="best_bid_ask",
            best_bid="0.50",
            best_ask="0.52",
        )

        assert event.get_mid_price() == 0.51

    def test_parse_last_trade_event(self):
        """Test parsing last trade event"""
        data = {
            "type": "last_trade_price",
            "asset_id": "token123",
            "price": "0.55",
            "size": "100",
        }

        event = parse_websocket_event(data)
        assert isinstance(event, LastTradePriceEvent)
        assert event.get_price_float() == 0.55
        assert event.get_size_float() == 100

    def test_parse_order_book_event(self):
        """Test parsing order book event"""
        data = {
            "type": "book",
            "asset_id": "token123",
            "bids": [["0.50", "100"], ["0.49", "200"]],
            "asks": [["0.52", "150"], ["0.53", "250"]],
        }

        event = parse_websocket_event(data)
        assert isinstance(event, OrderBookEvent)
        assert event.get_best_bid() == 0.50
        assert event.get_best_ask() == 0.52

    def test_parse_unknown_event(self):
        """Test parsing unknown event type"""
        data = {
            "type": "unknown_type",
            "asset_id": "token123",
        }

        event = parse_websocket_event(data)
        assert isinstance(event, WebSocketEvent)
        assert event.event_type == "unknown_type"


class TestMarketState:
    """Tests for MarketState"""

    def test_market_state_creation(self):
        """Test creating market state"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        assert state.outcome == "UP"
        assert state.current_price is None
        assert state.total_volume == 0.0

    def test_update_price(self):
        """Test price updates"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        state.update_price(0.50)
        assert state.current_price == 0.50
        assert state.first_price == 0.50

        state.update_price(0.55)
        assert state.current_price == 0.55
        assert state.first_price == 0.50  # Should not change
        assert state.max_price == 0.55
        assert state.min_price == 0.50

    def test_add_trade(self):
        """Test adding trades"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        state.add_trade(100, 0.50)
        assert state.total_volume == 100
        assert len(state.trade_history) == 1

        state.add_trade(200, 0.55)
        assert state.total_volume == 300
        assert len(state.trade_history) == 2

    def test_get_probability(self):
        """Test probability calculation"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        # Test with 0-1 scale price
        state.update_price(0.55)
        assert state.get_probability() == 55.0

        # Test with 0-100 scale price
        state.update_price(55)
        assert state.get_probability() == 55

    def test_get_price_change_pct(self):
        """Test price change percentage"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        state.update_price(0.50)
        state.update_price(0.55)

        change = state.get_price_change_pct()
        assert change == pytest.approx(10.0, rel=0.01)

    def test_update_bid_ask(self):
        """Test bid/ask updates"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        state.update_bid_ask(0.50, 0.52)
        assert state.best_bid == 0.50
        assert state.best_ask == 0.52
        # Should also update price to mid
        assert state.current_price == 0.51

    def test_get_spread(self):
        """Test spread calculation"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        state.update_bid_ask(0.50, 0.52)
        spread = state.get_spread()

        # Spread should be (0.52 - 0.50) / 0.51 * 100 ≈ 3.92%
        assert spread == pytest.approx(3.92, rel=0.1)

    def test_to_dict(self):
        """Test serialization to dict"""
        market = Market(id="test", slug="test-slug", question="Test")
        state = MarketState(market=market, outcome="UP")

        state.update_price(0.55)
        state.add_trade(100, 0.55)

        result = state.to_dict()

        assert result["market_id"] == "test"
        assert result["outcome"] == "UP"
        assert result["current_price"] == 0.55
        assert result["total_volume"] == 100
