# Polymarket BTC Up/Down 15m Event Monitor - TODO (Python)

A Python websocket-based monitoring system for Polymarket's BTC price prediction markets with 15-minute intervals using Gamma API and WebSocket subscriptions.

---

## 🎯 Project Overview

Real-time monitoring system that:
- 🔄 Connects to Polymarket's Gamma API for market data
- 🔄 Connects to Polymarket's WebSocket (wss://ws-subscriptions-clob.polymarket.com)
- 🔄 Tracks current and next BTC 15m up/down markets
- 🔄 Subscribes to market updates via CLOB token IDs
- ⏳ Displays live odds, volume, and price movements
- ⏳ Alerts on significant market changes

---

## 📋 Phase 1: Python Environment Setup

### Initial Setup
- [ ] **Create project structure**
  ```
  polymarket-btc-monitor/
  ├── main.py
  ├── config.py
  ├── api/
  │   ├── __init__.py
  │   └── gamma_api.py
  ├── ws/
  │   ├── __init__.py
  │   └── websocket_client.py
  ├── models/
  │   ├── __init__.py
  │   ├── market.py
  │   └── market_state.py
  ├── utils/
  │   ├── __init__.py
  │   ├── time_utils.py
  │   └── formatting.py
  ├── requirements.txt
  ├── .env
  └── README.md
  ```

- [ ] **Install dependencies**
  ```bash
  pip install websockets aiohttp python-dotenv rich
  ```

- [ ] **Create requirements.txt**
  ```
  websockets>=12.0
  aiohttp>=3.9.0
  python-dotenv>=1.0.0
  rich>=13.7.0  # For beautiful terminal output
  pydantic>=2.5.0  # For data validation
  ```

- [ ] **Set up .env file**
  ```
  GAMMA_API_BASE=https://gamma-api.polymarket.com
  WS_URL=wss://ws-subscriptions-clob.polymarket.com/ws/market
  PING_INTERVAL=10
  RECONNECT_BASE_DELAY=1
  MAX_RECONNECT_DELAY=30
  BASE_SLUG=btc-updown-15m
  ```

---

## 📋 Phase 2: Core Components Implementation

### A. Time & Slug Generation (`utils/time_utils.py`)
- [ ] **Create timestamp calculation functions**
  ```python
  def get_current_and_next_15min_timestamps() -> dict[str, int]:
      """Calculate current and next 15-minute interval timestamps"""
      pass
  
  def generate_current_and_next_slugs(base_slug: str) -> dict[str, str]:
      """Generate slugs for current and next events"""
      pass
  
  def get_time_remaining(close_date: datetime) -> str:
      """Calculate human-readable time remaining"""
      pass
  ```

### B. Data Models (`models/market.py`)
- [ ] **Define Market model using Pydantic**
  ```python
  from pydantic import BaseModel
  from typing import Optional
  from datetime import datetime
  
  class Market(BaseModel):
      id: str
      slug: str
      question: str
      active: bool
      closed: bool
      close_date: datetime
      clob_token_ids: list[str]
      outcomes: list[str]
      description: Optional[str] = None
  ```

- [ ] **Define WebSocket event models**
  ```python
  class WebSocketEvent(BaseModel):
      event_type: str
      asset_id: Optional[str] = None
      market: Optional[str] = None
      best_bid: Optional[str] = None
      best_ask: Optional[str] = None
      spread: Optional[str] = None
      price: Optional[str] = None
      timestamp: Optional[str] = None
      size: Optional[str] = None
      trade_id: Optional[str] = None
      bids: Optional[list[tuple[str, str]]] = None
      asks: Optional[list[tuple[str, str]]] = None
      assets_ids: Optional[list[str]] = None
  ```

### C. Market State Manager (`models/market_state.py`)
- [ ] **Create MarketState class**
  ```python
  class MarketState:
      def __init__(self, market: Market, outcome: str, is_current: bool):
          self.market = market
          self.outcome = outcome
          self.is_current = is_current
          self.price_history: list[float] = []
          self.trade_history: list[dict] = []
          self.current_price: Optional[float] = None
          self.total_volume: float = 0.0
          self.min_price: Optional[float] = None
          self.max_price: Optional[float] = None
          self.first_price: Optional[float] = None
      
      def update_price(self, price: float):
          """Update price and track history"""
          pass
      
      def add_trade(self, size: float, price: float):
          """Record a trade and update volume"""
          pass
      
      def get_probability(self) -> Optional[float]:
          """Calculate implied probability from price"""
          pass
      
      def get_price_change_pct(self) -> Optional[float]:
          """Calculate % change from first price"""
          pass
  ```

### D. Gamma API Client (`api/gamma_api.py`)
- [ ] **Implement async API client**
  ```python
  import aiohttp
  from typing import Optional
  
  class GammaAPIClient:
      def __init__(self, base_url: str):
          self.base_url = base_url
          self.session: Optional[aiohttp.ClientSession] = None
      
      async def __aenter__(self):
          self.session = aiohttp.ClientSession()
          return self
      
      async def __aexit__(self, exc_type, exc_val, exc_tb):
          await self.session.close()
      
      async def get_market_by_slug(self, slug: str) -> Optional[Market]:
          """Fetch market data by slug"""
          pass
      
      async def get_active_markets(self, limit: int = 50) -> list[Market]:
          """Fetch all active markets"""
          pass
      
      async def find_btc_markets(self) -> list[Market]:
          """Find active BTC 15m markets"""
          pass
  ```

### E. WebSocket Client (`ws/websocket_client.py`)
- [ ] **Implement async WebSocket handler**
  ```python
  import websockets
  import asyncio
  import json
  from typing import Callable, Set
  
  class PolymarketWebSocket:
      def __init__(self, url: str, ping_interval: int = 10):
          self.url = url
          self.ping_interval = ping_interval
          self.ws = None
          self.retry_count = 0
          self.running = False
      
      async def connect(self, asset_ids: Set[str], on_message: Callable):
          """Connect to WebSocket and handle messages"""
          pass
      
      async def subscribe(self, asset_ids: list[str]):
          """Send subscription message"""
          pass
      
      async def ping_loop(self):
          """Send periodic PING messages"""
          pass
      
      async def handle_message(self, message: str, on_message: Callable):
          """Process incoming WebSocket messages"""
          pass
      
      async def reconnect(self, asset_ids: Set[str], on_message: Callable):
          """Reconnect with exponential backoff"""
          pass
  ```

---

## 📋 Phase 3: Main Application Logic

### Main Application (`main.py`)
- [ ] **Initialize application**
  ```python
  import asyncio
  from api.gamma_api import GammaAPIClient
  from ws.websocket_client import PolymarketWebSocket
  from utils.time_utils import generate_current_and_next_slugs
  from models.market_state import MarketState
  from rich.console import Console
  
  console = Console()
  
  async def main():
      # Load config
      # Fetch current and next markets
      # Create market states
      # Connect to WebSocket
      # Handle messages
      pass
  ```

- [ ] **Market discovery function**
  ```python
  async def discover_markets(api_client: GammaAPIClient, base_slug: str):
      """Fetch current and next BTC markets"""
      slugs = generate_current_and_next_slugs(base_slug)
      
      current_market = await api_client.get_market_by_slug(slugs['current'])
      next_market = await api_client.get_market_by_slug(slugs['next'])
      
      # Fallback if needed
      if not current_market:
          btc_markets = await api_client.find_btc_markets()
          current_market = btc_markets[0] if btc_markets else None
      
      return current_market, next_market
  ```

- [ ] **Message handler function**
  ```python
  async def handle_market_event(
      event: WebSocketEvent,
      market_states: dict[str, MarketState]
  ):
      """Process WebSocket events and update market states"""
      if event.asset_id not in market_states:
          return
      
      state = market_states[event.asset_id]
      
      if event.event_type == 'best_bid_ask':
          # Update price
          pass
      elif event.event_type == 'last_trade_price':
          # Record trade
          pass
      elif event.event_type == 'book':
          # Update order book
          pass
      
      # Display update
      display_market_update(state, event)
  ```

---

## 📋 Phase 4: Display & Formatting

### Terminal Output (`utils/formatting.py`)
- [ ] **Use Rich library for beautiful output**
  ```python
  from rich.console import Console
  from rich.table import Table
  from rich.live import Live
  from rich.layout import Layout
  
  def create_market_table(market_states: dict) -> Table:
      """Create formatted table showing both markets"""
      table = Table(title="BTC Up/Down 15m Markets")
      table.add_column("Market", style="cyan")
      table.add_column("Outcome", style="magenta")
      table.add_column("Price", justify="right")
      table.add_column("Prob %", justify="right")
      table.add_column("Volume", justify="right")
      table.add_column("Change %", justify="right")
      table.add_column("Time Left", justify="right")
      
      # Add rows for each market state
      return table
  
  def format_probability(price: float) -> str:
      """Format price as probability percentage"""
      prob = price  # Assuming price is 0-100
      return f"{prob:.1f}%"
  
  def format_time_remaining(seconds: int) -> str:
      """Format seconds as MM:SS"""
      mins = seconds // 60
      secs = seconds % 60
      return f"{mins}m {secs}s"
  ```

- [ ] **Create live dashboard**
  ```python
  async def run_live_dashboard(market_states: dict):
      """Run a live-updating terminal dashboard"""
      with Live(create_market_table(market_states), refresh_per_second=1) as live:
          while True:
              live.update(create_market_table(market_states))
              await asyncio.sleep(1)
  ```

---

## 📋 Phase 5: Analytics & Alerts

### Price Analytics
- [ ] **Implement probability calculation**
  ```python
  def calculate_probability(price: float) -> float:
      """Convert price (0-100 or 0-1) to probability %"""
      # Need to verify actual price scale from API
      if price <= 1:
          return price * 100
      return price
  ```

- [ ] **Track price movements**
  ```python
  class PriceTracker:
      def __init__(self, window_size: int = 100):
          self.prices: list[tuple[float, float]] = []  # (timestamp, price)
          self.window_size = window_size
      
      def add_price(self, timestamp: float, price: float):
          self.prices.append((timestamp, price))
          if len(self.prices) > self.window_size:
              self.prices.pop(0)
      
      def get_moving_average(self, window_seconds: int = 60) -> Optional[float]:
          """Calculate moving average over time window"""
          pass
      
      def detect_rapid_change(self, threshold_pct: float = 5.0, 
                            window_seconds: int = 30) -> bool:
          """Detect if price changed >threshold% in time window"""
          pass
  ```

### Alert System
- [ ] **Define alert conditions**
  ```python
  from dataclasses import dataclass
  from enum import Enum
  
  class AlertType(Enum):
      PRICE_SWING = "price_swing"
      VOLUME_SPIKE = "volume_spike"
      SPREAD_WIDENING = "spread_widening"
      MARKET_CLOSING = "market_closing"
      PROBABILITY_FLIP = "probability_flip"
  
  @dataclass
  class Alert:
      alert_type: AlertType
      message: str
      timestamp: float
      severity: str  # 'info', 'warning', 'critical'
      market_slug: str
      outcome: str
  
  class AlertManager:
      def __init__(self):
          self.alerts: list[Alert] = []
          self.last_alert_time: dict[str, float] = {}
          self.cooldown_seconds = 60
      
      def check_alerts(self, state: MarketState) -> list[Alert]:
          """Check all alert conditions"""
          pass
      
      def trigger_alert(self, alert: Alert):
          """Display and log alert"""
          console.print(f"[bold red]⚠️  ALERT: {alert.message}[/bold red]")
          self.alerts.append(alert)
  ```

---

## 📋 Phase 6: Advanced Features

### Volume Tracking
- [ ] **Implement volume aggregation**
  ```python
  class VolumeTracker:
      def __init__(self):
          self.trades: list[dict] = []
          self.total_volume = 0.0
          self.volume_by_side: dict[str, float] = {'buy': 0.0, 'sell': 0.0}
      
      def add_trade(self, size: float, price: float, side: str = 'unknown'):
          """Record a trade"""
          self.trades.append({
              'timestamp': time.time(),
              'size': size,
              'price': price,
              'side': side
          })
          self.total_volume += size
          if side in self.volume_by_side:
              self.volume_by_side[side] += size
      
      def get_volume_in_window(self, window_seconds: int = 300) -> float:
          """Get volume in recent time window"""
          pass
  ```

### Data Persistence
- [ ] **Save data to JSON files**
  ```python
  import json
  from datetime import datetime
  
  class DataLogger:
      def __init__(self, log_dir: str = './logs'):
          self.log_dir = log_dir
          Path(log_dir).mkdir(exist_ok=True)
      
      def log_event(self, event: dict):
          """Append event to JSONL file"""
          filename = f"{self.log_dir}/events_{datetime.now().strftime('%Y%m%d')}.jsonl"
          with open(filename, 'a') as f:
              f.write(json.dumps(event) + '\n')
      
      def export_to_csv(self, market_state: MarketState, filename: str):
          """Export market data to CSV"""
          pass
  ```

### Configuration
- [ ] **Create config.py**
  ```python
  from pydantic_settings import BaseSettings
  
  class Config(BaseSettings):
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
      
      class Config:
          env_file = ".env"
  ```

---

## 🚀 Immediate Implementation Steps

### Day 1: Core Structure
1. [ ] Set up Python project structure
2. [ ] Install dependencies (websockets, aiohttp, rich)
3. [ ] Create data models with Pydantic
4. [ ] Implement time_utils.py functions
5. [ ] Test timestamp and slug generation

### Day 2: API Integration
6. [ ] Implement GammaAPIClient
7. [ ] Test market fetching by slug
8. [ ] Test fallback to find active BTC markets
9. [ ] Create MarketState class
10. [ ] Test market state updates

### Day 3: WebSocket Connection
11. [ ] Implement PolymarketWebSocket class
12. [ ] Add PING/PONG heartbeat
13. [ ] Add reconnection logic
14. [ ] Test subscription to markets
15. [ ] Parse and display events

### Day 4: Analytics & Display
16. [ ] Calculate probabilities from prices
17. [ ] Track cumulative volume
18. [ ] Implement Rich table display
19. [ ] Add color coding (green/red for UP/DOWN)
20. [ ] Create live-updating dashboard

### Day 5: Alerts & Polish
21. [ ] Implement AlertManager
22. [ ] Add price swing detection
23. [ ] Add volume spike detection
24. [ ] Implement data logging to files
25. [ ] Write README and documentation

---

## 📝 Python-Specific Implementation Notes

### Async/Await Best Practices
```python
# Always use async context managers
async with GammaAPIClient(config.gamma_api_base) as api:
    markets = await api.get_active_markets()

# Gather concurrent tasks
current_task = api.get_market_by_slug(current_slug)
next_task = api.get_market_by_slug(next_slug)
current_market, next_market = await asyncio.gather(current_task, next_task)

# Run multiple async tasks
await asyncio.gather(
    ws_client.connect(asset_ids, handle_message),
    run_live_dashboard(market_states),
    alert_manager.monitor_alerts(market_states)
)
```

### Error Handling Patterns
```python
# Retry with exponential backoff
async def retry_with_backoff(coro, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await coro
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = min(2 ** attempt, 30)
            await asyncio.sleep(delay)

# Graceful shutdown
def setup_signal_handlers(loop):
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

async def shutdown():
    console.print("[yellow]Shutting down gracefully...[/yellow]")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
```

### Rich Console Examples
```python
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich import box

console = Console()

# Styled output
console.print("[bold green]Connected to WebSocket[/bold green]")
console.print("[yellow]Warning:[/yellow] Market closing soon")
console.print(f"[cyan]Current price:[/cyan] [bold]{price}[/bold]")

# Tables
from rich.table import Table
table = Table(title="Market Overview", box=box.ROUNDED)
table.add_column("Market", style="cyan")
table.add_column("Probability", justify="right", style="green")

# Panels
panel = Panel(
    "[green]UP: 52.3%[/green] | [red]DOWN: 47.7%[/red]",
    title="Current Probabilities",
    border_style="blue"
)
console.print(panel)
```

---

## 🛠️ Python Tech Stack

**Required:**
- `websockets` - Async WebSocket client
- `aiohttp` - Async HTTP client
- `pydantic` - Data validation and settings
- `python-dotenv` - Environment variables
- `rich` - Beautiful terminal output

**Optional but Recommended:**
- `loguru` - Better logging than stdlib
- `typer` - CLI interface
- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support
- `pandas` - Data analysis (for CSV export)

---

## 🐛 Python-Specific Gotchas

### Common Issues:
- [ ] Remember to use `asyncio.run()` as entry point
- [ ] WebSocket libraries differ - `websockets` vs `websocket-client` (use `websockets`)
- [ ] JSON serialization of datetime objects (use `.isoformat()`)
- [ ] Event loop already running errors (check for nested `asyncio.run()`)
- [ ] Proper cleanup of WebSocket connections on exit

### Best Practices:
- [ ] Use type hints everywhere
- [ ] Use Pydantic for data validation
- [ ] Use async context managers (`async with`)
- [ ] Handle SIGTERM/SIGINT for graceful shutdown
- [ ] Use `logging` module or `loguru` instead of `print()`
- [ ] Separate I/O code from business logic

---

## 📚 Example Project Structure

```
polymarket-btc-monitor/
├── main.py                 # Entry point
├── config.py              # Configuration with pydantic-settings
├── requirements.txt       # Dependencies
├── .env                   # Environment variables
├── README.md             # Documentation
│
├── api/
│   ├── __init__.py
│   └── gamma_api.py      # Gamma API client
│
├── ws/
│   ├── __init__.py
│   └── websocket_client.py  # WebSocket handler
│
├── models/
│   ├── __init__.py
│   ├── market.py         # Market data models
│   ├── market_state.py   # Market state tracker
│   └── events.py         # WebSocket event models
│
├── analytics/
│   ├── __init__.py
│   ├── price_tracker.py  # Price analysis
│   ├── volume_tracker.py # Volume tracking
│   └── alerts.py         # Alert system
│
├── utils/
│   ├── __init__.py
│   ├── time_utils.py     # Time calculations
│   ├── formatting.py     # Rich console formatting
│   └── logger.py         # Logging setup
│
├── data/
│   └── logs/            # Event logs (gitignored)
│
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_websocket.py
    └── test_analytics.py
```

---

**Last Updated:** 2025-01-08
**Status:** Ready for Python implementation
**Current Focus:** Setting up async architecture with websockets + aiohttp
