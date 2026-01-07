"""Market discovery module for finding BTC prediction markets"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Market:
    """Represents a Polymarket prediction market"""
    id: str
    question: str
    condition_id: str
    slug: str
    end_date: datetime
    description: str
    category: str
    liquidity: float
    volume: float
    active: bool
    outcomes: List[str]
    outcome_prices: List[float]


class MarketDiscovery:
    """Discovers and filters BTC-related prediction markets"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.gamma_client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Polymarket Gamma client"""
        try:
            from polymarket_apis import PolymarketGammaClient
            self.gamma_client = PolymarketGammaClient()
            self.logger.info("Gamma client initialized successfully")
        except ImportError:
            self.logger.error("polymarket-apis not installed. Run: pip install polymarket-apis")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize Gamma client: {e}")
            raise

    async def search_btc_markets(self, keywords: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for BTC-related markets

        Args:
            keywords: List of keywords to search for (default: Bitcoin, BTC related terms)

        Returns:
            List of market dictionaries
        """
        if keywords is None:
            keywords = ["Bitcoin", "BTC", "bitcoin", "btc"]

        all_markets = []

        for keyword in keywords:
            try:
                self.logger.info(f"Searching for markets with keyword: {keyword}")
                results = self.gamma_client.search(keyword)

                if results:
                    self.logger.info(f"Found {len(results)} markets for '{keyword}'")
                    all_markets.extend(results)
                else:
                    self.logger.warning(f"No markets found for keyword: {keyword}")

            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {e}")

        # Remove duplicates based on market ID
        unique_markets = {market.get('id'): market for market in all_markets}
        return list(unique_markets.values())

    def filter_active_markets(self, markets: List[Dict]) -> List[Dict]:
        """Filter for active markets only"""
        active = [m for m in markets if m.get('active', False)]
        self.logger.info(f"Filtered to {len(active)} active markets out of {len(markets)}")
        return active

    def filter_short_term_markets(self, markets: List[Dict], max_days: int = 1) -> List[Dict]:
        """
        Filter for short-term markets (e.g., 15-minute intervals)

        Args:
            markets: List of market dictionaries
            max_days: Maximum number of days until market ends

        Returns:
            Filtered list of markets
        """
        from datetime import datetime, timedelta

        now = datetime.now()
        cutoff = now + timedelta(days=max_days)

        short_term = []
        for market in markets:
            end_date_str = market.get('endDate')
            if end_date_str:
                try:
                    # Parse ISO format date
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                    if end_date <= cutoff:
                        short_term.append(market)
                except Exception as e:
                    self.logger.debug(f"Could not parse date for market {market.get('id')}: {e}")

        self.logger.info(f"Found {len(short_term)} markets ending within {max_days} day(s)")
        return short_term

    def get_market_details(self, market_id: str) -> Optional[Dict]:
        """Get detailed information about a specific market"""
        try:
            market = self.gamma_client.get_market(market_id)
            return market
        except Exception as e:
            self.logger.error(f"Error fetching market {market_id}: {e}")
            return None

    def parse_market(self, market_dict: Dict) -> Market:
        """Parse raw market dictionary into Market dataclass"""
        try:
            return Market(
                id=market_dict.get('id', ''),
                question=market_dict.get('question', ''),
                condition_id=market_dict.get('conditionId', ''),
                slug=market_dict.get('slug', ''),
                end_date=datetime.fromisoformat(
                    market_dict.get('endDate', '').replace('Z', '+00:00')
                ),
                description=market_dict.get('description', ''),
                category=market_dict.get('category', ''),
                liquidity=float(market_dict.get('liquidity', 0)),
                volume=float(market_dict.get('volume', 0)),
                active=market_dict.get('active', False),
                outcomes=market_dict.get('outcomes', []),
                outcome_prices=market_dict.get('outcomePrices', []),
            )
        except Exception as e:
            self.logger.error(f"Error parsing market: {e}")
            raise

    async def find_btc_15m_markets(self) -> List[Dict]:
        """
        Find BTC markets with 15-minute resolution

        Returns:
            List of relevant BTC 15-minute markets
        """
        self.logger.info("Searching for BTC 15-minute markets...")

        # Search for BTC markets with specific keywords
        keywords = ["Bitcoin 15", "BTC 15", "Bitcoin will", "BTC next"]
        all_markets = await self.search_btc_markets(keywords)

        # Filter for active markets
        active_markets = self.filter_active_markets(all_markets)

        # Filter for short-term markets
        short_term = self.filter_short_term_markets(active_markets, max_days=1)

        # Additional filtering for 15-minute specific markets
        fifteen_min_markets = []
        for market in short_term:
            question = market.get('question', '').lower()
            if any(term in question for term in ['15 min', '15min', '15-min', 'fifteen minute']):
                fifteen_min_markets.append(market)

        self.logger.info(f"Found {len(fifteen_min_markets)} BTC 15-minute markets")
        return fifteen_min_markets

    def display_market_summary(self, markets: List[Dict]):
        """Display a summary of found markets"""
        if not markets:
            self.logger.warning("No markets to display")
            return

        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"Found {len(markets)} BTC Markets")
        self.logger.info(f"{'='*80}\n")

        for i, market in enumerate(markets, 1):
            self.logger.info(f"{i}. {market.get('question')}")
            self.logger.info(f"   ID: {market.get('id')}")
            self.logger.info(f"   Condition ID: {market.get('conditionId')}")
            self.logger.info(f"   Category: {market.get('category')}")
            self.logger.info(f"   Liquidity: ${market.get('liquidity', 0):,.2f}")
            self.logger.info(f"   Volume: ${market.get('volume', 0):,.2f}")
            self.logger.info(f"   End Date: {market.get('endDate')}")
            self.logger.info(f"   Active: {market.get('active')}")
            self.logger.info(f"   URL: https://polymarket.com/event/{market.get('slug')}\n")
