from typing import List, Dict, Any

def format_idr(amount: float) -> str:
    return f"Rp {amount:,.0f}".replace(",", ".")

def render_markdown_report(setups: List[Dict[str, Any]], status: Dict[str, Any]) -> str:
    lines = []
    lines.append("# FINTRAC 2026 - Trading Setup & Signals")
    lines.append("")
    lines.append("## 📊 Competition Status & Rules Tracker")
    total_trades = status.get("total_trades", 0)
    unique_tickers = status.get("unique_tickers", 0)
    quota_met = status.get("quota_completed", False)
    cash = status.get("cash", 0.0)
    portfolio_val = status.get("portfolio_value", 0.0)
    total_assets = status.get("total_assets", cash + portfolio_val)
    realized_pnl = status.get("realized_pnl", 0.0)
    
    quota_badge = "✅ COMPLETED" if quota_met else "⚠️ IN PROGRESS"
    lines.append(f"- **Progress to 10-Trade Quota:** {total_trades} / 10 trades ({quota_badge})")
    lines.append(f"- **Distinct Tickers Traded:** {unique_tickers} (Minimum 2 required)")
    lines.append(f"- **Cash Balance:** {format_idr(cash)}")
    lines.append(f"- **Portfolio Market Value:** {format_idr(portfolio_val)}")
    lines.append(f"- **Realized Profit/Loss:** {format_idr(realized_pnl)}")
    lines.append(f"- **Total Assets (Leaderboard Rank Score):** **{format_idr(total_assets)}**")
    lines.append("")
    
    positions = status.get("positions", {})
    if positions:
        lines.append("### 💼 Current Open Positions")
        lines.append("| Ticker | Lots | Avg Price | Total Cost |")
        lines.append("|:-------|:-----|:----------|:-----------|")
        for sym, p in positions.items():
            lines.append(f"| {sym} | {p['lots']} | {format_idr(p['avg_price'])} | {format_idr(p['total_cost'])} |")
        lines.append("")

    lines.append("## 🎯 Top High-Momentum IDX80 Setups")
    if not setups:
        lines.append("No active breakout setups found at this time.")
    else:
        lines.append("| Ticker | Entry / Current | Position Size | Allocation | TP1 (+4.5%) | TP2 (+8.5%) | Stop-Loss (-2.8%) | Score | RVOL | RSI |")
        lines.append("|:-------|:----------------|:--------------|:-----------|:------------|:------------|:------------------|:------|:-----|:----|")
        for s in setups:
            price = s.get("price", s.get("current_price", 0.0))
            lines.append(
                f"| **{s['ticker']}** | {format_idr(price)} | **{s['target_lots']} Lots** (100 shs/lot) | {format_idr(s['allocated_capital'])} | "
                f"{format_idr(s['tp1'])} | {format_idr(s['tp2'])} | {format_idr(s['stop_loss'])} | "
                f"{s['score']} | {s['rvol']}x | {s['rsi']} |"
            )
            
    lines.append("")
    lines.append("---")
    lines.append("*Reminder: Transact only during official IDX hours on your authorized mobile phone.*")
    return "\n".join(lines)

def render_terminal_status(status: Dict[str, Any]) -> str:
    total_trades = status.get("total_trades", 0)
    unique_tickers = status.get("unique_tickers", 0)
    quota_met = status.get("quota_completed", False)
    cash = status.get("cash", 0.0)
    portfolio_val = status.get("portfolio_value", 0.0)
    total_assets = status.get("total_assets", cash + portfolio_val)
    realized_pnl = status.get("realized_pnl", 0.0)
    
    quota_str = "[OK] Met" if quota_met else f"[WAIT] Need {max(0, 10 - total_trades)} more trades"
    out = [
        "=" * 60,
        "  FINTRAC 2026 - COMPETITION PORTFOLIO STATUS",
        "=" * 60,
        f"  Total Assets (Leaderboard): {format_idr(total_assets)}",
        f"  Available Cash:            {format_idr(cash)}",
        f"  Portfolio Value:           {format_idr(portfolio_val)}",
        f"  Realized PnL:              {format_idr(realized_pnl)}",
        "-" * 60,
        f"  Trade Quota Progress:      {total_trades} / 10 ({quota_str})",
        f"  Unique Tickers Traded:     {unique_tickers} (Min 2 required)",
        "-" * 60,
    ]
    positions = status.get("positions", {})
    if positions:
        out.append("  Active Positions:")
        for sym, p in positions.items():
            out.append(f"    - {sym:6}: {p['lots']} Lots @ avg {format_idr(p['avg_price'])} (Cost: {format_idr(p['total_cost'])})")
    else:
        out.append("  No open positions.")
    out.append("=" * 60)
    return "\n".join(out)
