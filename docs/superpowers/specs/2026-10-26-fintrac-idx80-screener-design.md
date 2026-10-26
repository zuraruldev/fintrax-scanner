# Design: FINTRAC 2026 IDX80 Momentum Screener & Trade Planner

## 1. Intent and Why
The user is participating in **FINTRAC 2026**, a 1-week virtual stock trading competition on IDX Mobile with an initial capital of **Rp 200,000,000**. The objective is to maximize **Total Assets** (Cash + Portfolio Value) to rank top of the leaderboard.

Because the user cannot monitor charts continuously and can only check their mobile device a few times per day, they need a high-conviction momentum swing screener and trade planner that filters the market before open (08:30 WIB) and at midday break (12:00 WIB) to produce 2–3 clear trade ideas with exact lot sizing, entry levels, profit targets, and stop-loss points.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **IDX80 Universe Compliance:** Strictly screen and track tickers belonging to the official IDX80 index list locked for the competition.
- **Momentum & Volume Breakout Ranking:** Score and rank all 80 stocks daily based on volume expansion (Relative Volume > 1.3x 20-day average), price breakout / trend strength (EMA9 > EMA20, RSI 50–70), and short-term volatility.
- **Actionable Execution Cards:** For top candidates, output exact recommendations:
  - Suggested Entry Price / Range
  - Stop-loss price (typically -2.5% to -3.5%)
  - Target take-profit price (+5% to +10%)
  - Position sizing in Lots (1 lot = 100 shares) based on capital allocation (~Rp 65M–100M per stock).
- **Competition Rule Tracker:** Provide a simple local tracker (e.g. `trades.json`) to log executed trades, ensuring the user hits the minimum 10 transactions across at least 2 distinct tickers.

### Non-Goals
- **Automated Order Placement:** IDX Mobile does not expose an open execution API and requires single-device manual authentication; the tool will not attempt automated execution.
- **Sub-second Scalping / Websocket Feeds:** The user trades a swing style with 3 daily check-ins; tick-level scalping feeds are unnecessary.
- **Complex Full-Stack GUI:** A lightweight terminal CLI / Markdown report that runs in seconds without web server overhead.

### Anti-Goals
- **Non-IDX80 Tickers:** Never recommend stocks outside the locked IDX80 list, as trades on other tickers do not count toward leaderboard score.
- **Over-Diversification:** Avoid splitting Rp 200M into 10–15 small positions. In a 5-day tournament, concentration into 2–3 high-momentum setups is required to achieve podium-level returns.
- **Low-Volatility Traps:** Avoid stagnant blue chips that move <0.5% a day unless they undergo a major news or volume breakout.

---

## 3. Constraints & Rules
- **Universe:** Exclusively IDX80 constituents.
- **Starting Capital:** Rp 200,000,000.
- **Trading Hours (WIB):**
  - Monday–Thursday: Session 1 (09:00–12:00), Session 2 (13:30–16:00).
  - Friday: Session 1 (09:00–11:30), Session 2 (14:00–16:00).
  - Orders outside market hours are disallowed.
- **Transaction Requirements:** Minimum 10 transactions (buys + sells) across at least 2 different tickers during the competition.
- **Position Mechanics:** Lot size = 100 shares. Overnight holding allowed up to competition end.
- **Device & Execution:** Manual order placement via 1 authorized mobile phone running IDX Mobile.

---

## 4. The Decided Workflow
1. **Morning Checkpoint (08:30–08:50 WIB):**
   - User runs `python screener.py scan`.
   - Tool fetches recent daily OHLCV for all IDX80 tickers via Yahoo Finance (`<TICKER>.JK`).
   - Tool ranks stocks by breakout momentum score and prints top 3–5 setup cards.
   - User opens IDX Mobile at 09:00 WIB and places buy orders for the selected 2–3 tickers.
2. **Midday Checkpoint (12:00–13:20 WIB):**
   - Tool can be re-run with intraday data (`python screener.py midday`) to inspect Session 1 volume and price action.
   - User checks if any position hit target profit or stop loss.
3. **Closing Checkpoint (15:30–15:55 WIB):**
   - User decides whether to lock in profits or hold winners overnight.
4. **Trade Logging:**
   - User runs `python screener.py log buy BBCA 100 10000` to track trade count toward the 10-trade quota.

---

## 5. What is Left to the Builder
- **IDX80 Constituent List:** Curate the 80 verified tickers trading on the Indonesia Stock Exchange as `<TICKER>.JK`.
- **Scoring Algorithm:** Combine:
  - Relative Volume (RVOL): Today's or recent volume vs 20-day moving average volume.
  - Price Momentum: % change over 1, 3, and 5 days, plus EMA alignment ($Close > EMA_{9} > EMA_{20}$).
  - RSI(14) filtering (favoring momentum continuation between 50 and 70, avoiding extreme overbought >80).
- **Sizing Logic:** Default allocation model dividing Rp 200M into 2 or 3 positions (e.g. 50% / 50% or 33% / 33% / 34%) with round lot calculation (floor to nearest 100 shares).
- **CLI Architecture:** Single-file or lightweight package in Python using `requests` or `urllib` to query Yahoo Finance without brittle heavy dependencies.
