# 🚀 Polymarket BTC Up/Down 15m Event Monitor

A real-time WebSocket-based monitoring system for Polymarket's Bitcoin price prediction markets with 15-minute intervals.

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Features

- **Real-time Market Monitoring**: WebSocket connection for live market data
- **BTC Market Discovery**: Automatically finds BTC 15-minute prediction markets
- **Live Odds Tracking**: Monitor up/down probabilities in real-time
- **Alert System**: Get notified of significant price changes and volume spikes
- **Rich Terminal UI**: Beautiful console dashboard with live updates
- **Multiple Notification Channels**: Console, Telegram, and Discord alerts
- **Configurable Thresholds**: Customize alert triggers and update intervals

## 🎯 Project Structure

```
polymarket-btc-monitor/
├── src/
│   ├── core/
│   │   ├── market_discovery.py    # Find and filter BTC markets
│   │   └── websocket_client.py    # WebSocket connection & data processing
│   ├── alerts/
│   │   └── alert_system.py        # Alert detection and notifications
│   ├── ui/
│   │   └── terminal_dashboard.py  # Terminal UI components
│   └── utils/
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging setup
├── tests/
│   ├── test_market_discovery.py
│   └── test_alert_system.py
├── main.py                         # Main application entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── TODO.md                         # Development roadmap
```

## 🚀 Quick Start

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
   cp .env.example .env
   # Edit .env with your preferences
   ```

4. **Run the monitor**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

Edit `.env` to customize settings:

```bash
# Alert thresholds
ALERT_PRICE_CHANGE_THRESHOLD=5       # Percentage change to trigger alert
ALERT_VOLUME_SPIKE_THRESHOLD=10000   # USD volume spike threshold

# Update interval
UPDATE_INTERVAL=5                     # Seconds between updates

# UI settings
ENABLE_TERMINAL_UI=true              # Use rich terminal UI
LOG_LEVEL=INFO                       # Logging level

# Notifications (optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_webhook_url
```

## 📊 Usage

### Basic Monitoring

Simply run the application to start monitoring:

```bash
python main.py
```

The monitor will:
1. Discover active BTC 15-minute markets
2. Connect to Polymarket's WebSocket API
3. Subscribe to market updates
4. Display live data in the terminal
5. Alert on significant changes

### Terminal Dashboard

The rich terminal UI shows:
- **Header**: Uptime and market count
- **Markets Table**: Live odds, volume, liquidity
- **Alerts Panel**: Recent notifications
- **Statistics**: Aggregate metrics

### Simple Mode

To use simple text output instead of the rich UI:

```bash
ENABLE_TERMINAL_UI=false python main.py
```

## 🔧 API Integration

### Polymarket APIs Used

1. **Gamma API** - Market discovery and metadata
   - Endpoint: `https://gamma-api.polymarket.com`
   - Used for: Searching BTC markets, getting market details

2. **WebSocket API** - Real-time data
   - Used for: Live market updates, order book, trades
   - Channels: Market channel for public data

### Authentication

API credentials are **optional** for read-only market monitoring. Required only for:
- Placing orders
- Accessing private user data

To add credentials:
```bash
POLYMARKET_API_KEY=your_key
POLYMARKET_API_SECRET=your_secret
POLYMARKET_PASSPHRASE=your_passphrase
POLYMARKET_WALLET_ADDRESS=your_address
```

## 📈 Alert Types

### Price Change Alerts
Triggered when odds change by more than the threshold percentage:
```
⚠️  [14:23:15] WARNING: Price increased by 7.5% (from 45.0% to 52.5%)
```

### Volume Spike Alerts
Triggered when volume increases significantly:
```
⚠️  [14:25:30] WARNING: Volume spiked by $15,000 (150% increase)
```

### New Market Alerts
Triggered when a new BTC 15m market is discovered:
```
ℹ️  [14:20:00] INFO: New BTC market discovered: Will BTC be up in 15 minutes?
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run specific tests:

```bash
pytest tests/test_market_discovery.py -v
pytest tests/test_alert_system.py -v
```

## 🛠️ Development

### Project Status

Currently in **Planning/Development Phase**. See [TODO.md](TODO.md) for the complete development roadmap.

### Completed Features

- ✅ Project structure setup
- ✅ Market discovery system
- ✅ WebSocket client implementation
- ✅ Data processing and odds calculation
- ✅ Alert system with multiple triggers
- ✅ Rich terminal UI
- ✅ Configuration management
- ✅ Basic tests

### Upcoming Features

- [ ] User authentication support
- [ ] Historical data storage
- [ ] Web dashboard (optional)
- [ ] Paper trading simulator
- [ ] Multi-market comparison
- [ ] Advanced analytics

## 📚 Resources

- [Polymarket Documentation](https://docs.polymarket.com/)
- [WSS Overview](https://docs.polymarket.com/developers/CLOB/websocket/wss-overview)
- [Get Markets API](https://docs.polymarket.com/developers/gamma-markets-api/get-markets)
- [Gamma Structure](https://docs.polymarket.com/developers/gamma-markets-api/gamma-structure)
- [polymarket-apis PyPI](https://pypi.org/project/polymarket-apis/)
- [Polymarket Agents GitHub](https://github.com/Polymarket/agents)

## 🐛 Troubleshooting

### No markets found
- BTC 15-minute markets may not always be available
- The monitor will fall back to other active BTC markets
- Check Polymarket website for current markets

### WebSocket connection issues
- Check your internet connection
- Verify Polymarket API is accessible
- Review logs for specific error messages

### Import errors
- Ensure Python 3.12+ is installed
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## ⚠️ Disclaimer

This tool is for educational and informational purposes only. It monitors publicly available market data from Polymarket. Always do your own research before making trading decisions.

## 📞 Support

- Issues: [GitHub Issues](https://github.com/alchemy666888/work/issues)
- Discussions: Use GitHub Discussions

---

**Built with ❤️ for the Polymarket community**
