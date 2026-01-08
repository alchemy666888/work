"""Configuration management with pydantic-settings"""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables"""

    # API Settings
    gamma_api_base: str = "https://gamma-api.polymarket.com"
    ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    # Connection Settings
    ping_interval: int = 10
    reconnect_base_delay: int = 1
    max_reconnect_delay: int = 30

    # Market Settings
    base_slug: str = "btc-updown-15m"

    # Alert Thresholds
    price_swing_threshold: float = 5.0  # %
    price_swing_window: int = 30  # seconds
    volume_spike_multiplier: float = 2.0
    market_closing_alert: int = 120  # seconds

    # Display Settings
    use_rich_output: bool = True
    refresh_rate: float = 1.0  # Hz

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
config = Config()
