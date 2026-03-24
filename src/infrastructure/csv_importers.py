"""CSV Importers for broker position exports.

Supports:
- Fidelity (positions_*.csv format)
- Schwab (future)
- E*Trade (future)
- Interactive Brokers (future)
"""

import csv
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ImportedPosition:
    """Standardized position from CSV import."""
    symbol: str
    description: str
    quantity: Decimal
    last_price: Optional[Decimal]
    current_value: Optional[Decimal]
    avg_cost_basis: Optional[Decimal]
    total_gain_loss_dollar: Optional[Decimal]
    total_gain_loss_percent: Optional[Decimal]
    account: str  # Account name/number
    account_type: str  # IRA, Individual, etc.
    asset_type: str  # Stock, Cash, etc.


class CSVImporter(ABC):
    """Abstract base for broker CSV importers."""

    @abstractmethod
    def parse(self, csv_path: str) -> List[ImportedPosition]:
        """Parse CSV file and return standardized positions."""
        pass

    @abstractmethod
    def can_parse(self, csv_path: str) -> bool:
        """Check if this importer can handle the given CSV."""
        pass


class FidelityCSVImporter(CSVImporter):
    """
    Import positions from Fidelity CSV export.

    Expected format: positions_MM-DD-YYYY.csv downloaded from Fidelity.com
    Columns: Account Number, Account Name, Symbol, Description, Quantity,
             Last Price, Last Price Change, Current Value, Today's Gain/Loss Dollar,
             Today's Gain/Loss Percent, Total Gain/Loss Dollar, Total Gain/Loss Percent,
             Percent Of Account, Cost Basis Total, Average Cost Basis, Type
    """

    # Column name mappings (Fidelity uses specific headers)
    COLUMN_MAP = {
        "symbol": "Symbol",
        "description": "Description",
        "quantity": "Quantity",
        "last_price": "Last Price",
        "current_value": "Current Value",
        "avg_cost_basis": "Average Cost Basis",
        "total_gain_loss_dollar": "Total Gain/Loss Dollar",
        "total_gain_loss_percent": "Total Gain/Loss Percent",
        "account_number": "Account Number",
        "account_name": "Account Name",
        "type": "Type",
    }

    def can_parse(self, csv_path: str) -> bool:
        """Check if this looks like a Fidelity export."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                sample = f.read(2000)
                # Look for Fidelity-specific indicators
                return (
                    "Fidelity" in sample or
                    "Account Number" in sample and "Symbol" in sample and "Description" in sample
                )
        except Exception:
            return False

    def parse(self, csv_path: str) -> List[ImportedPosition]:
        """
        Parse Fidelity positions CSV.

        Args:
            csv_path: Path to the CSV file

        Returns:
            List of ImportedPosition objects
        """
        positions = []
        path = Path(csv_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"Parsing Fidelity CSV: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            # Fidelity CSVs sometimes have a preamble or notes
            # Find the actual header row
            lines = f.readlines()

            # Find the header row (contains "Account Number")
            header_idx = 0
            for i, line in enumerate(lines):
                if "Account Number" in line:
                    header_idx = i
                    break

            # Parse from header row onwards
            reader = csv.DictReader(lines[header_idx:])

            for row in reader:
                try:
                    # Skip empty rows or cash positions without symbols
                    raw_symbol = row.get(self.COLUMN_MAP["symbol"], "")
                    if not raw_symbol:
                        continue
                    symbol = raw_symbol.strip()
                    if symbol in ["", "Pending activity"]:
                        continue

                    # Skip cash/money market positions (marked with **)
                    if "**" in symbol:
                        continue

                    position = self._parse_row(row)
                    if position:
                        positions.append(position)

                except Exception as e:
                    raw_sym = row.get(self.COLUMN_MAP["symbol"], "unknown")
                    sym_str = raw_sym.strip() if raw_sym else "unknown"
                    logger.warning(f"Failed to parse row for {sym_str}: {e}")
                    continue

        logger.info(f"Imported {len(positions)} positions from Fidelity CSV")
        return positions

    def _parse_row(self, row: Dict[str, str]) -> Optional[ImportedPosition]:
        """Parse a single CSV row into ImportedPosition."""

        # Extract symbol
        raw_symbol = row.get(self.COLUMN_MAP["symbol"], "")
        if not raw_symbol:
            return None
        symbol = raw_symbol.strip()

        # Clean up symbol (remove suffixes like "COM", "CL A", etc.)
        symbol = self._clean_symbol(symbol)

        # Extract description
        description = row.get(self.COLUMN_MAP["description"], "").strip()

        # Parse numeric fields (handle empty strings)
        quantity = self._parse_decimal(row.get(self.COLUMN_MAP["quantity"], ""))
        last_price = self._parse_decimal(row.get(self.COLUMN_MAP["last_price"], ""))
        current_value = self._parse_decimal(row.get(self.COLUMN_MAP["current_value"], ""))
        avg_cost_basis = self._parse_decimal(row.get(self.COLUMN_MAP["avg_cost_basis"], ""))
        total_gain_loss_dollar = self._parse_decimal(row.get(self.COLUMN_MAP["total_gain_loss_dollar"], ""))
        total_gain_loss_percent = self._parse_decimal(row.get(self.COLUMN_MAP["total_gain_loss_percent"], ""))

        # Account info
        account = row.get(self.COLUMN_MAP["account_name"], "").strip()
        account_type = self._extract_account_type(account)

        # Asset type
        asset_type = row.get(self.COLUMN_MAP["type"], "Cash").strip()

        return ImportedPosition(
            symbol=symbol,
            description=description,
            quantity=quantity,
            last_price=last_price,
            current_value=current_value,
            avg_cost_basis=avg_cost_basis,
            total_gain_loss_dollar=total_gain_loss_dollar,
            total_gain_loss_percent=total_gain_loss_percent,
            account=account,
            account_type=account_type,
            asset_type=asset_type,
        )

    def _clean_symbol(self, symbol: str) -> str:
        """Clean up symbol from Fidelity format."""
        # Remove common suffixes Fidelity adds
        suffixes_to_remove = [
            " COM", " COM CL A", " COM CL B", " COM USD0.001",
            " COMMON STOCK", " CLASS A", " INC", " CORP", " ETF",
            " TRUST", " (POST REV SPLIT)",
        ]

        for suffix in suffixes_to_remove:
            if suffix in symbol:
                symbol = symbol.replace(suffix, "")

        return symbol.strip()

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parse string to Decimal, handling currency formatting."""
        if not value or value.strip() in ["", "--"]:
            return None

        # Remove currency symbols, commas, + signs
        cleaned = value.replace("$", "").replace(",", "").replace("+", "").replace("%", "").strip()

        try:
            return Decimal(cleaned) if cleaned else None
        except Exception:
            return None

    def _extract_account_type(self, account_name: str) -> str:
        """Extract account type from account name."""
        account_upper = account_name.upper()

        if "IRA" in account_upper and "ROTH" in account_upper:
            return "ROTH_IRA"
        elif "IRA" in account_upper:
            return "TRADITIONAL_IRA"
        elif "JOINT" in account_upper:
            return "JOINT"
        elif "INDIVIDUAL" in account_upper:
            return "INDIVIDUAL"
        elif "CASH" in account_upper:
            return "CASH_MANAGEMENT"
        else:
            return "UNKNOWN"


class CSVImporterFactory:
    """Factory to detect and use appropriate CSV importer."""

    _importers = [
        FidelityCSVImporter(),
        # Add more importers here
    ]

    @classmethod
    def detect_and_parse(cls, csv_path: str) -> List[ImportedPosition]:
        """
        Auto-detect CSV format and parse.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of ImportedPosition

        Raises:
            ValueError: If format cannot be detected
        """
        for importer in cls._importers:
            if importer.can_parse(csv_path):
                logger.info(f"Detected format: {importer.__class__.__name__}")
                return importer.parse(csv_path)

        raise ValueError(
            f"Could not detect CSV format for {csv_path}. "
            f"Supported formats: Fidelity"
        )

    @classmethod
    def list_supported(cls) -> List[str]:
        """List supported broker formats."""
        return [i.__class__.__name__.replace("CSVImporter", "") for i in cls._importers]


# Convenience function
def import_positions(csv_path: str, broker: Optional[str] = None) -> List[ImportedPosition]:
    """
    Import positions from CSV file.

    Args:
        csv_path: Path to CSV file
        broker: Optional broker name (fidelity, schwab, etc.)
               If not provided, auto-detects format

    Returns:
        List of ImportedPosition
    """
    if broker:
        broker = broker.lower()
        if broker == "fidelity":
            return FidelityCSVImporter().parse(csv_path)
        else:
            raise ValueError(f"Unknown broker: {broker}. Supported: fidelity")

    # Auto-detect
    return CSVImporterFactory.detect_and_parse(csv_path)
