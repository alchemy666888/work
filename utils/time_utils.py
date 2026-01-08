"""Time utility functions for timestamp calculations and slug generation"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def get_current_and_next_15min_timestamps() -> dict[str, int]:
    """
    Calculate current and next 15-minute interval timestamps.

    Returns:
        Dictionary with 'current' and 'next' Unix timestamps (seconds)
    """
    now = datetime.now(timezone.utc)

    # Round down to nearest 15 minutes
    current_minute = now.minute
    rounded_minute = (current_minute // 15) * 15

    current_interval = now.replace(
        minute=rounded_minute, second=0, microsecond=0
    )
    next_interval = current_interval + timedelta(minutes=15)

    return {
        "current": int(current_interval.timestamp()),
        "next": int(next_interval.timestamp()),
    }


def generate_current_and_next_slugs(base_slug: str) -> dict[str, str]:
    """
    Generate slugs for current and next events based on timestamps.

    Args:
        base_slug: Base slug pattern (e.g., 'btc-updown-15m')

    Returns:
        Dictionary with 'current' and 'next' slugs
    """
    timestamps = get_current_and_next_15min_timestamps()

    return {
        "current": f"{base_slug}-{timestamps['current']}",
        "next": f"{base_slug}-{timestamps['next']}",
    }


def get_time_remaining(close_date: datetime) -> str:
    """
    Calculate human-readable time remaining until close date.

    Args:
        close_date: The market close datetime

    Returns:
        Human-readable time remaining string (e.g., '5m 30s', '1h 15m')
    """
    now = datetime.now(timezone.utc)

    # Ensure close_date is timezone-aware
    if close_date.tzinfo is None:
        close_date = close_date.replace(tzinfo=timezone.utc)

    remaining = close_date - now

    if remaining.total_seconds() < 0:
        return "Ended"

    total_seconds = int(remaining.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        return f"{days}d {hours}h"


def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse ISO format datetime string to datetime object.

    Args:
        date_str: ISO format datetime string

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_str:
        return None

    try:
        # Handle 'Z' suffix for UTC
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def get_current_interval_info() -> dict[str, any]:
    """
    Get comprehensive information about the current 15-minute interval.

    Returns:
        Dictionary with interval information
    """
    now = datetime.now(timezone.utc)
    timestamps = get_current_and_next_15min_timestamps()

    current_start = datetime.fromtimestamp(timestamps["current"], tz=timezone.utc)
    current_end = datetime.fromtimestamp(timestamps["next"], tz=timezone.utc)

    elapsed = (now - current_start).total_seconds()
    remaining = (current_end - now).total_seconds()

    return {
        "current_timestamp": timestamps["current"],
        "next_timestamp": timestamps["next"],
        "current_start": current_start.isoformat(),
        "current_end": current_end.isoformat(),
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "progress_percent": round((elapsed / 900) * 100, 1),  # 900 = 15 minutes
    }
