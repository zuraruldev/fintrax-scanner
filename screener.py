#!/usr/bin/env python3
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from fintrac_screener.universe import load_tickers, is_valid_ticker
from fintrac_screener.market_data import fetch_candles
from fintrac_screener.indicators import compute_momentum_score
from fintrac_screener.strategy import generate_trade_setups
from fintrac_screener.trade_tracker import TradeTracker
from fintrac_screener.reporter import render_markdown_report, render_terminal_status, format_idr

def process_single_ticker(ticker: str, interval: str = "1d", range_str: str = "3mo"):
    candles = fetch_candles(ticker, interval=interval, range_str=range_str)
    if not candles:
        return None
    metrics = compute_momentum_score(candles)
    return {
        "ticker": ticker,
        "current_price": candles["current_price"],
        **metrics
    }

def run_scan(capital: float = 200_000_000.0, num_positions: int = 3, interval: str = "1d", ticker_file: str = "idx80_tickers.txt"):
    tickers = load_tickers(ticker_file)
    if not tickers:
        print(f"No tickers found in {ticker_file}!")
        return

    print(f"Scanning {len(tickers)} IDX80 constituents for momentum setups...")
    scored_candidates = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {executor.submit(process_single_ticker, t, interval, "3mo"): t for t in tickers}
        for future in as_completed(future_map):
            try:
                res = future.result()
                if res and res.get("score", 0) > 0:
                    scored_candidates.append(res)
            except Exception as e:
                # Log error and continue with remaining tickers
                pass

    setups = generate_trade_setups(scored_candidates, capital=capital, num_positions=num_positions)
    tracker = TradeTracker()
    current_prices = {c["ticker"]: c["current_price"] for c in scored_candidates}
    status = tracker.get_status(current_prices=current_prices)

    # Write signals.md
    md_content = render_markdown_report(setups, status)
    with open("signals.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("Saved report to signals.md\n")

    # Display Top Setups in Terminal
    print("=" * 80)
    print("  FINTRAC 2026 - TOP MOMENTUM SETUPS")
    print("=" * 80)
    print(f"{'Ticker':<10} {'Price':<10} {'Lots':<10} {'TP1 (+4.5%)':<14} {'TP2 (+8.5%)':<14} {'SL (-2.8%)':<14} {'RVOL':<8} {'RSI':<6}")
    print("-" * 80)
    for s in setups:
        print(f"{s['ticker']:<10} {format_idr(s['price']):<10} {f'{s['target_lots']} Lots':<10} {format_idr(s['tp1']):<14} {format_idr(s['tp2']):<14} {format_idr(s['stop_loss']):<14} {s['rvol']:<7.1f}x {s['rsi']:<6.1f}")
    print("=" * 80)
    print("\n" + render_terminal_status(status))

def main():
    parser = argparse.ArgumentParser(description="FINTRAC 2026 IDX80 Screener & Trade Planner")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Run pre-market morning scan")
    scan_parser.add_argument("--capital", type=float, default=200_000_000.0, help="Total capital in IDR")
    scan_parser.add_argument("--positions", type=int, default=3, help="Number of concentrated positions (default 3)")
    scan_parser.add_argument("--tickers", type=str, default="idx80_tickers.txt", help="Path to ticker list")

    # midday
    midday_parser = subparsers.add_parser("midday", help="Run midday review scan")
    midday_parser.add_argument("--capital", type=float, default=200_000_000.0, help="Total capital in IDR")
    midday_parser.add_argument("--positions", type=int, default=3, help="Number of positions")
    midday_parser.add_argument("--tickers", type=str, default="idx80_tickers.txt", help="Path to ticker list")

    # log
    log_parser = subparsers.add_parser("log", help="Log an executed trade")
    log_parser.add_argument("action", choices=["buy", "sell"], help="Action: buy or sell")
    log_parser.add_argument("ticker", help="Stock ticker (e.g. BBCA)")
    log_parser.add_argument("lots", type=int, help="Number of lots traded")
    log_parser.add_argument("price", type=float, help="Execution price per share")
    log_parser.add_argument("--tickers", type=str, default="idx80_tickers.txt", help="Path to ticker list")

    # status
    subparsers.add_parser("status", help="Show current portfolio status and trade quota")

    args = parser.parse_args()

    if args.command == "scan":
        run_scan(capital=args.capital, num_positions=args.positions, interval="1d", ticker_file=args.tickers)
    elif args.command == "midday":
        run_scan(capital=args.capital, num_positions=args.positions, interval="60m", ticker_file=args.tickers)
    elif args.command == "log":
        valid_tickers = load_tickers(args.tickers)
        if valid_tickers and not is_valid_ticker(args.ticker, valid_tickers):
            print(f"⚠️ WARNING: {args.ticker.upper()} is NOT in the official IDX80 list! In FINTRAC 2026, trades outside IDX80 are disqualified.")
        tracker = TradeTracker()
        try:
            tracker.record_trade(args.action, args.ticker, args.lots, args.price)
            print(f"Logged {args.action.upper()} {args.lots} lots of {args.ticker.upper()} at {format_idr(args.price)}")
            print("\n" + render_terminal_status(tracker.get_status()))
        except ValueError as e:
            print(f"❌ Error: {e}")
    elif args.command == "status":
        tracker = TradeTracker()
        print(render_terminal_status(tracker.get_status()))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
