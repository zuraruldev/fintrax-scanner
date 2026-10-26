# FINTRAC 2026 Discord Bot & Alya AI Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the FINTRAC 2026 IDX80 momentum screener and portfolio management engine into the Oceanic.js Discord bot and Alya AI chat assistant with role-based access control, rich embed cards, and scheduled market briefings.

**Architecture:** Extend the existing Python CLI (`screener.py`) to emit clean JSON and support single-ticker quotes, then connect it to the Discord bot via a typed Node.js subprocess bridge. Expose capabilities through a structured Discord command (`fx fintrac`), Alya agent tools in `src/tools/`, and an automated weekday market briefing background timer in `src/module/fintrac.ts`.

**Tech Stack:** Python 3.10+ (argparse, requests, numpy), TypeScript (ESNext), Node.js (child_process, process.loadEnvFile), Oceanic.js (v1.12.0), esbuild.

**Spec:** `/home/zura/fintrac_screener/docs/superpowers/specs/2026-10-26-fintrac-discord-bot-design.md`

## Global Constraints
- Universe compliance: Exclusively trade and screen stocks within official IDX80 (`idx80_tickers.txt`).
- Price fraction ticks: All generated levels (entry, TP1, TP2, SL) must conform to official BEI tick sizes (Rp 1, 2, 5, 10, 25).
- Single source of truth: Both Python CLI and Discord bot read/write `/home/zura/fintrac_screener/trades.json`.
- Strict access control: FINTRAC commands and AI tools are restricted to bot admins and explicitly authorized users.
- Non-blocking execution: All Python subprocess calls must execute asynchronously without blocking Discord's event loop.

## Review Focus
- **Unauthorized user execution**: An unapproved user attempting `fx fintrac` or asking Alya to run fintrac tools must receive an access-denied response and never see trade data or execute scans.
- **Python CLI failure handling**: Subprocess timeouts, network errors on Yahoo Finance API, or invalid arguments must be caught and returned as clean Discord error embeds, not unhandled process crashes.
- **JSON serialization fidelity**: Target prices, lots, momentum scores, and Indonesian Rupiah amounts must parse cleanly between Python's stdout and TypeScript interfaces.
- **Double alert prevention**: Weekday briefings (08:30, 12:00, 16:05 WIB) must fire exactly once per designated time slot per calendar day.
- **Build integrity**: The Discord bot must compile cleanly via `node build.js` and pass ESLint without TypeScript or bundling errors.

---

### Task 1: Python Engine `--json` Output Flag & `quote` Subcommand

**Files:**
- Modify: `/home/zura/fintrac_screener/screener.py`
- Modify: `/home/zura/fintrac_screener/fintrac_screener/strategy.py`
- Test: `/home/zura/fintrac_screener/tests/test_cli_json.py`

**Interfaces:**
- Consumes: `generate_trade_setups`, `TradeTracker`, `fetch_candles`, `compute_momentum_score`
- Produces: JSON payload structure on `stdout` when `--json` is supplied to `scan`, `midday`, `status`, `log`, and `quote <ticker>`.

- [ ] **Step 1: Write tests for `--json` outputs and `quote` subcommand in `tests/test_cli_json.py`**
- [ ] **Step 2: Run pytest to verify tests fail**
  Run: `pytest tests/test_cli_json.py -v`
  Expected: FAIL (argument `--json` unrecognized or `quote` not found)
- [ ] **Step 3: Implement `--json` flag and `quote` subcommand in `screener.py`**
  - Add `--json` boolean argument to CLI parser.
  - Add `quote` subcommand accepting a single ticker (validating against IDX80), computing momentum metrics, and generating trade levels.
  - When `--json` is true, suppress ANSI printing and output clean `json.dumps(result, indent=2)`.
- [ ] **Step 4: Run pytest to verify all tests pass**
  Run: `pytest tests/test_cli_json.py -v`
  Expected: PASS
- [ ] **Step 5: Verify CLI manual execution**
  Run: `python3 screener.py status --json`
  Expected: Valid JSON with cash, portfolio, realized_pnl, quota progress.

---

### Task 2: Discord Bot Access Control & Authorized Users Storage

**Files:**
- Create: `/home/zura/code/discord-bot/src/fintrac/auth.ts`
- Create: `/home/zura/code/discord-bot/data/fintrac_users.json` (initial empty list)
- Test: `/home/zura/code/discord-bot/test/fintrac-auth.test.ts`

**Interfaces:**
- Consumes: `isAdmin(userId)` from `src/constants.ts`
- Produces:
  ```typescript
  export function isFintracAuthorized(userId: string): boolean;
  export function allowFintracUser(userId: string): boolean;
  export function revokeFintracUser(userId: string): boolean;
  export function getFintracAuthorizedUsers(): string[];
  ```

- [ ] **Step 1: Write unit tests for authorization in `/home/zura/code/discord-bot/test/fintrac-auth.test.ts`**
- [ ] **Step 2: Implement authorization helper in `/home/zura/code/discord-bot/src/fintrac/auth.ts`**
  - Check `isAdmin(userId)`.
  - Read `process.env.FINTRAC_ALLOWED_USERS` (comma-separated).
  - Read and persist user IDs to `data/fintrac_users.json`.
- [ ] **Step 3: Run test script via Node.js to verify authorization behavior**
  Run: `node --test test/fintrac-auth.test.ts` (or direct ts-node / node runner)
  Expected: PASS
- [ ] **Step 4: Ensure directory and initial `data/fintrac_users.json` file exist**

---

### Task 3: Discord Bot Subprocess Bridge

**Files:**
- Create: `/home/zura/code/discord-bot/src/fintrac/types.ts`
- Create: `/home/zura/code/discord-bot/src/fintrac/bridge.ts`
- Test: `/home/zura/code/discord-bot/test/fintrac-bridge.test.ts`

**Interfaces:**
- Consumes: `child_process.execFile`, `process.env.FINTRAC_DIR`, `process.env.FINTRAC_PYTHON`
- Produces:
  ```typescript
  export async function runFintracScan(mode: 'scan' | 'midday', options?: { capital?: number; positions?: number }): Promise<FintracScanResult>;
  export async function getFintracStatus(): Promise<FintracStatusResult>;
  export async function getFintracQuote(ticker: string): Promise<FintracQuoteResult>;
  export async function logFintracTrade(action: 'buy' | 'sell', ticker: string, lots: number, price: number): Promise<FintracLogResult>;
  ```

- [ ] **Step 1: Define TypeScript interfaces in `src/fintrac/types.ts` for setups, status, quotes, and log outcomes**
- [ ] **Step 2: Write tests in `test/fintrac-bridge.test.ts` verifying bridge execution against mock and real python CLI**
- [ ] **Step 3: Implement `src/fintrac/bridge.ts` using `child_process.execFile` with 60-second timeout and JSON parsing**
- [ ] **Step 4: Run bridge test to verify status and scan results are returned as strongly-typed objects**
  Run: `node test/fintrac-bridge.test.ts`
  Expected: PASS

---

### Task 4: Discord Command `fx fintrac`

**Files:**
- Create: `/home/zura/code/discord-bot/src/command/fintrac.ts`

**Interfaces:**
- Consumes: `defineCommand` from `src/Command.ts`, `isFintracAuthorized` from `src/fintrac/auth.ts`, bridge methods from `src/fintrac/bridge.ts`, embeds from `src/utils.ts`
- Produces: `fx fintrac <scan|midday|status|quote|log|allow|revoke>` Discord command.

- [ ] **Step 1: Implement `src/command/fintrac.ts`**
  - Check authorization: if `!isFintracAuthorized(message.author.id)`, reply with error embed rejecting unauthorized access.
  - Handle `scan` and `midday`: Send "Scanning IDX80..." typing indicator, invoke bridge, render rich embeds showing top setups with Entry, Lot, Capital, TP1, TP2, SL, Score, RVOL, RSI.
  - Handle `status`: Render embed with Total Assets, Cash, Portfolio Value, Realized PnL, open positions, and transaction quota counter (`N / 10 trades`, distinct tickers).
  - Handle `quote <ticker>`: Render single-stock momentum snapshot with calculated levels.
  - Handle `log <buy|sell> <ticker> <lots> <price>`: Record trade and render updated portfolio balance.
  - Handle `allow <@user>` & `revoke <@user>`: Restricted to `isAdmin(message.author.id)`.
- [ ] **Step 2: Verify command registration and syntax parsing with esbuild compile**

---

### Task 5: Alya AI Chat Bot Tools & System Context

**Files:**
- Create: `/home/zura/code/discord-bot/src/tools/fintrac.ts`
- Modify: `/home/zura/code/discord-bot/src/tools/registry.ts`
- Modify: `/home/zura/code/discord-bot/src/chat/service.ts`
- Modify: `/home/zura/code/discord-bot/data/docs.md`

**Interfaces:**
- Consumes: `toolRegistry.register`, `runFintracScan`, `getFintracStatus`, `getFintracQuote`, `logFintracTrade`, `isFintracAuthorized`
- Produces: AI agent function definitions for `fintrac_scan`, `fintrac_status`, `fintrac_quote`, and `fintrac_log_trade`.

- [ ] **Step 1: Create `src/tools/fintrac.ts` registering the 4 tools into `toolRegistry`**
  - Implement execution handlers with authorization checking against `context.userId`.
- [ ] **Step 2: Update `src/tools/registry.ts` and `src/chat/service.ts`**
  - Allow `getAllDefinitions` to accept `{ isAdmin?: boolean; userId?: string }` so fintrac tools are omitted if user is unauthorized.
  - Update `service.ts` to pass `userId` to `getAllDefinitions`.
- [ ] **Step 3: Update `data/docs.md`**
  - Add FINTRAC 2026 rules section: Rp 200M capital, IDX80 list, min 10 transactions across >= 2 tickers, TP1 +4.5%, TP2 +8.5%, SL -2.8%.
  - Instruct Alya on how to explain momentum scores and quota status.

---

### Task 6: Automated Market Briefing Background Module

**Files:**
- Create: `/home/zura/code/discord-bot/src/module/fintrac.ts`

**Interfaces:**
- Consumes: Oceanic.js Client, `process.env.FINTRAC_ALERT_CHANNEL_ID`, `runFintracScan`, `getFintracStatus`
- Produces: Auto-scheduled background worker running once per minute.

- [ ] **Step 1: Implement `src/module/fintrac.ts`**
  - Convert system time to `Asia/Jakarta` (WIB).
  - Check day of week: Monday to Friday (1 to 5).
  - Schedule triggers:
    - 08:30 WIB: Morning pre-market scan brief.
    - 12:00 WIB: Midday review brief.
    - 16:05 WIB: End-of-day portfolio and trade quota recap.
  - Guard against multiple triggers within the same day using a `lastAlertKey` tracker (e.g. `YYYY-MM-DD-08:30`).
  - Dispatch formatted embeds to the channel specified by `process.env.FINTRAC_ALERT_CHANNEL_ID`.
- [ ] **Step 2: Ensure virtual import bundle picks up the new module in `src/index.ts`**

---

### Task 7: End-to-End Build and Verification

**Files:**
- Test all components across both repositories

- [ ] **Step 1: Run Python tests in `/home/zura/fintrac_screener`**
  Run: `pytest tests/ -v`
  Expected: All tests pass
- [ ] **Step 2: Compile Discord Bot bundle**
  Run: `node build.js` in `/home/zura/code/discord-bot`
  Expected: Clean build without errors into `dist/index.js`
- [ ] **Step 3: Run ESLint in `/home/zura/code/discord-bot`**
  Run: `npm run lint`
  Expected: 0 errors
- [ ] **Step 4: End-to-end dry run verification**
  - Verify `python3 screener.py scan --json` produces valid JSON.
  - Verify `python3 screener.py quote BBCA --json` produces valid quote JSON.
  - Verify authorization helper blocks random user ID and allows admin user ID.
