# Polymarket BTC Up/Down 15m Event Monitor

A real-time WebSocket-based monitoring system for Polymarket's Bitcoin price prediction markets with 15-minute intervals.

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Real-time Market Monitoring**: Pure WebSocket connection for live market data
- **BTC Market Discovery**: Automatically finds BTC 15-minute prediction markets
- **Live Odds Tracking**: Monitor up/down probabilities in real-time
- **Alert System**: Get notified of price swings, volume spikes, and market closing
- **Rich Terminal UI**: Beautiful console dashboard with live updates
- **Async Architecture**: Built with asyncio, aiohttp, and websockets
- **Pydantic Models**: Type-safe data validation and configuration

## Project Structure

```
polymarket-btc-monitor/
├── main.py                 # Entry point
├── config.py               # Configuration with pydantic-settings
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── README.md               # Documentation
│
├── api/
│   ├── __init__.py
│   └── gamma_api.py        # Gamma API client
│
├── ws/
│   ├── __init__.py
│   └── websocket_client.py # WebSocket handler
│
├── models/
│   ├── __init__.py
│   ├── market.py           # Market data models
│   ├── market_state.py     # Market state tracker
│   └── events.py           # WebSocket event models
│
├── analytics/
│   ├── __init__.py
│   ├── price_tracker.py    # Price analysis
│   ├── volume_tracker.py   # Volume tracking
│   └── alerts.py           # Alert system
│
├── utils/
│   ├── __init__.py
│   ├── time_utils.py       # Time calculations
│   ├── formatting.py       # Rich console formatting
│   └── logger.py           # Logging setup
│
├── data/
│   └── logs/               # Event logs (gitignored)
│
└── tests/
    ├── __init__.py
    ├── test_time_utils.py
    ├── test_models.py
    └── test_analytics.py
```

## Quick Start

### Prerequisites

- Python 3.12 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alchemy666888/work.git
   cd work
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   # Edit .env with your preferences
   ```

4. **Run the monitor**
   ```bash
   python main.py
   ```

## Configuration

Edit `.env` to customize settings:

```bash
# API Settings
GAMMA_API_BASE=https://gamma-api.polymarket.com
WS_URL=wss://ws-subscriptions-clob.polymarket.com/ws/market

# Connection Settings
PING_INTERVAL=10
RECONNECT_BASE_DELAY=1
MAX_RECONNECT_DELAY=30

# Market Settings
BASE_SLUG=btc-updown-15m

# Alert Thresholds
PRICE_SWING_THRESHOLD=5.0      # Percentage
PRICE_SWING_WINDOW=30          # Seconds
VOLUME_SPIKE_MULTIPLIER=2.0
MARKET_CLOSING_ALERT=120       # Seconds

# Display Settings
USE_RICH_OUTPUT=true
REFRESH_RATE=1.0               # Hz

# Logging
LOG_LEVEL=INFO
```

## Usage

### Basic Monitoring

Simply run the application to start monitoring:

```bash
python main.py
```

The monitor will:
1. Calculate current and next 15-minute interval timestamps
2. Discover active BTC 15-minute markets using Gamma API
3. Connect to Polymarket's WebSocket API
4. Subscribe to market token IDs
5. Display live data in a Rich terminal dashboard
6. Alert on significant changes

### Terminal Dashboard

The Rich terminal UI shows:
- **Markets Table**: Live odds, probability, volume, and time remaining
- **Color Coding**: Green for UP, Red for DOWN outcomes
- **Alerts**: Real-time notifications for price swings and events

## Architecture

### Async Design

The application uses Python's asyncio for concurrent operations:

```python
# Fetch markets concurrently
current_task = api.get_market_by_slug(current_slug)
next_task = api.get_market_by_slug(next_slug)
current_market, next_market = await asyncio.gather(current_task, next_task)

# Run multiple tasks
await asyncio.gather(
    ws_client.connect(asset_ids, handle_message),
    run_live_dashboard(market_states),
)
```

### WebSocket Events

Supported event types:
- `best_bid_ask`: Price updates from order book
- `last_trade_price`: Trade execution events
- `book`: Full order book snapshots
- `ping/pong`: Connection heartbeat

### Market State Tracking

Each market outcome (UP/DOWN) has its own state tracker:
- Price history and moving averages
- Trade history and volume
- Min/max prices
- Probability calculations

## Alert Types

### Price Swing Alerts
Triggered when price changes exceed threshold:
```
ALERT: Price swung up by 7.50%
```

### Probability Flip Alerts
Triggered when probability crosses 50%:
```
ALERT: Probability flipped above 50% (now 52.3%)
```

### Market Closing Alerts
Triggered when market is about to close:
```
ALERT: Market closing in 2m 0s
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test files:

```bash
pytest tests/test_time_utils.py -v
pytest tests/test_models.py -v
pytest tests/test_analytics.py -v
```

## Dependencies

**Required:**
- `websockets>=12.0` - Async WebSocket client
- `aiohttp>=3.9.0` - Async HTTP client
- `pydantic>=2.5.0` - Data validation
- `pydantic-settings>=2.1.0` - Configuration management
- `python-dotenv>=1.0.0` - Environment variables
- `rich>=13.7.0` - Beautiful terminal output
- `loguru>=0.7.0` - Logging

**Development:**
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support

## API Integration

### Polymarket APIs Used

1. **Gamma API** - Market discovery and metadata
   - Endpoint: `https://gamma-api.polymarket.com`
   - Used for: Searching BTC markets, getting market details

2. **WebSocket API** - Real-time data
   - Endpoint: `wss://ws-subscriptions-clob.polymarket.com/ws/market`
   - Used for: Live price updates, order book, trades

## Resources

- [Polymarket Documentation](https://docs.polymarket.com/)
- [WSS Overview](https://docs.polymarket.com/developers/CLOB/websocket/wss-overview)
- [Gamma Markets API](https://docs.polymarket.com/developers/gamma-markets-api/get-markets)
- [Gamma Structure](https://docs.polymarket.com/developers/gamma-markets-api/gamma-structure)

## Troubleshooting

### No markets found
- BTC 15-minute markets may not always be available
- The monitor will fall back to searching for active BTC markets
- Check Polymarket website for current markets

### WebSocket connection issues
- Check your internet connection
- The client has automatic reconnection with exponential backoff
- Review logs for specific error messages

### Import errors
- Ensure Python 3.12+ is installed
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational and informational purposes only. It monitors publicly available market data from Polymarket. Always do your own research before making trading decisions.

---

**Built with Python async/await architecture**
