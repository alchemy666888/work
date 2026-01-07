"""Alert system for market events"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from src.utils.logger import setup_logger
from src.utils.config import config

logger = setup_logger(__name__)


@dataclass
class Alert:
    """Represents a market alert"""
    timestamp: datetime
    alert_type: str  # 'price_change', 'volume_spike', 'new_market', etc.
    market_id: str
    market_question: str
    message: str
    severity: str  # 'info', 'warning', 'critical'
    data: Dict


class AlertSystem:
    """Monitors markets and triggers alerts based on conditions"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.alert_history: List[Alert] = []
        self.previous_prices: Dict[str, float] = {}
        self.previous_volumes: Dict[str, float] = {}
        self.price_change_threshold = config.alerts.price_change_threshold
        self.volume_spike_threshold = config.alerts.volume_spike_threshold

    async def check_price_change(self, market_id: str, question: str, current_price: float) -> Optional[Alert]:
        """
        Check if price has changed significantly

        Args:
            market_id: Market identifier
            question: Market question
            current_price: Current market price/odds (as percentage)

        Returns:
            Alert if threshold exceeded, None otherwise
        """
        if market_id not in self.previous_prices:
            self.previous_prices[market_id] = current_price
            return None

        previous_price = self.previous_prices[market_id]
        price_change = abs(current_price - previous_price)
        change_percentage = (price_change / previous_price * 100) if previous_price > 0 else 0

        if change_percentage >= self.price_change_threshold:
            direction = "increased" if current_price > previous_price else "decreased"
            severity = "warning" if change_percentage < 10 else "critical"

            alert = Alert(
                timestamp=datetime.now(),
                alert_type="price_change",
                market_id=market_id,
                market_question=question,
                message=f"Price {direction} by {change_percentage:.2f}% "
                        f"(from {previous_price:.1f}% to {current_price:.1f}%)",
                severity=severity,
                data={
                    "previous_price": previous_price,
                    "current_price": current_price,
                    "change_percentage": change_percentage,
                    "direction": direction,
                }
            )

            self.previous_prices[market_id] = current_price
            await self._trigger_alert(alert)
            return alert

        self.previous_prices[market_id] = current_price
        return None

    async def check_volume_spike(self, market_id: str, question: str, current_volume: float) -> Optional[Alert]:
        """
        Check if volume has spiked significantly

        Args:
            market_id: Market identifier
            question: Market question
            current_volume: Current trading volume in USDC

        Returns:
            Alert if spike detected, None otherwise
        """
        if market_id not in self.previous_volumes:
            self.previous_volumes[market_id] = current_volume
            return None

        previous_volume = self.previous_volumes[market_id]
        volume_increase = current_volume - previous_volume

        if volume_increase >= self.volume_spike_threshold:
            increase_percentage = (volume_increase / previous_volume * 100) if previous_volume > 0 else 0

            alert = Alert(
                timestamp=datetime.now(),
                alert_type="volume_spike",
                market_id=market_id,
                market_question=question,
                message=f"Volume spiked by ${volume_increase:,.0f} "
                        f"({increase_percentage:.1f}% increase)",
                severity="warning",
                data={
                    "previous_volume": previous_volume,
                    "current_volume": current_volume,
                    "volume_increase": volume_increase,
                    "increase_percentage": increase_percentage,
                }
            )

            self.previous_volumes[market_id] = current_volume
            await self._trigger_alert(alert)
            return alert

        self.previous_volumes[market_id] = current_volume
        return None

    async def check_new_market(self, market: Dict) -> Alert:
        """Create alert for a new market discovered"""
        alert = Alert(
            timestamp=datetime.now(),
            alert_type="new_market",
            market_id=market.get('id', ''),
            market_question=market.get('question', ''),
            message=f"New BTC market discovered: {market.get('question')}",
            severity="info",
            data=market
        )

        await self._trigger_alert(alert)
        return alert

    async def _trigger_alert(self, alert: Alert):
        """
        Trigger an alert through all configured channels

        Args:
            alert: Alert object to send
        """
        # Store in history
        self.alert_history.append(alert)

        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        # Log the alert
        log_message = f"[{alert.severity.upper()}] {alert.alert_type}: {alert.message}"

        if alert.severity == "critical":
            self.logger.critical(log_message)
        elif alert.severity == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Send to notification channels
        await self._send_console_notification(alert)

        if config.alerts.telegram_bot_token:
            await self._send_telegram_notification(alert)

        if config.alerts.discord_webhook_url:
            await self._send_discord_notification(alert)

    async def _send_console_notification(self, alert: Alert):
        """Send alert to console (already logged above)"""
        pass  # Logging handles console output

    async def _send_telegram_notification(self, alert: Alert):
        """Send alert to Telegram"""
        try:
            # Implementation for Telegram notifications
            # Would require additional library like python-telegram-bot
            self.logger.debug(f"Would send Telegram notification: {alert.message}")
            # TODO: Implement actual Telegram sending
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")

    async def _send_discord_notification(self, alert: Alert):
        """Send alert to Discord"""
        try:
            import aiohttp

            webhook_url = config.alerts.discord_webhook_url
            if not webhook_url:
                return

            # Color based on severity
            colors = {
                "info": 0x3498db,      # Blue
                "warning": 0xf39c12,   # Orange
                "critical": 0xe74c3c,  # Red
            }

            embed = {
                "title": f"{alert.alert_type.replace('_', ' ').title()}",
                "description": alert.message,
                "color": colors.get(alert.severity, 0x95a5a6),
                "fields": [
                    {"name": "Market", "value": alert.market_question[:256], "inline": False},
                    {"name": "Severity", "value": alert.severity.upper(), "inline": True},
                    {"name": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                ],
                "footer": {"text": f"Market ID: {alert.market_id}"}
            }

            payload = {"embeds": [embed]}

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 204:
                        self.logger.debug("Discord notification sent successfully")
                    else:
                        self.logger.error(f"Discord notification failed: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {e}")

    def get_recent_alerts(self, limit: int = 10) -> List[Alert]:
        """Get most recent alerts"""
        return self.alert_history[-limit:]

    def get_alerts_by_type(self, alert_type: str) -> List[Alert]:
        """Get all alerts of a specific type"""
        return [alert for alert in self.alert_history if alert.alert_type == alert_type]

    def get_critical_alerts(self) -> List[Alert]:
        """Get all critical alerts"""
        return [alert for alert in self.alert_history if alert.severity == "critical"]
