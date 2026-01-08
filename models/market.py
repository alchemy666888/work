"""Market data models using Pydantic"""

import json
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


def parse_json_string_list(value: Any) -> list:
    """Parse a JSON string list or return as-is if already a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    return []


class Market(BaseModel):
    """Represents a Polymarket prediction market"""

    id: str = Field(description="Unique market identifier")
    slug: str = Field(description="URL-friendly market slug")
    question: str = Field(description="Market question")
    active: bool = Field(default=True, description="Whether market is active")
    closed: bool = Field(default=False, description="Whether market is closed")
    close_date: Optional[datetime] = Field(
        default=None, alias="endDate", description="Market close/end date"
    )
    clob_token_ids: list[str] = Field(
        default_factory=list,
        alias="clobTokenIds",
        description="CLOB token IDs for outcomes",
    )
    outcomes: list[str] = Field(
        default_factory=list, description="Possible outcomes (e.g., ['Up', 'Down'])"
    )
    outcome_prices: list[str] = Field(
        default_factory=list,
        alias="outcomePrices",
        description="Current prices for each outcome",
    )
    description: Optional[str] = Field(default=None, description="Market description")
    category: Optional[str] = Field(default=None, description="Market category")
    condition_id: Optional[str] = Field(
        default=None, alias="conditionId", description="Condition ID"
    )
    volume: Optional[float] = Field(default=0.0, description="Total trading volume")
    liquidity: Optional[float] = Field(default=0.0, description="Market liquidity")

    # Validators to parse JSON string lists from API
    @field_validator("clob_token_ids", "outcomes", "outcome_prices", mode="before")
    @classmethod
    def parse_json_list(cls, value: Any) -> list:
        """Parse JSON string lists from API response."""
        return parse_json_string_list(value)

    class Config:
        populate_by_name = True
        extra = "allow"  # Allow extra fields from API

    def get_up_token_id(self) -> Optional[str]:
        """Get the token ID for the UP outcome"""
        if len(self.clob_token_ids) >= 1:
            return self.clob_token_ids[0]
        return None

    def get_down_token_id(self) -> Optional[str]:
        """Get the token ID for the DOWN outcome"""
        if len(self.clob_token_ids) >= 2:
            return self.clob_token_ids[1]
        return None

    def get_up_price(self) -> Optional[float]:
        """Get the current UP price"""
        if len(self.outcome_prices) >= 1:
            try:
                return float(self.outcome_prices[0])
            except (ValueError, TypeError):
                return None
        return None

    def get_down_price(self) -> Optional[float]:
        """Get the current DOWN price"""
        if len(self.outcome_prices) >= 2:
            try:
                return float(self.outcome_prices[1])
            except (ValueError, TypeError):
                return None
        return None

    def is_btc_15m_market(self) -> bool:
        """Check if this is a BTC 15-minute market"""
        lower_question = self.question.lower()
        lower_slug = self.slug.lower()

        btc_terms = ["bitcoin", "btc"]
        time_terms = ["15 min", "15min", "15-min", "fifteen minute"]

        has_btc = any(term in lower_question or term in lower_slug for term in btc_terms)
        has_15m = any(term in lower_question or term in lower_slug for term in time_terms)

        return has_btc and has_15m


class MarketSearchResult(BaseModel):
    """Search result from Gamma API"""

    markets: list[Market] = Field(default_factory=list)
    total: Optional[int] = Field(default=None)

    class Config:
        extra = "allow"
