"""Terminal-based dashboard for market monitoring"""

import asyncio
from typing import Dict, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TerminalDashboard:
    """Rich terminal UI for monitoring BTC markets"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.console = Console()
        self.markets_data = {}
        self.alerts = []
        self.start_time = datetime.now()

    def create_header(self) -> Panel:
        """Create dashboard header"""
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

        header_text = Text()
        header_text.append("🚀 Polymarket BTC Monitor", style="bold cyan")
        header_text.append(f"\n⏱️  Uptime: {uptime_str}", style="dim")
        header_text.append(f"  |  📊 Monitoring {len(self.markets_data)} markets", style="dim")

        return Panel(header_text, style="blue")

    def create_markets_table(self) -> Table:
        """Create table showing current market data"""
        table = Table(title="BTC Markets - Live Odds", show_header=True, header_style="bold magenta")

        table.add_column("Market", style="cyan", no_wrap=False, width=40)
        table.add_column("UP Odds", justify="right", style="green")
        table.add_column("DOWN Odds", justify="right", style="red")
        table.add_column("Volume", justify="right", style="yellow")
        table.add_column("Liquidity", justify="right", style="blue")
        table.add_column("Ends In", justify="right", style="dim")

        if not self.markets_data:
            table.add_row("No markets being monitored", "-", "-", "-", "-", "-")
            return table

        for market_id, data in self.markets_data.items():
            question = data.get('question', 'Unknown')[:40]
            up_odds = data.get('up_odds', 0)
            down_odds = data.get('down_odds', 0)
            volume = data.get('volume', 0)
            liquidity = data.get('liquidity', 0)
            end_time = data.get('end_time', '')

            # Color code based on odds
            up_style = "bold green" if up_odds > 50 else "green"
            down_style = "bold red" if down_odds > 50 else "red"

            table.add_row(
                question,
                f"{up_odds:.1f}%",
                f"{down_odds:.1f}%",
                f"${volume:,.0f}",
                f"${liquidity:,.0f}",
                end_time
            )

        return table

    def create_alerts_panel(self) -> Panel:
        """Create panel showing recent alerts"""
        if not self.alerts:
            alert_text = Text("No alerts yet", style="dim")
        else:
            alert_text = Text()
            # Show last 5 alerts
            for alert in self.alerts[-5:]:
                severity = alert.get('severity', 'info')
                message = alert.get('message', '')
                timestamp = alert.get('timestamp', datetime.now()).strftime("%H:%M:%S")

                # Color based on severity
                color = {
                    'info': 'blue',
                    'warning': 'yellow',
                    'critical': 'red'
                }.get(severity, 'white')

                alert_text.append(f"[{timestamp}] ", style="dim")
                alert_text.append(f"{message}\n", style=color)

        return Panel(alert_text, title="📢 Recent Alerts", border_style="yellow")

    def create_stats_panel(self) -> Panel:
        """Create panel showing statistics"""
        stats_text = Text()

        total_markets = len(self.markets_data)
        total_volume = sum(m.get('volume', 0) for m in self.markets_data.values())
        total_liquidity = sum(m.get('liquidity', 0) for m in self.markets_data.values())
        total_alerts = len(self.alerts)

        stats_text.append(f"Total Markets: {total_markets}\n", style="cyan")
        stats_text.append(f"Total Volume: ${total_volume:,.0f}\n", style="yellow")
        stats_text.append(f"Total Liquidity: ${total_liquidity:,.0f}\n", style="blue")
        stats_text.append(f"Total Alerts: {total_alerts}\n", style="magenta")

        return Panel(stats_text, title="📈 Statistics", border_style="green")

    def create_layout(self) -> Layout:
        """Create the main dashboard layout"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=8)
        )

        layout["body"].split_row(
            Layout(name="main", ratio=2),
            Layout(name="sidebar", ratio=1)
        )

        layout["footer"].split_row(
            Layout(name="alerts"),
        )

        # Fill layouts
        layout["header"].update(self.create_header())
        layout["main"].update(self.create_markets_table())
        layout["sidebar"].update(self.create_stats_panel())
        layout["footer"].update(self.create_alerts_panel())

        return layout

    def update_market_data(self, market_id: str, data: Dict):
        """Update data for a specific market"""
        self.markets_data[market_id] = data

    def add_alert(self, alert: Dict):
        """Add a new alert to the display"""
        self.alerts.append(alert)
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    async def run(self, update_callback=None):
        """
        Run the live dashboard

        Args:
            update_callback: Optional async function to call for data updates
        """
        try:
            with Live(self.create_layout(), console=self.console, refresh_per_second=1) as live:
                while True:
                    # Call update callback if provided
                    if update_callback:
                        await update_callback()

                    # Refresh the display
                    live.update(self.create_layout())

                    # Wait before next update
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Dashboard stopped by user")
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")


class SimpleTerminalDisplay:
    """Simple text-based display for systems without rich terminal support"""

    def __init__(self):
        self.logger = setup_logger(__name__)

    def display_market(self, market: Dict):
        """Display a single market"""
        print("\n" + "="*80)
        print(f"Market: {market.get('question')}")
        print(f"UP Odds: {market.get('up_odds', 0):.1f}%")
        print(f"DOWN Odds: {market.get('down_odds', 0):.1f}%")
        print(f"Volume: ${market.get('volume', 0):,.0f}")
        print(f"Liquidity: ${market.get('liquidity', 0):,.0f}")
        print(f"Ends: {market.get('end_time', 'Unknown')}")
        print("="*80)

    def display_alert(self, alert: Dict):
        """Display an alert"""
        severity = alert.get('severity', 'INFO').upper()
        message = alert.get('message', '')
        timestamp = alert.get('timestamp', datetime.now()).strftime("%H:%M:%S")

        prefix = {
            'CRITICAL': '🔴',
            'WARNING': '⚠️ ',
            'INFO': 'ℹ️ '
        }.get(severity, '  ')

        print(f"{prefix} [{timestamp}] {severity}: {message}")

    def display_summary(self, markets: List[Dict], alerts: List[Dict]):
        """Display a summary of all markets and alerts"""
        print("\n" + "="*80)
        print("POLYMARKET BTC MONITOR - SUMMARY")
        print("="*80)

        print(f"\n📊 Monitoring {len(markets)} markets")

        for i, market in enumerate(markets, 1):
            print(f"\n{i}. {market.get('question', 'Unknown')[:60]}")
            print(f"   UP: {market.get('up_odds', 0):.1f}% | DOWN: {market.get('down_odds', 0):.1f}%")
            print(f"   Volume: ${market.get('volume', 0):,.0f} | Liquidity: ${market.get('liquidity', 0):,.0f}")

        if alerts:
            print(f"\n📢 Recent Alerts ({len(alerts)}):")
            for alert in alerts[-5:]:
                self.display_alert(alert)

        print("\n" + "="*80)
