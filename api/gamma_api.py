"""Gamma API client for Polymarket market data"""

import asyncio
from typing import Optional
import aiohttp

from models.market import Market, MarketSearchResult
from utils.logger import logger


class GammaAPIClient:
    """
    Async API client for Polymarket Gamma API.

    Usage:
        async with GammaAPIClient() as client:
            market = await client.get_market_by_slug("btc-updown-15m-1234567890")
    """

    def __init__(self, base_url: str = "https://gamma-api.polymarket.com"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={"Accept": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            )

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        retries: int = 3,
    ) -> Optional[dict]:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            retries: Number of retries

        Returns:
            Response data or None
        """
        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"

        for attempt in range(retries):
            try:
                async with self.session.request(method, url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.debug(f"Resource not found: {url}")
                        return None
                    else:
                        logger.warning(
                            f"API request failed: {response.status} - {url}"
                        )

            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{retries})")
            except aiohttp.ClientError as e:
                logger.warning(f"Client error (attempt {attempt + 1}/{retries}): {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    async def get_market_by_slug(self, slug: str) -> Optional[Market]:
        """
        Fetch market data by slug.

        Args:
            slug: Market slug (e.g., 'btc-updown-15m-1234567890')

        Returns:
            Market object or None if not found
        """
        # First try the markets endpoint with slug parameter
        data = await self._request("GET", "/markets", params={"slug": slug})

        if data and isinstance(data, list) and len(data) > 0:
            try:
                return Market(**data[0])
            except Exception as e:
                logger.error(f"Error parsing market data: {e}")
                return None

        # Fallback: try direct slug lookup
        data = await self._request("GET", f"/markets/{slug}")
        if data:
            try:
                return Market(**data)
            except Exception as e:
                logger.error(f"Error parsing market data: {e}")

        return None

    async def get_market_by_id(self, market_id: str) -> Optional[Market]:
        """
        Fetch market data by ID.

        Args:
            market_id: Market ID

        Returns:
            Market object or None if not found
        """
        data = await self._request("GET", f"/markets/{market_id}")

        if data:
            try:
                return Market(**data)
            except Exception as e:
                logger.error(f"Error parsing market data: {e}")

        return None

    async def get_active_markets(self, limit: int = 50, offset: int = 0) -> list[Market]:
        """
        Fetch active markets.

        Args:
            limit: Maximum number of markets to fetch
            offset: Pagination offset

        Returns:
            List of Market objects
        """
        data = await self._request(
            "GET",
            "/markets",
            params={"limit": limit, "offset": offset, "active": "true"},
        )

        if data and isinstance(data, list):
            markets = []
            for item in data:
                try:
                    markets.append(Market(**item))
                except Exception as e:
                    logger.debug(f"Skipping invalid market: {e}")
            return markets

        return []

    async def search_markets(self, query: str) -> list[Market]:
        """
        Search markets by keyword.

        Args:
            query: Search query string

        Returns:
            List of matching Market objects
        """
        # Try the search endpoint
        data = await self._request("GET", "/markets", params={"q": query})

        if data and isinstance(data, list):
            markets = []
            for item in data:
                try:
                    markets.append(Market(**item))
                except Exception as e:
                    logger.debug(f"Skipping invalid market: {e}")
            return markets

        return []

    async def find_btc_markets(self) -> list[Market]:
        """
        Find active BTC-related markets.

        Returns:
            List of BTC Market objects
        """
        # Search with multiple keywords
        keywords = ["Bitcoin", "BTC"]
        all_markets = []
        seen_ids = set()

        for keyword in keywords:
            markets = await self.search_markets(keyword)
            for market in markets:
                if market.id not in seen_ids:
                    seen_ids.add(market.id)
                    all_markets.append(market)

        # Filter for active markets
        active_markets = [m for m in all_markets if m.active and not m.closed]

        logger.info(f"Found {len(active_markets)} active BTC markets")
        return active_markets

    async def find_btc_15m_markets(self) -> list[Market]:
        """
        Find active BTC 15-minute markets.

        Returns:
            List of BTC 15m Market objects
        """
        # Get all BTC markets
        btc_markets = await self.find_btc_markets()

        # Filter for 15-minute markets
        btc_15m_markets = [m for m in btc_markets if m.is_btc_15m_market()]

        logger.info(f"Found {len(btc_15m_markets)} BTC 15-minute markets")
        return btc_15m_markets

    async def get_markets_by_slugs(self, slugs: list[str]) -> dict[str, Market]:
        """
        Fetch multiple markets by their slugs concurrently.

        Args:
            slugs: List of market slugs

        Returns:
            Dictionary mapping slug to Market object
        """
        tasks = [self.get_market_by_slug(slug) for slug in slugs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        markets = {}
        for slug, result in zip(slugs, results):
            if isinstance(result, Market):
                markets[slug] = result
            elif isinstance(result, Exception):
                logger.error(f"Error fetching market {slug}: {result}")

        return markets

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
