# Design: FINTRAC 2026 Discord Bot & Alya AI Agent Integration

## 1. Intent and Why
The user is competing in the **FINTRAC 2026** virtual stock trading tournament on IDX Mobile. They manage trades on mobile during their daily routine and use their Discord bot (running Oceanic.js and the Alya AI agent at `/home/zura/code/discord-bot`) as their primary command center.

They need to execute momentum screening (`scan`, `midday`), check portfolio status and quota progress (`status`), look up live stock quotes (`quote`), and log trades (`log`) directly from Discord via:
1. Structured Discord commands (`fx fintrac ...`)
2. Conversational chat with the Alya AI assistant (who can trigger tools and explain setups)
3. Automated market briefing alerts at key trading hours (08:30 WIB, 12:00 WIB, 16:05 WIB)

Access must be strictly gated: only bot admins and explicitly authorized users can run FINTRAC commands or access FINTRAC agent tools.

---

## 2. Architecture & Approach

### 2.1 Subprocess Bridge (`screener.py --json`)
Instead of rewriting indicator math and Yahoo Finance API parsing into TypeScript, the existing Python engine (`/home/zura/fintrac_screener/screener.py`) is enhanced with a `--json` output flag and a single-ticker `quote` command.
The Discord bot invokes Python via Node.js `child_process.execFile` in `/home/zura/fintrac_screener`, parsing the stdout JSON.

### 2.2 Access Control & Authorization
- Bot Admins (`isAdmin(userId)` in `src/constants.ts`) always have access.
- Authorized users are loaded from `process.env.FINTRAC_ALLOWED_USERS` (comma-separated IDs) merged with a local persistent file `/home/zura/code/discord-bot/data/fintrac_users.json`.
- Admins can run `fx fintrac allow <@user|id>` and `fx fintrac revoke <@user|id>` to manage access dynamically.
- Alya AI tools are gated: tool definitions and executions require `isAdmin(userId) || isFintracAuthorized(userId)`.

### 2.3 Discord Command (`fx fintrac`)
- `fx fintrac scan [--capital <N>] [--positions <N>]`: Pre-market 1-day scan.
- `fx fintrac midday [--capital <N>] [--positions <N>]`: Midday 60m session review.
- `fx fintrac status`: Portfolio valuation, cash balance, realized PnL, open positions, and 10-trade quota progress.
- `fx fintrac quote <ticker>`: Real-time quote, RSI, RVOL, EMA alignment, and calculated levels for a single IDX80 stock.
- `fx fintrac log <buy|sell> <ticker> <lots> <price>`: Record tournament trade.
- `fx fintrac allow <user>` / `fx fintrac revoke <user>`: Admin-only access management.

### 2.4 Alya AI Agent Tool Calling
Four tools registered in `src/tools/registry.ts`:
- `fintrac_scan`: Parameters `{ mode: "scan" | "midday", capital?: number, positions?: number }`
- `fintrac_quote`: Parameters `{ ticker: string }`
- `fintrac_status`: Parameters `{}`
- `fintrac_log_trade`: Parameters `{ action: "buy" | "sell", ticker: string, lots: number, price: number }`

Alya receives knowledge about the FINTRAC 2026 rules (IDX80 only, 10 min trades across >=2 tickers, Rp 200M capital, TP1 +4.5%, TP2 +8.5%, SL -2.8%) in `data/docs.md` and system prompts, allowing her to discuss trading setups and quota progress intelligently.

### 2.5 Automated Market Briefings (`src/module/fintrac.ts`)
- Scheduled alerts sent to `FINTRAC_ALERT_CHANNEL_ID` on trading days (Monday–Friday):
  - **08:30 WIB**: Pre-market morning scan brief.
  - **12:00 WIB**: Midday review brief.
  - **16:05 WIB**: End-of-day portfolio and trade quota summary.
- Guarded to execute once per slot per day.

---

## 3. Constraints & Edge Cases
- **Rate Limiting & Delays**: Free Yahoo Finance data for IDX (.JK) has 10–15 min delay; continuous 1-minute 80-stock scans are avoided to prevent HTTP 429 IP bans. Instead, automated alerts occur at 08:30, 12:00, 16:05 WIB, while `fx fintrac quote <ticker>` provides instant single-ticker checks.
- **Shared State**: Both Python CLI and Discord bot read and write directly to `/home/zura/fintrac_screener/trades.json`.
- **Tick Rounding**: All target prices strictly adhere to BEI price fractions.
