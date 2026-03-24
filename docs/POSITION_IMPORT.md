# User Position Import Options

## Problem

Users shouldn't have to manually type positions like "I have 100 shares of AAPL at $150 cost basis". This is:
- Error-prone
- Time-consuming
- Gets out of sync quickly

## Solutions (Ranked by Preference)

### 1. **Direct Broker API** (Best - Automated)

Connect to broker APIs to sync positions automatically.

**Supported:**
- **Alpaca** - Full API access to positions
- **OKX** - Full API access to positions
- **Interactive Brokers** (future)
- **Coinbase** (future)

**User flow:**
```
1. User enters API keys in config/.env
2. System periodically syncs positions
3. Always up-to-date for trading decisions
```

**Implementation:**
```python
# src/infrastructure/portfolio_sync.py

class PortfolioSync:
    """Syncs positions from broker APIs."""

    async def sync_from_alpaca(self, user_id: str) -> Portfolio:
        broker = AlpacaBroker(api_key=..., secret_key=...)
        positions = await broker.get_positions()
        await self.save_to_db(user_id, positions)

    async def sync_from_okx(self, user_id: str) -> Portfolio:
        broker = OKXBroker(api_key=..., secret=..., passphrase=...)
        positions = await broker.get_positions()
        await self.save_to_db(user_id, positions)
```

---

### 2. **CSV Import** (Good - One-time bulk)

Most brokers allow exporting positions to CSV.

**Supported brokers with CSV export:**
| Broker | Export Path | Format |
|--------|-------------|--------|
| Schwab | Account → Positions → Export | CSV |
| Fidelity | Positions → Download | CSV |
| E*Trade | Portfolio → Export | CSV |
| Webull | Account → Export | CSV |
| TD Ameritrade | Account → History → Export | CSV |
| Robinhood | Account → Statements | PDF (harder) |

**User flow:**
```
1. User exports CSV from broker
2. Runs: traderclaw import-positions --file positions.csv --broker schwab
3. System parses and saves
```

**Implementation:**
```python
# src/infrastructure/csv_importers.py

class SchwabCSVImporter:
    """Import positions from Schwab CSV export."""

    COLUMN_MAPPING = {
        "Symbol": "symbol",
        "Description": "name",
        "Quantity": "quantity",
        "Price": "current_price",
        "Cost Basis": "avg_entry_price",
    }

    def parse(self, csv_path: str) -> List[Position]:
        df = pd.read_csv(csv_path)
        positions = []
        for _, row in df.iterrows():
            positions.append(Position(
                symbol=row["Symbol"],
                quantity=float(row["Quantity"]),
                avg_entry_price=float(row["Cost Basis"]),
                current_price=float(row["Price"]),
            ))
        return positions


class FidelityCSVImporter:
    """Import positions from Fidelity export."""
    # Similar implementation with different column mapping
```

---

### 3. **Screenshot OCR** (Interesting - Visual)

User takes screenshot of brokerage app, we extract positions.

**Pros:**
- Works with ANY broker
- No API keys needed
- Very convenient for users

**Cons:**
- OCR can be error-prone
- Requires image processing
- Privacy concerns with screenshots

**Implementation:**
```python
# src/infrastructure/screenshot_ocr.py

import pytesseract
from PIL import Image
import cv2
import numpy as np

class PositionScreenshotOCR:
    """Extract positions from brokerage app screenshots."""

    SUPPORTED_LAYOUTS = ["alpaca", "robinhood", "webull", "schwab"]

    def extract_positions(self, image_path: str, broker_app: str) -> List[Position]:
        """
        Extract positions from screenshot.

        Uses template matching for known broker apps,
        then OCR to extract text.
        """
        img = cv2.imread(image_path)

        # Apply template matching for known layout
        if broker_app in self.SUPPORTED_LAYOUTS:
            roi = self._extract_region_of_interest(img, broker_app)
        else:
            roi = img

        # OCR the position table
        text = pytesseract.image_to_string(roi)

        # Parse positions from text
        return self._parse_positions_from_text(text)

    def _extract_region_of_interest(self, img: np.ndarray, app: str) -> np.ndarray:
        """Extract the positions table region based on app layout."""
        # Known coordinates for position tables in different apps
        roi_map = {
            "robinhood": (100, 300, 800, 1200),  # x, y, w, h
            "webull": (50, 250, 900, 1100),
            # etc.
        }
        x, y, w, h = roi_map[app]
        return img[y:y+h, x:x+w]
```

---

### 4. **Manual Entry UI** (Fallback - Simple)

Simple form for users without API access or CSV exports.

**CLI flow:**
```bash
$ traderclaw add-position
Symbol: AAPL
Quantity: 100
Average Entry Price: 150.00
Date Acquired: 2024-01-15

Position added: 100 shares AAPL @ $150
```

**Or via YAML:**
```yaml
# config/positions.yaml
positions:
  - symbol: AAPL
    quantity: 100
    avg_entry_price: 150.00
    date_acquired: 2024-01-15
    broker: schwab

  - symbol: BTC
    quantity: 0.5
    avg_entry_price: 40000.00
    date_acquired: 2024-02-01
    broker: coinbase
```

---

### 5. **Plaid / Account Aggregation** (Future - Multi-broker)

Use Plaid or similar to connect to multiple brokers.

**Pros:**
- One connection, multiple brokers
- Standardized data format

**Cons:**
- Not all brokers supported
- Additional cost
- More complex permissions

---

## Recommended Implementation Priority

### Phase 1: API + Manual
1. ✅ Alpaca API sync (already implemented)
2. ✅ OKX API sync (already implemented)
3. Simple YAML/CLI manual entry for other positions

### Phase 2: CSV Import
4. Implement CSV parsers for top 5 brokers (Schwab, Fidelity, E*Trade, etc.)

### Phase 3: Convenience Features
5. Screenshot OCR (cool factor, broad compatibility)
6. Plaid integration (if needed)

---

## Updated User Flow

### For Alpaca/OKX Users (API)
```bash
# One-time setup
traderclaw config --broker alpaca --api-key xxx --secret yyy

# Positions sync automatically
$ traderclaw status
Portfolio synced from Alpaca:
  - AAPL: 100 shares @ $150 (current: $185.50, +23.7%)
  - TSLA: 50 shares @ $200 (current: $175.20, -12.4%)

# Now query without typing positions
$ traderclaw ask "Should I sell AAPL?"
# System already knows: 100 shares, +23.7%, $150 cost basis
```

### For Other Broker Users (CSV)
```bash
# Export CSV from Schwab/Fidelity/etc
# Then import
traderclaw import-positions positions.csv --broker schwab

# Now query
$ traderclaw ask "Should I sell AAPL?"
```

### For Manual Entry
```bash
# Quick add
traderclaw add-position --symbol AAPL --qty 100 --entry 150

# Or edit YAML directly
vim config/positions.yaml
```

---

## Code Implementation Plan

Let me implement the CSV importer and improve the position service to support multiple sources:

1. `src/infrastructure/portfolio_sync.py` - Unified position sync
2. `src/infrastructure/csv_importers.py` - Broker CSV parsers
3. Update `orchestrator.py` to use synced positions

**Should I implement these components?**