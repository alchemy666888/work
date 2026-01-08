"""Rich console formatting utilities"""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


def create_market_table(market_states: dict) -> Table:
    """
    Create formatted table showing market data.

    Args:
        market_states: Dictionary mapping asset_id to MarketState objects

    Returns:
        Rich Table object
    """
    table = Table(
        title="BTC Up/Down 15m Markets",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Market", style="cyan", no_wrap=False, width=30)
    table.add_column("Outcome", style="magenta", width=10)
    table.add_column("Price", justify="right", width=10)
    table.add_column("Prob %", justify="right", width=10)
    table.add_column("Volume", justify="right", width=12)
    table.add_column("Change %", justify="right", width=10)
    table.add_column("Time Left", justify="right", width=12)

    if not market_states:
        table.add_row("No markets", "-", "-", "-", "-", "-", "-")
        return table

    for asset_id, state in market_states.items():
        # Get display values
        market_name = state.market.question[:28] if state.market else "Unknown"
        outcome = state.outcome if state.outcome else "-"
        price = format_price(state.current_price)
        probability = format_probability(state.current_price)
        volume = format_volume(state.total_volume)
        change = format_change(state.get_price_change_pct())

        # Get time remaining
        if state.market and state.market.close_date:
            from .time_utils import get_time_remaining
            time_left = get_time_remaining(state.market.close_date)
        else:
            time_left = "-"

        # Style based on outcome
        if outcome.upper() == "UP":
            outcome_style = "bold green"
        elif outcome.upper() == "DOWN":
            outcome_style = "bold red"
        else:
            outcome_style = "white"

        table.add_row(
            market_name,
            Text(outcome, style=outcome_style),
            price,
            probability,
            volume,
            change,
            time_left,
        )

    return table


def format_price(price: Optional[float]) -> str:
    """
    Format price value.

    Args:
        price: Price value (0-1 or 0-100 scale)

    Returns:
        Formatted price string
    """
    if price is None:
        return "-"

    # Normalize to 0-100 scale if needed
    if price <= 1:
        price = price * 100

    return f"${price:.2f}"


def format_probability(price: Optional[float]) -> str:
    """
    Format price as probability percentage.

    Args:
        price: Price value (typically 0-1 or 0-100)

    Returns:
        Formatted probability string
    """
    if price is None:
        return "-"

    # Normalize to 0-100 scale if needed
    if price <= 1:
        prob = price * 100
    else:
        prob = price

    return f"{prob:.1f}%"


def format_volume(volume: Optional[float]) -> str:
    """
    Format volume with appropriate units.

    Args:
        volume: Volume in USDC

    Returns:
        Formatted volume string
    """
    if volume is None:
        return "-"

    if volume >= 1_000_000:
        return f"${volume / 1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"${volume / 1_000:.1f}K"
    else:
        return f"${volume:.0f}"


def format_change(change_pct: Optional[float]) -> str:
    """
    Format price change percentage with color indicator.

    Args:
        change_pct: Percentage change

    Returns:
        Formatted change string with color
    """
    if change_pct is None:
        return "-"

    if change_pct > 0:
        return f"[green]+{change_pct:.2f}%[/green]"
    elif change_pct < 0:
        return f"[red]{change_pct:.2f}%[/red]"
    else:
        return "0.00%"


def format_time_remaining(seconds: int) -> str:
    """
    Format seconds as MM:SS or HH:MM:SS.

    Args:
        seconds: Total seconds remaining

    Returns:
        Formatted time string
    """
    if seconds < 0:
        return "Ended"

    if seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"


def create_status_panel(connected: bool, markets_count: int, alerts_count: int) -> Panel:
    """
    Create a status panel showing connection and monitoring info.

    Args:
        connected: WebSocket connection status
        markets_count: Number of monitored markets
        alerts_count: Number of recent alerts

    Returns:
        Rich Panel object
    """
    status_icon = "[green]Connected[/green]" if connected else "[red]Disconnected[/red]"

    content = Text()
    content.append(f"Status: {status_icon}\n")
    content.append(f"Markets: {markets_count}\n", style="cyan")
    content.append(f"Alerts: {alerts_count}", style="yellow")

    return Panel(
        content,
        title="Monitor Status",
        border_style="blue",
    )


def create_alert_panel(alerts: list) -> Panel:
    """
    Create a panel showing recent alerts.

    Args:
        alerts: List of Alert objects

    Returns:
        Rich Panel object
    """
    if not alerts:
        content = Text("No alerts", style="dim")
    else:
        content = Text()
        for alert in alerts[-5:]:  # Show last 5 alerts
            severity_color = {
                "info": "blue",
                "warning": "yellow",
                "critical": "red",
            }.get(alert.severity, "white")

            timestamp = alert.timestamp.strftime("%H:%M:%S")
            content.append(f"[{timestamp}] ", style="dim")
            content.append(f"{alert.message}\n", style=severity_color)

    return Panel(
        content,
        title="Recent Alerts",
        border_style="yellow",
    )


def print_startup_banner():
    """Print application startup banner."""
    banner = """
[bold cyan]========================================[/bold cyan]
[bold cyan]  Polymarket BTC Up/Down 15m Monitor  [/bold cyan]
[bold cyan]========================================[/bold cyan]
    """
    console.print(banner)


def print_market_update(
    market_name: str,
    outcome: str,
    price: float,
    change: Optional[float] = None,
):
    """
    Print a single market update line.

    Args:
        market_name: Name of the market
        outcome: UP or DOWN
        price: Current price
        change: Optional price change percentage
    """
    outcome_style = "green" if outcome.upper() == "UP" else "red"
    change_str = format_change(change) if change is not None else ""

    console.print(
        f"[cyan]{market_name}[/cyan] | "
        f"[{outcome_style}]{outcome}[/{outcome_style}]: "
        f"{format_probability(price)} {change_str}"
    )
