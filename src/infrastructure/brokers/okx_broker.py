"""OKX exchange broker implementation.

Supports both demo/sandbox trading (default) and live trading.
Demo: https://www.okx.com (with simulated trading header)
Live: https://www.okx.com

Features:
- Spot trading (US limitation)
- Demo trading environment
- HMAC-SHA256 authentication
"""

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging

import requests

from ...application.interfaces.broker import (
    AbstractBroker,
    Order,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    Position,
    AccountBalance,
)

logger = logging.getLogger(__name__)


class OKXBroker(AbstractBroker):
    """OKX crypto exchange broker.

    Demo/sandbox trading is enabled by default. Set paper=False for live trading
    with explicit risk acknowledgment.

    Note: OKX US only supports spot trading. Futures/margin not available.
    """

    BASE_URL = "https://www.okx.com"
    DEMO_HEADER = "1"  # x-simulated-trading header value

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        paper: bool = True,
        config: Optional[dict] = None
    ):
        super().__init__(
            name="okx",
            api_key=api_key,
            api_secret=api_secret,
            paper=paper,
            config=config
        )
        self.passphrase = passphrase
        self.base_url = self.config.get("base_url", self.BASE_URL)
        self.session = requests.Session()

    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC-SHA256 signature for OKX API.

        Args:
            timestamp: ISO format timestamp
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            body: Request body (empty string for GET)

        Returns:
            Base64 encoded signature
        """
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    def _get_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate request headers with authentication."""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        signature = self._generate_signature(timestamp, method, path, body)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        if self.paper:
            headers["x-simulated-trading"] = self.DEMO_HEADER

        return headers

    async def connect(self) -> bool:
        """Connect to OKX API.

        Returns:
            True if connection successful
        """
        if not all([self.api_key, self.api_secret, self.passphrase]):
            logger.error("OKX API key, secret, and passphrase are required")
            return False

        try:
            # Verify connection by fetching account balance
            path = "/api/v5/account/balance"
            url = f"{self.base_url}{path}"
            headers = self._get_headers("GET", path)

            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                mode = "demo" if self.paper else "live"
                logger.info(f"Connected to OKX {mode} trading")
                self._connected = True
                return True
            else:
                logger.error(f"OKX API error: {data.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to OKX: {e}")
            return False

    async def get_account_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            AccountBalance with cash, buying power, equity
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        path = "/api/v5/account/balance"
        url = f"{self.base_url}{path}"
        headers = self._get_headers("GET", path)

        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "0":
                raise RuntimeError(f"OKX API error: {data.get('msg')}")

            details = data.get("data", [{}])[0]

            # OKX returns balances per currency
            total_equity = Decimal("0")
            total_cash = Decimal("0")

            for balance in details.get("details", []):
                eq = Decimal(balance.get("eq", "0"))  # Total equity
                cash = Decimal(balance.get("cashBal", "0"))  # Cash balance
                total_equity += eq
                total_cash += cash

            # Buying power is more complex in OKX (available balance for trading)
            # Using availBal for the primary currency
            buying_power = Decimal("0")
            for balance in details.get("details", []):
                if balance.get("ccy") == "USDT":  # Use USDT as proxy for buying power
                    buying_power = Decimal(balance.get("availBal", "0"))
                    break

            return AccountBalance(
                currency="USDT",  # OKX uses USDT as primary
                cash=total_cash,
                buying_power=buying_power,
                equity=total_equity,
            )

        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise

    async def place_order(self, order: Order) -> OrderResult:
        """Place a new order.

        Supports:
        - Market orders
        - Limit orders
        - Spot trading only (US limitation)

        Args:
            order: Order details

        Returns:
            OrderResult with execution status
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        # Map internal order side/type to OKX format
        side = "buy" if order.side == OrderSide.BUY else "sell"
        ord_type = "market" if order.order_type == OrderType.MARKET else "limit"

        # OKX uses different order size modes
        # For market orders: use sz (size in base currency) or tgtCcy
        # For simplicity, we'll use sz with the quantity

        body = {
            "instId": order.symbol,  # e.g., "BTC-USDT"
            "tdMode": "cash",  # Spot trading
            "side": side,
            "ordType": ord_type,
            "sz": str(order.quantity),
        }

        if order.order_type == OrderType.LIMIT:
            if order.price is None:
                raise ValueError("Limit orders require a price")
            body["px"] = str(order.price)

        # Time in force
        if order.time_in_force.lower() == "gtc":
            body["tgtCcy"] = "base_ccy"  # Good till cancel
        elif order.time_in_force.lower() == "ioc":
            body["ordType"] = "ioc"
        elif order.time_in_force.lower() == "fok":
            body["ordType"] = "fok"

        import json
        body_json = json.dumps(body)

        path = "/api/v5/trade/order"
        url = f"{self.base_url}{path}"
        headers = self._get_headers("POST", path, body_json)

        try:
            response = self.session.post(url, headers=headers, data=body_json, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "0":
                error_msg = data.get('msg', 'Unknown error')
                logger.error(f"OKX order failed: {error_msg}")
                return OrderResult(
                    order_id="",
                    status=OrderStatus.REJECTED,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    filled_quantity=Decimal("0"),
                    avg_fill_price=None,
                    created_at=datetime.now(timezone.utc),
                    broker_message=error_msg,
                )

            order_data = data.get("data", [{}])[0]
            return self._convert_order(order_data)

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str = "") -> bool:
        """Cancel an existing order.

        Args:
            order_id: Order to cancel
            symbol: Trading pair (required by OKX)

        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        if not symbol:
            # Need to look up the symbol from the order
            order = await self.get_order(order_id)
            if not order:
                logger.error(f"Cannot cancel order {order_id}: order not found")
                return False
            symbol = order.symbol

        body = {
            "instId": symbol,
            "ordId": order_id,
        }

        import json
        body_json = json.dumps(body)

        path = "/api/v5/trade/cancel-order"
        url = f"{self.base_url}{path}"
        headers = self._get_headers("POST", path, body_json)

        try:
            response = self.session.post(url, headers=headers, data=body_json, timeout=10)
            response.raise_for_status()
            data = response.json()

            return data.get("code") == "0"

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order(self, order_id: str) -> Optional[OrderResult]:
        """Get order status by ID.

        Note: OKX requires both order ID and symbol.
        We'll need to query all open orders to find it.

        Args:
            order_id: Order ID

        Returns:
            OrderResult or None if not found
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        # OKX requires instId for order queries
        # We'll try to find it by querying recent orders
        orders = await self.get_open_orders()
        for order in orders:
            if order.order_id == order_id:
                return order

        # Check filled orders
        path = "/api/v5/trade/orders-history"
        url = f"{self.base_url}{path}"
        params = {"instType": "SPOT", "limit": "100"}

        try:
            import urllib.parse
            query_string = urllib.parse.urlencode(params)
            full_path = f"{path}?{query_string}"
            headers = self._get_headers("GET", full_path)

            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                for order_data in data.get("data", []):
                    if order_data.get("ordId") == order_id:
                        return self._convert_order(order_data)

            return None

        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """Get all current positions.

        For spot trading, positions are simply the account balances.

        Returns:
            List of Position objects
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        path = "/api/v5/account/balance"
        url = f"{self.base_url}{path}"
        headers = self._get_headers("GET", path)

        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "0":
                return []

            positions = []
            details = data.get("data", [{}])[0].get("details", [])

            for balance in details:
                qty = Decimal(balance.get("eq", "0"))
                if qty > 0:
                    positions.append(
                        Position(
                            symbol=balance.get("ccy", ""),
                            quantity=qty,
                            avg_entry_price=Decimal(balance.get("avgPx", "0")),
                            current_price=None,
                            market_value=None,
                            unrealized_pnl=None,
                            side="long",
                        )
                    )

            return positions

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol.

        Args:
            symbol: Asset symbol (e.g., "BTC")

        Returns:
            Position or None if no position
        """
        positions = await self.get_positions()
        for position in positions:
            if position.symbol == symbol:
                return position
        return None

    async def get_open_orders(self) -> List[OrderResult]:
        """Get all open orders.

        Returns:
            List of open OrderResult objects
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        path = "/api/v5/trade/orders-pending"
        url = f"{self.base_url}{path}"
        params = {"instType": "SPOT", "limit": "100"}

        try:
            import urllib.parse
            query_string = urllib.parse.urlencode(params)
            full_path = f"{path}?{query_string}"
            headers = self._get_headers("GET", full_path)

            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                return [self._convert_order(o) for o in data.get("data", [])]

            return []

        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    def _convert_order(self, order_data: Dict[str, Any]) -> OrderResult:
        """Convert OKX order data to internal OrderResult."""
        status_map = {
            "live": OrderStatus.OPEN,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }

        side_map = {
            "buy": OrderSide.BUY,
            "sell": OrderSide.SELL,
        }

        ord_type_map = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "post_only": OrderType.LIMIT,
            "fok": OrderType.LIMIT,
            "ioc": OrderType.LIMIT,
        }

        return OrderResult(
            order_id=order_data.get("ordId", ""),
            status=status_map.get(order_data.get("state"), OrderStatus.REJECTED),
            symbol=order_data.get("instId", ""),
            side=side_map.get(order_data.get("side"), OrderSide.BUY),
            order_type=ord_type_map.get(order_data.get("ordType"), OrderType.MARKET),
            quantity=Decimal(order_data.get("sz", "0")),
            filled_quantity=Decimal(order_data.get("accFillSz", "0")),
            avg_fill_price=Decimal(order_data.get("avgPx")) if order_data.get("avgPx") else None,
            created_at=datetime.fromisoformat(order_data.get("cTime", "").replace('Z', '+00:00')) if order_data.get("cTime") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(order_data.get("uTime", "").replace('Z', '+00:00')) if order_data.get("uTime") else None,
            broker_message=order_data.get("state"),
        )
