# FINTRAC 2026 - Master Trading System & Strategy Guide

## 1. Executive Summary & Competition Framework

### The Playing Field
- **Competition:** FINTRAC 2026 Virtual Trading Tournament on **IDX Mobile**.
- **Initial Capital:** Rp 200.000.000 (Dua Ratus Juta Rupiah).
- **Duration:** 1-Week Trading Sprint (Senin – Jumat).
- **Scoring Metric:** **Total Assets** (Cash + Portfolio Market Value) at competition close.
- **Critical Constraints:**
  1. **Universe Restriction:** Strictly stocks within the **IDX80** index. Any trades outside IDX80 are disqualified.
  2. **Mandatory Quota:** Minimum **10 transactions** (Buys + Sells combined) during the competition week.
  3. **Diversification Minimum:** Trades must be executed on at least **2 distinct tickers**.
  4. **Execution Device:** 1 single authorized mobile device running IDX Mobile (manual tapping).
  5. **Trading Hours:**
     - Senin–Kamis: Sesi 1 (09.00–12.00 WIB), Sesi 2 (13.30–16.00 WIB)
     - Jumat: Sesi 1 (09.00–11.30 WIB), Sesi 2 (14.00–16.00 WIB)

---

## 2. Core Strategy: Momentum Swing for Leaderboard Dominance

### Why Not Scalping or 10-Stock Diversification?
Because you can only check your phone 2–3 times a day, fast intraday scalping is impossible. Conversely, spreading Rp 200M into 10–15 slow blue chips (like ASII or BBCA moving +0.5% a day) will leave you in the middle of the leaderboard.

In a 5-day tournament, the mathematical path to the top 3 is **Concentrated Momentum Swing**:
1. **Capital Allocation:** Divide Rp 200M into **2 or 3 explosive setups** (~Rp 65M–100M per position). A +5% move on Rp 66M generates +Rp 3.300.000 to your total assets.
2. **Quota Pacing Plan:** Front-load trades on **Monday through Wednesday**. Log 6–8 trades early via phased entries and partial exits. This ensures the 10-trade quota is achieved by Wednesday, leaving you free to ride winning runners on Thursday and Friday without pressure.
3. **Phased Take-Profit Execution:**
   - **TP1 (+4.5%):** Sell 50% of the position. This locks in profit, reduces risk to break-even, and immediately adds a trade count toward the 10-trade requirement.
   - **TP2 (+8.5%):** Hold or trail the remaining 50% into the end of the day or week.
4. **Strict Capital Preservation:** Cut losses immediately at **-2.8%** (around 3–5 ticks down). If a breakout fails, cut it fast and reallocate.
5. **Overnight Rule:** Hold winning momentum stocks overnight into the next day's opening gap. Liquidate stagnant or losing positions before the 16.00 WIB market close.

---

## 3. System Architecture & Build

The project is built as a modular, lightweight Python suite located at `/home/zura/fintrac_screener`. It avoids heavy bloated libraries (like TA-Lib or heavy pandas installations) so it runs in ~2 seconds with 100% reliability.

### Directory Structure
```
fintrac_screener/
├── screener.py                  # CLI Entrypoint (scan, midday, log, status)
├── idx80_tickers.txt            # Locked list of 80 IDX80 constituents
├── pyproject.toml               # Test configuration
├── requirements.txt             # dependencies (requests, numpy, pytest)
├── fintrac_screener/
│   ├── __init__.py
│   ├── universe.py              # Ticker parser, normalizer, and validator
│   ├── market_data.py           # Multi-threaded Yahoo Finance chart parser
│   ├── indicators.py            # EMA, RSI, RVOL, and Momentum scoring
│   ├── strategy.py              # Lot sizing (100 shares/lot) & Fraksi BEI
│   ├── trade_tracker.py         # JSON ledger, quota validator, realized PnL
│   └── reporter.py              # ANSI terminal styling & signals.md generator
└── tests/                       # 18 automated unit and integration tests
```

### Technical Indicators & Scoring Math
1. **Relative Volume (RVOL):**
   $$\text{RVOL} = \frac{\text{Volume}_{\text{today}}}{\text{Average Volume}_{\text{past 20 days}}}$$
   Stocks with $\text{RVOL} \ge 1.3\text{x}$ indicate institutional accumulation or retail breakout surge.
2. **Trend Alignment (EMA 9 & EMA 20):**
   Exponential Moving Averages calculate short-term momentum. A valid bullish breakout requires:
   $$\text{Price} \ge \text{EMA}_9 \ge \text{EMA}_{20}$$
3. **RSI(14) Momentum Sweet Spot:**
   - RSI between **50 and 72** receives maximum fitness score (continuation momentum).
   - RSI $> 72$ receives a penalty for extreme overbought risk.
4. **Composite Score Formula:**
   $$\text{Score} = 0.35 \times \text{RVOL}_{\text{scaled}} + 0.25 \times \text{Trend Bonus} + 0.20 \times \text{Price \% Change} + 0.20 \times \text{RSI Fitness}$$
5. **IDX Price Fractions (Fraksi Harga BEI):**
   All calculated stop-losses and profit targets automatically round to legal IDX tick sizes:
   - Price $< 200$: 1 tick = Rp 1
   - Price $200 - < 500$: 1 tick = Rp 2
   - Price $500 - < 2.000$: 1 tick = Rp 5
   - Price $2.000 - < 5.000$: 1 tick = Rp 10
   - Price $\ge 5.000$: 1 tick = Rp 25
6. **Lot Calculation:**
   $$\text{Lots} = \lfloor \frac{\text{Allocated Capital}}{\text{Price} \times 100} \rfloor$$
   Guarantees zero fractional shares and exact Indonesian standard lot sizing (1 Lot = 100 lembar).

---

## 4. Daily Operating Routine (How to Use)

### Checkpoint 1: Morning Pre-Market Scan (08.30 – 08.50 WIB)
Run the scanner on your computer:
```bash
cd /home/zura/fintrac_screener
python3 screener.py scan
```
- The tool scans all 80 IDX80 stocks in parallel in ~2 seconds.
- It displays the top setups on your terminal and automatically creates `signals.md`.
- Open `signals.md` or look at your terminal. Pick the top 2 or 3 setups.
- At **09.00 WIB**, open your IDX Mobile app and submit Buy orders with the exact **Lots** listed.

#### 💡 Action Guide: How to Act on the Scan Output
When you run `python3 screener.py scan` and see the **TOP MOMENTUM SETUPS** table:
```
Ticker     Price      Lots       TP1 (+4.5%)    TP2 (+8.5%)    SL (-2.8%)     RVOL     RSI   
--------------------------------------------------------------------------------
TLKM.JK    Rp 2.250   296 Lots   Rp 2.350       Rp 2.440       Rp 2.190       3.0    x 66.2  
BMRI.JK    Rp 3.910   170 Lots   Rp 4.090       Rp 4.240       Rp 3.800       2.1    x 62.9  
BBRI.JK    Rp 2.910   229 Lots   Rp 3.040       Rp 3.160       Rp 2.830       1.2    x 57.8  
```
Here is your exact execution flow:
1. **Open IDX Mobile:** Login to your registered account on your authorized phone.
2. **Place the Buy Orders:**
   - Tap Buy -> search `TLKM` -> input **296 Lots** -> price **2250**.
   - Tap Buy -> search `BMRI` -> input **170 Lots** -> price **3910**.
   - Tap Buy -> search `BBRI` -> input **229 Lots** -> price **2910**.
3. **Log the Trades in the System:** Once your orders are filled in the app, sync them locally so your 10-trade quota and cash are tracked:
   ```bash
   python3 screener.py log buy TLKM 296 2250
   python3 screener.py log buy BMRI 170 3910
   python3 screener.py log buy BBRI 229 2910
   ```
4. **Setting Exit Triggers:**
   - Note the **TP1** and **SL** prices from the table on your phone notes or order book.
   - When a stock climbs to **TP1** (e.g. TLKM reaches 2350), sell half (148 lots) to bank profit and log it:
     `python3 screener.py log sell TLKM 148 2350`
   - If a stock drops to **SL** (e.g. TLKM hits 2190), exit immediately to preserve capital:
     `python3 screener.py log sell TLKM 296 2190`

### Checkpoint 2: Midday Break Review (12.00 – 13.20 WIB)
During the midday session break, check if any of your stocks hit TP1 or if fresh afternoon setups appeared:
```bash
python3 screener.py midday
```
- If a stock hit **TP1 (+4.5%)**, tap **Sell** on your phone for **half** of your lots.
- Record the execution:
  ```bash
  python3 screener.py log sell <TICKER> <LOTS> <PRICE>
  ```

### Checkpoint 3: Pre-Close Decision (15.30 – 15.55 WIB)
- If your stock is strongly up and closing near the high of the day on high volume, **hold it overnight** to capture the next morning gap-up.
- If a stock is stagnant (0% to -1%) or breaking down toward stop-loss (-2.8%), **sell it before 16.00 WIB** to free up cash for tomorrow morning's scan.
- Log every executed sell:
  ```bash
  python3 screener.py log sell <TICKER> <LOTS> <PRICE>
  ```

### Checkpoint 4: Checking Leaderboard Status & Quota Progress
At any time, run:
```bash
python3 screener.py status
```
This displays:
- **Total Assets:** Your official leaderboard score (Cash + Current Portfolio Value).
- **Trade Quota Progress:** Exact count towards the 10-trade requirement (e.g. `6 / 10 ([WAIT] Need 4 more trades)` or `✅ COMPLETED`).
- **Unique Tickers Traded:** Must be $\ge 2$.
- **Realized PnL:** Cash profits banked into your account.
- **Open Positions:** Lots held, average buy price, and total invested cost.

---

## 5. Command Reference Cheat Sheet

| Action | Command | Purpose |
|:-------|:--------|:--------|
| **Morning Scan** | `python3 screener.py scan` | Scans 80 tickers, produces top 3 setups and `signals.md`. |
| **Midday Scan** | `python3 screener.py midday` | Scans recent intraday candles during session break. |
| **Custom Split** | `python3 screener.py scan --positions 2` | Allocates Rp 200M into 2 positions (~Rp 100M each). |
| **Log Buy** | `python3 screener.py log buy BDMN 133 5000` | Records purchase of 133 lots BDMN at Rp 5.000. |
| **Log Sell** | `python3 screener.py log sell BDMN 66 5225` | Records sale of 66 lots BDMN at Rp 5.225. |
| **Check Status**| `python3 screener.py status` | Shows Total Assets, remaining quota, and portfolio. |
| **Run Tests** | `pytest` | Runs all 18 unit tests to verify system integrity. |

---

## 6. How to Update the Locked IDX80 Ticker List

The committee may provide their own specific spreadsheet of the locked 80 tickers. 
To update the screener's universe:
1. Open `/home/zura/fintrac_screener/idx80_tickers.txt` in any text editor.
2. Paste the 80 tickers, one per line (e.g. `BBCA`, `BBRI`, `BMRI`, etc.).
3. Save the file. The screener will automatically read and validate against your updated list on the next run.
