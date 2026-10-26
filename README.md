# FINTRAC 2026 - IDX80 Momentum Screener & Trade Planner

A high-performance Python scanner and competition trade planner built specifically for the **FINTRAC 2026** trading competition on **IDX Mobile**.

Designed for participants managing **Rp 200,000,000** capital who only check their phones a few times a day and need high-conviction momentum swing picks compliant with all tournament rules.

---

## 🏆 Competition Rules & Constraints Enforced

- **Universe:** Exclusively official **IDX80** constituent stocks (`idx80_tickers.txt`).
- **Initial Capital:** Rp 200,000,000.
- **Sizing & Allocation:** 1 Lot = 100 shares. Automatically rounds down to whole lots and splits capital across 2–3 high-conviction positions (~Rp 65M–100M each).
- **Rule Verification:** Tracks the mandatory **10 transactions** and **≥ 2 distinct tickers** rule.
- **Phased Exits:**
  - **TP1 (+4.5%):** Take profit on 50% of the position.
  - **TP2 (+8.5%):** Trail or exit remaining 50%.
  - **Stop-Loss (-2.8%):** Strict cut-loss to preserve capital.
  - All price targets are automatically aligned with official **IDX Price Fractions (Fraksi Harga BEI)**.

---

## 🛠️ Architecture & Build

- **Language:** Python 3.10+
- **HTTP Engine:** Lightweight `requests` client querying Yahoo Finance (`<TICKER>.JK`) with thread-pool concurrency.
- **Math & Indicators:** Zero heavy external TA-Lib dependencies; pure numpy/standard library implementations of:
  - Exponential Moving Average (EMA 9 & EMA 20)
  - Relative Strength Index (RSI 14) with momentum fitness scoring (50–72 sweet spot)
  - Relative Volume (RVOL 20-day baseline)
- **Local Ledger:** `trades.json` storing execution history, realized PnL, cash balance, and quota progress.
- **Reports:** Live terminal ANSI color table + markdown export (`signals.md`).

---

## 🚀 Quick Start & Usage

### 1. Installation
```bash
git clone https://github.com/zuraruldev/fintrax-scanner.git
cd fintrax-scanner
pip install -r requirements.txt # requires requests, numpy, pytest
```

### 2. Pre-Market Scan (08:30 WIB)
Run before market opens to get the top 3 high-momentum setups:
```bash
python3 screener.py scan
```
Options:
- `--capital <AMOUNT>`: Default `200000000` (Rp 200M).
- `--positions <N>`: Default `3` (split across 3 stocks).
- `--tickers <FILE>`: Path to ticker list (default: `idx80_tickers.txt`).

This command outputs a ranked terminal table and creates `signals.md` with exact lot sizes ready to be entered into IDX Mobile.

### 3. Midday Check (12:00 WIB)
Run during the midday break to evaluate Session 1 intraday volume and price action:
```bash
python3 screener.py midday
```

### 4. Logging Trades (Quota & Portfolio Tracking)
Whenever you execute a trade on your phone, log it locally:
```bash
# Example: Bought 133 lots of BDMN at Rp 5,000
python3 screener.py log buy BDMN 133 5000

# Example: Hit TP1 (+4.5%) - Sold half (66 lots) at Rp 5,225
python3 screener.py log sell BDMN 66 5225
```

### 5. Check Portfolio & Leaderboard Status
Check your total assets, remaining quota, and open positions:
```bash
python3 screener.py status
```

---

## 🧪 Testing

Run the automated test suite (18 unit and integration tests):
```bash
pytest
```
