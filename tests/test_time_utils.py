"""Tests for time utility functions"""

import pytest
from datetime import datetime, timezone, timedelta

from utils.time_utils import (
    get_current_and_next_15min_timestamps,
    generate_current_and_next_slugs,
    get_time_remaining,
    parse_iso_datetime,
    get_current_interval_info,
)


class TestTimestampCalculations:
    """Tests for timestamp calculation functions"""

    def test_get_current_and_next_15min_timestamps(self):
        """Test that timestamps are 15 minutes apart"""
        result = get_current_and_next_15min_timestamps()

        assert "current" in result
        assert "next" in result

        # Should be exactly 15 minutes (900 seconds) apart
        assert result["next"] - result["current"] == 900

        # Current timestamp should be in the past or present
        assert result["current"] <= int(datetime.now(timezone.utc).timestamp())

    def test_timestamps_aligned_to_15min(self):
        """Test that timestamps are aligned to 15-minute boundaries"""
        result = get_current_and_next_15min_timestamps()

        # Convert to datetime and check alignment
        current_dt = datetime.fromtimestamp(result["current"], tz=timezone.utc)

        # Minutes should be 0, 15, 30, or 45
        assert current_dt.minute % 15 == 0
        assert current_dt.second == 0
        assert current_dt.microsecond == 0


class TestSlugGeneration:
    """Tests for slug generation"""

    def test_generate_current_and_next_slugs(self):
        """Test slug generation with base slug"""
        base_slug = "btc-updown-15m"
        result = generate_current_and_next_slugs(base_slug)

        assert "current" in result
        assert "next" in result

        # Slugs should start with base slug
        assert result["current"].startswith(base_slug)
        assert result["next"].startswith(base_slug)

        # Slugs should contain timestamps
        timestamps = get_current_and_next_15min_timestamps()
        assert str(timestamps["current"]) in result["current"]
        assert str(timestamps["next"]) in result["next"]


class TestTimeRemaining:
    """Tests for time remaining calculation"""

    def test_time_remaining_future(self):
        """Test time remaining for future date"""
        future = datetime.now(timezone.utc) + timedelta(minutes=5, seconds=30)
        result = get_time_remaining(future)

        assert "m" in result
        assert "s" in result

    def test_time_remaining_past(self):
        """Test time remaining for past date"""
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = get_time_remaining(past)

        assert result == "Ended"

    def test_time_remaining_hours(self):
        """Test time remaining with hours"""
        future = datetime.now(timezone.utc) + timedelta(hours=2, minutes=30)
        result = get_time_remaining(future)

        assert "h" in result
        assert "m" in result

    def test_time_remaining_days(self):
        """Test time remaining with days"""
        future = datetime.now(timezone.utc) + timedelta(days=2, hours=5)
        result = get_time_remaining(future)

        assert "d" in result
        assert "h" in result


class TestISODatetimeParsing:
    """Tests for ISO datetime parsing"""

    def test_parse_iso_with_z_suffix(self):
        """Test parsing ISO string with Z suffix"""
        result = parse_iso_datetime("2024-01-15T10:30:00Z")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_iso_with_offset(self):
        """Test parsing ISO string with timezone offset"""
        result = parse_iso_datetime("2024-01-15T10:30:00+00:00")

        assert result is not None
        assert result.year == 2024

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = parse_iso_datetime("")
        assert result is None

    def test_parse_invalid_string(self):
        """Test parsing invalid string"""
        result = parse_iso_datetime("not-a-date")
        assert result is None


class TestIntervalInfo:
    """Tests for interval info function"""

    def test_get_current_interval_info(self):
        """Test getting current interval info"""
        result = get_current_interval_info()

        assert "current_timestamp" in result
        assert "next_timestamp" in result
        assert "elapsed_seconds" in result
        assert "remaining_seconds" in result
        assert "progress_percent" in result

        # Elapsed + remaining should equal 900 seconds (15 minutes)
        assert result["elapsed_seconds"] + result["remaining_seconds"] == 900

        # Progress should be 0-100
        assert 0 <= result["progress_percent"] <= 100
