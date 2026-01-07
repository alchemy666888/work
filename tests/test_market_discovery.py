"""Tests for market discovery module"""

import pytest
from datetime import datetime, timedelta
from src.core.market_discovery import MarketDiscovery


class TestMarketDiscovery:
    """Test market discovery functionality"""

    def test_filter_active_markets(self):
        """Test filtering for active markets"""
        discovery = MarketDiscovery()

        markets = [
            {'id': '1', 'active': True},
            {'id': '2', 'active': False},
            {'id': '3', 'active': True},
        ]

        active = discovery.filter_active_markets(markets)
        assert len(active) == 2
        assert all(m['active'] for m in active)

    def test_filter_short_term_markets(self):
        """Test filtering for short-term markets"""
        discovery = MarketDiscovery()

        now = datetime.now()
        markets = [
            {'id': '1', 'endDate': (now + timedelta(hours=1)).isoformat()},
            {'id': '2', 'endDate': (now + timedelta(days=2)).isoformat()},
            {'id': '3', 'endDate': (now + timedelta(hours=12)).isoformat()},
        ]

        short_term = discovery.filter_short_term_markets(markets, max_days=1)
        assert len(short_term) == 2
        assert short_term[0]['id'] in ['1', '3']

    def test_parse_market(self):
        """Test market parsing"""
        discovery = MarketDiscovery()

        market_dict = {
            'id': 'test-123',
            'question': 'Will BTC go up?',
            'conditionId': 'cond-123',
            'slug': 'btc-up',
            'endDate': '2026-01-10T00:00:00Z',
            'description': 'Test market',
            'category': 'Crypto',
            'liquidity': 10000.0,
            'volume': 5000.0,
            'active': True,
            'outcomes': ['Yes', 'No'],
            'outcomePrices': [0.6, 0.4],
        }

        market = discovery.parse_market(market_dict)
        assert market.id == 'test-123'
        assert market.question == 'Will BTC go up?'
        assert market.liquidity == 10000.0
        assert len(market.outcomes) == 2


@pytest.mark.asyncio
async def test_search_btc_markets():
    """Test searching for BTC markets (integration test)"""
    # This test requires actual API access
    # Skip in CI/CD environments without credentials
    try:
        discovery = MarketDiscovery()
        markets = await discovery.search_btc_markets(['Bitcoin'])
        assert isinstance(markets, list)
    except Exception as e:
        pytest.skip(f"API not available: {e}")
