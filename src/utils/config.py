"""Configuration management for Polymarket Monitor"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class PolymarketConfig:
    """Polymarket API configuration"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    wallet_address: Optional[str] = None


@dataclass
class AlertConfig:
    """Alert configuration"""
    price_change_threshold: float = 5.0  # Percentage
    volume_spike_threshold: float = 10000.0  # USDC
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook_url: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    update_interval: int = 5  # Seconds
    enable_terminal_ui: bool = True
    log_level: str = "INFO"


class Config:
    """Main configuration class"""

    def __init__(self):
        self.polymarket = PolymarketConfig(
            api_key=os.getenv("POLYMARKET_API_KEY"),
            api_secret=os.getenv("POLYMARKET_API_SECRET"),
            passphrase=os.getenv("POLYMARKET_PASSPHRASE"),
            wallet_address=os.getenv("POLYMARKET_WALLET_ADDRESS"),
        )

        self.alerts = AlertConfig(
            price_change_threshold=float(os.getenv("ALERT_PRICE_CHANGE_THRESHOLD", "5")),
            volume_spike_threshold=float(os.getenv("ALERT_VOLUME_SPIKE_THRESHOLD", "10000")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        )

        self.monitoring = MonitoringConfig(
            update_interval=int(os.getenv("UPDATE_INTERVAL", "5")),
            enable_terminal_ui=os.getenv("ENABLE_TERMINAL_UI", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def has_api_credentials(self) -> bool:
        """Check if API credentials are configured"""
        return all([
            self.polymarket.api_key,
            self.polymarket.api_secret,
            self.polymarket.passphrase,
        ])


# Global configuration instance
config = Config()
