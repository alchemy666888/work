"""Web server for monitoring dashboard"""

import asyncio
import json
from typing import Callable, Optional
from aiohttp import web, WSMsgType
from utils.logger import logger


# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BTC Up/Down 15m Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .status-item {
            background: rgba(255,255,255,0.1);
            padding: 15px 25px;
            border-radius: 10px;
            text-align: center;
        }
        .status-label {
            font-size: 0.8rem;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .status-value {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .status-value.connected { color: #4ade80; }
        .status-value.disconnected { color: #f87171; }

        .markets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .market-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .market-card.current {
            border-color: #3a7bd5;
            box-shadow: 0 0 20px rgba(58, 123, 213, 0.3);
        }
        .market-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .market-title {
            font-size: 1.2rem;
            font-weight: bold;
        }
        .market-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            text-transform: uppercase;
        }
        .badge-current {
            background: #3a7bd5;
            color: white;
        }
        .badge-next {
            background: #666;
            color: white;
        }
        .market-time {
            font-size: 0.9rem;
            color: #888;
            margin-bottom: 15px;
        }
        .outcomes-table {
            width: 100%;
            border-collapse: collapse;
        }
        .outcomes-table th,
        .outcomes-table td {
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .outcomes-table th {
            color: #888;
            font-weight: normal;
            font-size: 0.8rem;
            text-transform: uppercase;
        }
        .outcome-up { color: #4ade80; }
        .outcome-down { color: #f87171; }
        .price {
            font-size: 1.3rem;
            font-weight: bold;
        }
        .change {
            font-size: 0.9rem;
        }
        .change.positive { color: #4ade80; }
        .change.negative { color: #f87171; }
        .spread {
            color: #888;
            font-size: 0.85rem;
        }

        .footer {
            text-align: center;
            color: #666;
            font-size: 0.8rem;
            margin-top: 30px;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .updating {
            animation: pulse 1s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>BTC Up/Down 15m Monitor</h1>
            <p>Real-time Polymarket prediction market monitoring</p>
        </header>

        <div class="status-bar">
            <div class="status-item">
                <div class="status-label">Connection</div>
                <div class="status-value" id="connection-status">Connecting...</div>
            </div>
            <div class="status-item">
                <div class="status-label">Markets</div>
                <div class="status-value" id="market-count">0</div>
            </div>
            <div class="status-item">
                <div class="status-label">Last Update</div>
                <div class="status-value" id="last-update">--:--:--</div>
            </div>
        </div>

        <div class="markets-grid" id="markets-container">
            <div class="market-card">
                <p style="text-align: center; color: #888;">Waiting for market data...</p>
            </div>
        </div>

        <div class="footer">
            <p>Polymarket BTC Up/Down 15m Event Monitor</p>
        </div>
    </div>

    <script>
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 10;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('connection-status').className = 'status-value connected';
            };

            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                } catch (e) {
                    console.error('Failed to parse message:', e);
                }
            };

            ws.onclose = function() {
                console.log('WebSocket disconnected');
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-status').className = 'status-value disconnected';

                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                    console.log(`Reconnecting in ${delay}ms...`);
                    setTimeout(connect, delay);
                }
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function updateDashboard(data) {
            // Update last update time
            const now = new Date();
            document.getElementById('last-update').textContent = now.toLocaleTimeString();

            // Update market count
            const marketCount = Object.keys(data.markets || {}).length;
            document.getElementById('market-count').textContent = marketCount;

            // Group states by market
            const marketGroups = {};
            for (const [assetId, state] of Object.entries(data.states || {})) {
                const marketSlug = state.market_slug || 'unknown';
                if (!marketGroups[marketSlug]) {
                    marketGroups[marketSlug] = {
                        slug: marketSlug,
                        question: state.question || marketSlug,
                        close_date: state.close_date,
                        is_current: state.is_current,
                        outcomes: {}
                    };
                }
                marketGroups[marketSlug].outcomes[state.outcome] = state;
            }

            // Render markets
            const container = document.getElementById('markets-container');
            if (Object.keys(marketGroups).length === 0) {
                container.innerHTML = '<div class="market-card"><p style="text-align: center; color: #888;">No markets available</p></div>';
                return;
            }

            // Sort: current first, then next
            const sortedMarkets = Object.values(marketGroups).sort((a, b) => {
                if (a.is_current && !b.is_current) return -1;
                if (!a.is_current && b.is_current) return 1;
                return 0;
            });

            container.innerHTML = sortedMarkets.map(market => {
                const isCurrent = market.is_current;
                const upState = market.outcomes['UP'] || {};
                const downState = market.outcomes['DOWN'] || {};

                const timeRemaining = market.close_date ? formatTimeRemaining(market.close_date) : '--';

                return `
                    <div class="market-card ${isCurrent ? 'current' : ''}">
                        <div class="market-header">
                            <span class="market-title">${escapeHtml(market.question || market.slug)}</span>
                            <span class="market-badge ${isCurrent ? 'badge-current' : 'badge-next'}">
                                ${isCurrent ? 'Current' : 'Next'}
                            </span>
                        </div>
                        <div class="market-time">Closes in: ${timeRemaining}</div>
                        <table class="outcomes-table">
                            <thead>
                                <tr>
                                    <th>Outcome</th>
                                    <th>Price</th>
                                    <th>Change</th>
                                    <th>Bid/Ask</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="outcome-up">UP</td>
                                    <td class="price">${formatPrice(upState.current_price)}</td>
                                    <td class="change ${getChangeClass(upState.price_change_pct)}">${formatChange(upState.price_change_pct)}</td>
                                    <td class="spread">${formatBidAsk(upState.best_bid, upState.best_ask)}</td>
                                </tr>
                                <tr>
                                    <td class="outcome-down">DOWN</td>
                                    <td class="price">${formatPrice(downState.current_price)}</td>
                                    <td class="change ${getChangeClass(downState.price_change_pct)}">${formatChange(downState.price_change_pct)}</td>
                                    <td class="spread">${formatBidAsk(downState.best_bid, downState.best_ask)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `;
            }).join('');
        }

        function formatPrice(price) {
            if (price === null || price === undefined) return '--';
            return (price * 100).toFixed(1) + '%';
        }

        function formatChange(change) {
            if (change === null || change === undefined) return '--';
            const sign = change >= 0 ? '+' : '';
            return sign + change.toFixed(2) + '%';
        }

        function getChangeClass(change) {
            if (change === null || change === undefined) return '';
            return change >= 0 ? 'positive' : 'negative';
        }

        function formatBidAsk(bid, ask) {
            const bidStr = bid !== null && bid !== undefined ? (bid * 100).toFixed(1) : '--';
            const askStr = ask !== null && ask !== undefined ? (ask * 100).toFixed(1) : '--';
            return `${bidStr} / ${askStr}`;
        }

        function formatTimeRemaining(closeDate) {
            const close = new Date(closeDate);
            const now = new Date();
            const diff = close - now;

            if (diff <= 0) return 'Ended';

            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);

            if (hours > 0) {
                return `${hours}h ${minutes % 60}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${seconds % 60}s`;
            } else {
                return `${seconds}s`;
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Start connection
        connect();
    </script>
</body>
</html>
"""


class WebServer:
    """
    Aiohttp-based web server for the monitoring dashboard.

    Provides:
    - HTML dashboard at /
    - WebSocket endpoint at /ws for real-time updates
    - JSON API at /api/status for current state
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        get_state: Optional[Callable] = None,
    ):
        """
        Initialize web server.

        Args:
            host: Host to bind to
            port: Port to listen on
            get_state: Callback to get current monitor state
        """
        self.host = host
        self.port = port
        self.get_state = get_state

        self.app = web.Application()
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/ws", self.handle_websocket)
        self.app.router.add_get("/api/status", self.handle_api_status)

        self.websockets: set[web.WebSocketResponse] = set()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.running = False
        self._broadcast_task: Optional[asyncio.Task] = None

    async def handle_index(self, request: web.Request) -> web.Response:
        """Serve the HTML dashboard."""
        return web.Response(text=DASHBOARD_HTML, content_type="text/html")

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websockets.add(ws)
        logger.info(f"WebSocket client connected (total: {len(self.websockets)})")

        try:
            # Send initial state
            if self.get_state:
                state = self.get_state()
                await ws.send_json(state)

            # Keep connection alive
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Handle any client messages if needed
                    pass
                elif msg.type == WSMsgType.ERROR:
                    logger.warning(f"WebSocket error: {ws.exception()}")
                    break
        finally:
            self.websockets.discard(ws)
            logger.info(f"WebSocket client disconnected (total: {len(self.websockets)})")

        return ws

    async def handle_api_status(self, request: web.Request) -> web.Response:
        """Return current state as JSON."""
        if self.get_state:
            state = self.get_state()
            return web.json_response(state)
        return web.json_response({"error": "No state available"}, status=503)

    async def broadcast_state(self, state: dict):
        """Broadcast state to all connected WebSocket clients."""
        if not self.websockets:
            return

        # Send to all clients, removing any that fail
        closed = set()
        for ws in self.websockets:
            try:
                await ws.send_json(state)
            except Exception:
                closed.add(ws)

        self.websockets -= closed

    async def _broadcast_loop(self, interval: float = 1.0):
        """Periodically broadcast state to all clients."""
        try:
            while self.running:
                if self.get_state and self.websockets:
                    state = self.get_state()
                    await self.broadcast_state(state)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    async def start(self):
        """Start the web server."""
        self.running = True

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        # Start broadcast loop
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())

        logger.info(f"Web server started at http://{self.host}:{self.port}")

    async def stop(self):
        """Stop the web server."""
        self.running = False

        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections
        for ws in self.websockets:
            await ws.close()
        self.websockets.clear()

        if self.runner:
            await self.runner.cleanup()

        logger.info("Web server stopped")
