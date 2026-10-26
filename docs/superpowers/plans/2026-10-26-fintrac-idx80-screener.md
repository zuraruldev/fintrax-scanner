# FINTRAC 2026 IDX80 Screener & Trade Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust, dependency-light Python CLI screener and quota manager for the FINTRAC 2026 IDX Mobile competition, screening IDX80 momentum breakouts and generating phone-ready lot sizes and trade targets for a Rp 200,000,000 portfolio.

**Architecture:** A modular Python package with pure functions for technical indicator calculation (EMA, RSI, RVOL), a resilient Yahoo Finance HTTP parser, an allocation and risk-management strategy engine computing lot counts (100 shares/lot) and phased profit exits, a local JSON trade ledger tracking the 10-trade quota across >=2 tickers, and a CLI producing both terminal tables and a phone-readable `signals.md`.

**Tech Stack:** Python 3.12+, `requests`, `numpy`, `pytest`.

**Spec:** `/home/zura/docs/superpowers/specs/2026-10-26-fintrac-idx80-screener-design.md`

## Global Constraints
- **Universe Restriction:** Strictly IDX80 constituents formatted as `<TICKER>.JK` (configurable via `idx80_tickers.txt`).
- **Initial Capital:** Fixed at Rp 200,000,000 default.
- **Lot Sizing:** 1 lot = 100 shares. Round down to integer lots; zero fractional shares allowed.
- **Quota Rule:** Minimum 10 transactions (buys + sells) across at least 2 distinct tickers.
- **Risk Parameters:** Phased take-profit at +4.5% (TP1) and +8.5% (TP2); strict stop loss at -2.8%.
- **Zero Heavy Dependencies:** No pandas or heavy TA-Lib requirements; use standard library plus `requests` and `numpy`.

## Review Focus
1. **Network failure or missing ticker data:** If Yahoo Finance returns 404 or empty candles for a ticker, the screener must skip it gracefully without crashing or aborting the rest of the scan. (Pinned to Task 2).
2. **Zero or low volume division:** When calculating RVOL where 20-day average volume is 0, return 0.0 without triggering ZeroDivisionError. (Pinned to Task 3).
3. **Price lower than cash per position:** If stock price exceeds total available cash or position budget, lot sizing returns 0 lots instead of throwing an exception. (Pinned to Task 4).
4. **Duplicate trade logging:** Recording multiple buy/sell entries on the same ticker correctly updates average buy price, current open lots, and increments total transaction count. (Pinned to Task 5).
5. **Partial sell calculation:** Selling a portion of lots (e.g. 50% for TP1) calculates realized PnL on those lots and keeps remaining lots in open portfolio. (Pinned to Task 5).

---

### Task 1: Project Setup, Constituent Universe & Shared Types

**Files:**
- Create: `fintrac_screener/__init__.py`
- Create: `fintrac_screener/universe.py`
- Create: `idx80_tickers.txt`
- Test: `tests/test_universe.py`

**Interfaces:**
- Produces: `load_tickers(file_path: str = "idx80_tickers.txt") -> list[str]`
- Produces: `is_valid_ticker(ticker: str, allowed_tickers: list[str]) -> bool`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_universe.py
import os
import pytest
from fintrac_screener.universe import load_tickers, is_valid_ticker

def test_load_tickers_default(tmp_path):
    sample_file = tmp_path / "tickers.txt"
    sample_file.write_text("BBCA\nBBRI\n# comment\nBMRI\n\n")
    tickers = load_tickers(str(sample_file))
    assert tickers == ["BBCA.JK", "BBRI.JK", "BMRI.JK"]

def test_is_valid_ticker():
    allowed = ["BBCA.JK", "BBRI.JK"]
    assert is_valid_ticker("BBCA", allowed) is True
    assert is_valid_ticker("BBCA.JK", allowed) is True
    assert is_valid_ticker("GOTO", allowed) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_universe.py -v`
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Implement universe loader and default `idx80_tickers.txt`**

Implement `load_tickers` and `is_valid_ticker` in `fintrac_screener/universe.py`. Normalize symbols by stripping whitespace, uppercase conversion, and appending `.JK` if missing. Create `idx80_tickers.txt` containing the 80 IDX80 constituent tickers (BBCA, BBRI, BMRI, BBNI, ASII, TLKM, AMMN, ADRO, BRPT, BUKA, GOTO, CPIN, ICBP, INDF, KLBF, MAPI, PGAS, PTBA, SMGR, UNTR, UNVR, etc.).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_universe.py -v`
Expected: PASS

- [ ] **Step 5: Verify default `idx80_tickers.txt` has 80 tickers**

Run: `python3 -c "from fintrac_screener.universe import load_tickers; t = load_tickers('idx80_tickers.txt'); assert len(t) == 80, f'Count: {len(t)}'"`
Expected: Clean pass with count == 80.

---

### Task 2: Yahoo Finance Market Data Client

**Files:**
- Create: `fintrac_screener/market_data.py`
- Test: `tests/test_market_data.py`

**Interfaces:**
- Consumes: Ticker string (e.g. `"BBCA.JK"`)
- Produces: `fetch_candles(ticker: str, interval: str = "1d", range_str: str = "3mo") -> dict | None` returning dict with keys: `dates`, `opens`, `highs`, `lows`, `closes`, `volumes`, `current_price`

- [ ] **Step 1: Write the failing test with mocked responses and review focus edge cases**

```python
# tests/test_market_data.py
import pytest
from unittest.mock import patch, MagicMock
from fintrac_screener.market_data import fetch_candles, parse_yahoo_chart_response

def test_parse_yahoo_chart_response_valid():
    sample_payload = {
        "chart": {
            "result": [{
                "meta": {"regularMarketPrice": 10200.0},
                "timestamp": [1700000000, 1700086400],
                "indicators": {
                    "quote": [{
                        "open": [10000.0, 10100.0],
                        "high": [10200.0, 10300.0],
                        "low": [9950.0, 10050.0],
                        "close": [10100.0, 10200.0],
                        "volume": [50000000, 65000000]
                    }]
                }
            }],
            "error": None
        }
    }
    result = parse_yahoo_chart_response(sample_payload)
    assert result is not None
    assert result["current_price"] == 10200.0
    assert len(result["closes"]) == 2
    assert result["volumes"][-1] == 65000000

def test_parse_yahoo_chart_response_error_or_empty():
    assert parse_yahoo_chart_response({"chart": {"result": None, "error": {"code": "Not Found"}}}) is None
    assert parse_yahoo_chart_response({}) is None

@patch("fintrac_screener.market_data.requests.get")
def test_fetch_candles_handles_network_error(mock_get):
    mock_get.side_effect = Exception("Connection error")
    assert fetch_candles("BBCA.JK") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_market_data.py -v`
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Implement `fintrac_screener/market_data.py`**

Implement `parse_yahoo_chart_response(data: dict) -> dict | None` to filter out None/NaN entries and extract float series for open/high/low/close/volume. Implement `fetch_candles(ticker: str, interval: str = "1d", range_str: str = "3mo") -> dict | None` with `requests.get` using custom User-Agent, timeout=8s, and graceful exception handling.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_market_data.py -v`
Expected: PASS

---

### Task 3: Technical Indicators & Momentum Scoring Engine

**Files:**
- Create: `fintrac_screener/indicators.py`
- Test: `tests/test_indicators.py`

**Interfaces:**
- Consumes: Numerical series (`closes: list[float]`, `volumes: list[int]`)
- Produces:
  - `compute_ema(series: list[float], period: int) -> list[float]`
  - `compute_rsi(closes: list[float], period: int = 14) -> float`
  - `compute_rvol(volumes: list[int], window: int = 20) -> float`
  - `compute_momentum_score(candles: dict) -> dict` returning `{'score': float, 'rvol': float, 'rsi': float, 'ema_trend': bool, 'change_1d': float, 'change_5d': float}`

- [ ] **Step 1: Write the failing test including Review Focus zero-volume case**

```python
# tests/test_indicators.py
import pytest
from fintrac_screener.indicators import compute_ema, compute_rsi, compute_rvol, compute_momentum_score

def test_compute_ema():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    ema = compute_ema(prices, period=3)
    assert len(ema) == len(prices)
    assert ema[-1] > ema[0]

def test_compute_rsi():
    # Continual up move -> high RSI
    closes = [float(100 + i * 2) for i in range(25)]
    rsi = compute_rsi(closes, period=14)
    assert rsi > 70.0

def test_compute_rvol_and_zero_division():
    vols = [1000] * 20 + [2500]
    assert compute_rvol(vols, window=20) == 2.5
    # Zero volume handling (Review Focus #2)
    assert compute_rvol([0] * 21, window=20) == 0.0

def test_compute_momentum_score():
    closes = [100.0 + i for i in range(30)]
    volumes = [10000] * 29 + [30000]
    candles = {
        "closes": closes,
        "volumes": volumes,
        "highs": [c + 1 for c in closes],
        "lows": [c - 1 for c in closes],
        "opens": closes,
        "current_price": closes[-1]
    }
    metrics = compute_momentum_score(candles)
    assert metrics["score"] > 0
    assert metrics["rvol"] >= 2.5
    assert metrics["ema_trend"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_indicators.py -v`
Expected: FAIL

- [ ] **Step 3: Implement indicators in `fintrac_screener/indicators.py`**

Implement standard EMA formula ($Multiplier = 2 / (period + 1)$), Wilder's RSI smoothing, and Relative Volume ($Volume_{today} / Mean(Volume_{prev20})$). Implement composite momentum score:
$Score = 0.4 \times RVOL + 0.3 \times TrendBonus + 0.2 \times (1D\% + 5D\%) + 0.1 \times RSI\_Fitness$ where $RSI\_Fitness$ peaks in the 55–70 range.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_indicators.py -v`
Expected: PASS

---

### Task 4: Position Sizing & Swing Trade Setup Generator

**Files:**
- Create: `fintrac_screener/strategy.py`
- Test: `tests/test_strategy.py`

**Interfaces:**
- Consumes: Scored candidates list, `capital: float = 200_000_000.0`, `num_positions: int = 3`
- Produces: `generate_trade_setups(scored_stocks: list[dict], capital: float = 200_000_000, num_positions: int = 3) -> list[dict]`
  Each setup returns: `ticker`, `price`, `target_lots`, `allocated_capital`, `tp1`, `tp2`, `stop_loss`, `score`, `rvol`, `rsi`

- [ ] **Step 1: Write the failing test with 100-share lot constraints & price exceeding capital edge case**

```python
# tests/test_strategy.py
import pytest
from fintrac_screener.strategy import calculate_lot_size, generate_trade_setups

def test_calculate_lot_size():
    # Capital: 66,666,666 IDR. Price = 9,000 IDR per share.
    # 1 lot = 100 shares = 900,000 IDR.
    # Expected lots = 66,666,666 // 900,000 = 74 lots.
    lots, actual_capital = calculate_lot_size(price=9000.0, allocated_cash=66_666_666.0)
    assert lots == 74
    assert actual_capital == 74 * 100 * 9000.0
    assert actual_capital <= 66_666_666.0

def test_calculate_lot_size_price_too_high():
    # Stock price higher than allocated cash
    lots, actual_capital = calculate_lot_size(price=100_000.0, allocated_cash=5000.0)
    assert lots == 0
    assert actual_capital == 0.0

def test_generate_trade_setups():
    candidates = [
        {"ticker": "BBCA.JK", "current_price": 10000.0, "score": 85.0, "rvol": 2.1, "rsi": 62.0},
        {"ticker": "BBRI.JK", "current_price": 5000.0, "score": 80.0, "rvol": 1.8, "rsi": 58.0},
        {"ticker": "BMRI.JK", "current_price": 6000.0, "score": 75.0, "rvol": 1.5, "rsi": 55.0},
    ]
    setups = generate_trade_setups(candidates, capital=200_000_000.0, num_positions=3)
    assert len(setups) == 3
    # Check phased TP and SL
    bbca = setups[0]
    assert bbca["target_lots"] > 0
    assert bbca["tp1"] == pytest.approx(10000.0 * 1.045, rel=1e-2)
    assert bbca["tp2"] == pytest.approx(10000.0 * 1.085, rel=1e-2)
    assert bbca["stop_loss"] == pytest.approx(10000.0 * 0.972, rel=1e-2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_strategy.py -v`
Expected: FAIL

- [ ] **Step 3: Implement strategy calculations in `fintrac_screener/strategy.py`**

Implement `calculate_lot_size(price: float, allocated_cash: float) -> tuple[int, float]` with strict `int(allocated_cash // (price * 100))`. Implement `generate_trade_setups(...)` calculating TP1 (+4.5%), TP2 (+8.5%), and Stop-Loss (-2.8%) rounded to standard IDX tick increments.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_strategy.py -v`
Expected: PASS

---

### Task 5: Trade Ledger & Quota Management Module

**Files:**
- Create: `fintrac_screener/trade_tracker.py`
- Test: `tests/test_trade_tracker.py`

**Interfaces:**
- Consumes: Trade log entries (action: buy/sell, ticker, lots, price, timestamp)
- Produces: `TradeTracker` class with methods:
  - `record_trade(action: str, ticker: str, lots: int, price: float) -> dict`
  - `get_status(current_prices: dict[str, float] = None) -> dict` returning `total_trades`, `unique_tickers`, `quota_completed`, `cash`, `portfolio_value`, `total_assets`, `positions`

- [ ] **Step 1: Write the failing test including partial sell and duplicate trade tracking**

```python
# tests/test_trade_tracker.py
import pytest
from fintrac_screener.trade_tracker import TradeTracker

def test_trade_tracker_buy_and_partial_sell(tmp_path):
    ledger_file = tmp_path / "trades.json"
    tracker = TradeTracker(file_path=str(ledger_file), initial_capital=200_000_000.0)

    # 1. Buy 100 lots of BBCA at 10,000 (Cost = 100,000,000)
    tracker.record_trade("buy", "BBCA", 100, 10000.0)
    status = tracker.get_status({"BBCA": 10000.0})
    assert status["total_trades"] == 1
    assert status["cash"] == 100_000_000.0
    assert status["positions"]["BBCA"]["lots"] == 100

    # 2. Sell 50 lots of BBCA at 10,500 (Proceeds = 50 * 100 * 10,500 = 52,500,000)
    tracker.record_trade("sell", "BBCA", 50, 10500.0)
    status = tracker.get_status({"BBCA": 10500.0})
    assert status["total_trades"] == 2
    assert status["positions"]["BBCA"]["lots"] == 50
    assert status["cash"] == 152_500_000.0
    # Total assets = Cash (152.5M) + Open (50 * 100 * 10,500 = 52.5M) = 205,000,000
    assert status["total_assets"] == 205_000_000.0

def test_trade_tracker_quota_verification(tmp_path):
    ledger_file = tmp_path / "trades.json"
    tracker = TradeTracker(file_path=str(ledger_file))
    # Minimum 10 trades on at least 2 tickers
    for i in range(5):
        tracker.record_trade("buy", "BBCA", 1, 10000.0)
        tracker.record_trade("sell", "BBCA", 1, 10000.0)
    status = tracker.get_status()
    # 10 trades on only 1 ticker -> quota NOT completed
    assert status["total_trades"] == 10
    assert status["quota_completed"] is False

    tracker.record_trade("buy", "BBRI", 1, 5000.0)
    status = tracker.get_status()
    # 11 trades across 2 tickers -> quota completed
    assert status["unique_tickers"] == 2
    assert status["quota_completed"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_trade_tracker.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `TradeTracker` in `fintrac_screener/trade_tracker.py`**

Implement JSON persistence, position FIFO/weighted average tracking, cash balance updates, and validation against the 10-trade and >=2-ticker rules.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_trade_tracker.py -v`
Expected: PASS

---

### Task 6: CLI Runner, Formatted Terminal Output & `signals.md` Generator

**Files:**
- Create: `screener.py`
- Create: `fintrac_screener/reporter.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- CLI Commands:
  - `python screener.py scan [--capital 200000000] [--positions 3]`
  - `python screener.py midday`
  - `python screener.py log <buy|sell> <ticker> <lots> <price>`
  - `python screener.py status`
- Produces: `signals.md` containing formatted markdown report of setups and portfolio status.

- [ ] **Step 1: Write CLI and reporter tests**

```python
# tests/test_cli.py
import os
import subprocess
import pytest
from fintrac_screener.reporter import render_markdown_report

def test_render_markdown_report():
    setups = [{
        "ticker": "BBCA.JK",
        "current_price": 10200.0,
        "target_lots": 65,
        "allocated_capital": 66300000.0,
        "tp1": 10650.0,
        "tp2": 11050.0,
        "stop_loss": 9925.0,
        "score": 88.5,
        "rvol": 2.4,
        "rsi": 64.2
    }]
    status = {
        "total_trades": 4,
        "unique_tickers": 2,
        "quota_completed": False,
        "cash": 133700000.0,
        "total_assets": 200000000.0
    }
    md = render_markdown_report(setups, status)
    assert "# FINTRAC 2026 - Trading Setup & Signals" in md
    assert "BBCA.JK" in md
    assert "65 Lots" in md
    assert "4 / 10" in md

def test_cli_help():
    result = subprocess.run(["python3", "screener.py", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "scan" in result.stdout
    assert "log" in result.stdout
    assert "status" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Implement reporter and CLI entrypoint**

In `fintrac_screener/reporter.py`, format setup cards with clean markdown tables and colored ANSI terminal formatting.
In `screener.py`, use `argparse` to wire `scan`, `midday`, `log`, and `status`. Ensure `scan` writes `signals.md` in the working directory.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

---

### Task 7: End-to-End Verification with Live Market Test

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All unit and integration tests PASS.

- [ ] **Step 2: Execute live scan on a 5-ticker sample**

Run: `python3 -c "from fintrac_screener.universe import load_tickers; from fintrac_screener.market_data import fetch_candles; from fintrac_screener.indicators import compute_momentum_score; c = fetch_candles('BBCA.JK'); m = compute_momentum_score(c); print('BBCA Live Score:', m['score'])"`
Expected: Fetches actual Yahoo Finance quote and prints positive momentum score without errors.

- [ ] **Step 3: Run `python3 screener.py status` and verify clean initialization**

Run: `python3 screener.py status`
Expected: Shows starting cash Rp 200,000,000, 0/10 trades completed, and clean formatting.
