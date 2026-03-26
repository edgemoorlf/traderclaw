"""Multi-account broker manager for TraderClaw.

Manages multiple broker accounts (paper and live) for strategy comparison
tand isolation.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import yaml

from ...application.interfaces.broker import AbstractBroker
from .alpaca_broker import AlpacaBroker

logger = logging.getLogger(__name__)


@dataclass
class BrokerAccountConfig:
    """Configuration for a broker account."""
    account_id: str
    broker_type: str  # "alpaca", "okx", etc.
    name: str
    paper: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None  # For OKX
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)


class BrokerManager:
    """
    Manages multiple broker accounts.

    Supports:
    - Multiple Alpaca paper accounts for strategy comparison
    - Named accounts (e.g., "strategy_a_paper", "strategy_b_paper")
    - Account isolation for risk management
    """

    def __init__(self, config_path: str = "config/brokers.yaml"):
        self.config_path = Path(config_path)
        self._brokers: Dict[str, AbstractBroker] = {}
        self._configs: Dict[str, BrokerAccountConfig] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """Load broker configurations from file."""
        if not self.config_path.exists():
            logger.warning(f"Broker config not found: {self.config_path}")
            return

        try:
            with open(self.config_path) as f:
                data = yaml.safe_load(f) or {}

            for account_data in data.get("accounts", []):
                config = BrokerAccountConfig(
                    account_id=account_data["account_id"],
                    broker_type=account_data["broker_type"],
                    name=account_data.get("name", account_data["account_id"]),
                    paper=account_data.get("paper", True),
                    api_key=account_data.get("api_key"),
                    api_secret=account_data.get("api_secret"),
                    passphrase=account_data.get("passphrase"),
                    enabled=account_data.get("enabled", True),
                    metadata=account_data.get("metadata", {}),
                )
                self._configs[config.account_id] = config

            logger.info(f"Loaded {len(self._configs)} broker account configs")

        except Exception as e:
            logger.error(f"Failed to load broker configs: {e}")

    def save_configs(self) -> None:
        """Save broker configurations to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "accounts": [
                {
                    "account_id": cfg.account_id,
                    "broker_type": cfg.broker_type,
                    "name": cfg.name,
                    "paper": cfg.paper,
                    "api_key": cfg.api_key,
                    "api_secret": cfg.api_secret,
                    "passphrase": cfg.passphrase,
                    "enabled": cfg.enabled,
                    "metadata": cfg.metadata,
                }
                for cfg in self._configs.values()
            ]
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def add_account(self, config: BrokerAccountConfig) -> None:
        """Add a new broker account."""
        self._configs[config.account_id] = config
        self.save_configs()
        logger.info(f"Added broker account: {config.account_id}")

    def remove_account(self, account_id: str) -> bool:
        """Remove a broker account."""
        if account_id in self._configs:
            del self._configs[account_id]
            self._brokers.pop(account_id, None)
            self.save_configs()
            return True
        return False

    def get_broker(self, account_id: str = "default") -> AbstractBroker:
        """
        Get or create broker instance for account.

        Args:
            account_id: Account identifier

        Returns:
            Broker instance
        """
        if account_id in self._brokers:
            return self._brokers[account_id]

        # Create new broker instance
        config = self._configs.get(account_id)
        if not config:
            # Try to use default/first available account
            if "default" in self._configs:
                config = self._configs["default"]
            elif self._configs:
                config = list(self._configs.values())[0]
            else:
                raise ValueError(f"No broker account configured for: {account_id}")

        if not config.enabled:
            raise ValueError(f"Account {account_id} is disabled")

        # Create broker based on type
        if config.broker_type == "alpaca":
            broker = AlpacaBroker(
                api_key=config.api_key,
                api_secret=config.api_secret,
                paper=config.paper,
            )
        else:
            raise ValueError(f"Unsupported broker type: {config.broker_type}")

        self._brokers[account_id] = broker
        return broker

    def list_accounts(self) -> List[BrokerAccountConfig]:
        """List all configured accounts."""
        return list(self._configs.values())

    def get_account(self, account_id: str) -> Optional[BrokerAccountConfig]:
        """Get account configuration."""
        return self._configs.get(account_id)

    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all enabled accounts."""
        results = {}
        for account_id, config in self._configs.items():
            if not config.enabled:
                continue
            try:
                broker = self.get_broker(account_id)
                connected = await broker.connect()
                results[account_id] = connected
            except Exception as e:
                logger.error(f"Failed to connect {account_id}: {e}")
                results[account_id] = False
        return results

    def create_paper_account(
        self,
        account_id: str,
        name: str,
        api_key: str,
        api_secret: str,
        metadata: Optional[Dict] = None
    ) -> BrokerAccountConfig:
        """
        Create a new paper trading account.

        Args:
            account_id: Unique identifier
            name: Human-readable name
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            metadata: Optional metadata

        Returns:
            Account configuration
        """
        config = BrokerAccountConfig(
            account_id=account_id,
            broker_type="alpaca",
            name=name,
            paper=True,
            api_key=api_key,
            api_secret=api_secret,
            metadata=metadata or {},
        )
        self.add_account(config)
        return config


# Singleton instance
_broker_manager: Optional[BrokerManager] = None


def get_broker_manager(config_path: str = "config/brokers.yaml") -> BrokerManager:
    """Get or create singleton broker manager."""
    global _broker_manager
    if _broker_manager is None:
        _broker_manager = BrokerManager(config_path)
    return _broker_manager


def reset_broker_manager() -> None:
    """Reset singleton (mainly for testing)."""
    global _broker_manager
    _broker_manager = None
