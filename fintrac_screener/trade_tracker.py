import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class TradeTracker:
    def __init__(self, file_path: str = "trades.json", initial_capital: float = 200_000_000.0):
        self.file_path = file_path
        self.initial_capital = float(initial_capital)
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "initial_capital" not in data:
                        data["initial_capital"] = self.initial_capital
                    if "trades" not in data:
                        data["trades"] = []
                    return data
            except Exception:
                pass
        return {
            "initial_capital": self.initial_capital,
            "trades": []
        }

    def _save(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def record_trade(self, action: str, ticker: str, lots: int, price: float) -> Dict[str, Any]:
        clean_action = action.strip().lower()
        if clean_action not in ["buy", "sell"]:
            raise ValueError(f"Invalid trade action: {action}. Must be 'buy' or 'sell'.")
            
        clean_ticker = ticker.strip().upper()
        if clean_ticker.endswith(".JK"):
            clean_ticker = clean_ticker[:-3]

        trade_entry = {
            "id": len(self.data["trades"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "action": clean_action,
            "ticker": clean_ticker,
            "lots": int(lots),
            "price": float(price),
            "value": float(lots * 100 * price)
        }
        self.data["trades"].append(trade_entry)
        self._save()
        return trade_entry

    def get_status(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        cash = float(self.data.get("initial_capital", self.initial_capital))
        positions: Dict[str, Dict[str, Any]] = {}
        unique_tickers = set()
        trades = self.data.get("trades", [])

        for t in trades:
            ticker = t["ticker"]
            unique_tickers.add(ticker)
            action = t["action"]
            lots = t["lots"]
            price = t["price"]
            trade_val = float(lots * 100 * price)

            if action == "buy":
                cash -= trade_val
                if ticker not in positions:
                    positions[ticker] = {"lots": 0, "avg_price": 0.0, "total_cost": 0.0}
                curr = positions[ticker]
                new_lots = curr["lots"] + lots
                new_cost = curr["total_cost"] + trade_val
                new_avg = new_cost / (new_lots * 100) if new_lots > 0 else 0.0
                positions[ticker] = {"lots": new_lots, "avg_price": new_avg, "total_cost": new_cost}
            elif action == "sell":
                cash += trade_val
                if ticker in positions:
                    curr = positions[ticker]
                    new_lots = max(0, curr["lots"] - lots)
                    new_cost = new_lots * 100 * curr["avg_price"]
                    if new_lots == 0:
                        del positions[ticker]
                    else:
                        positions[ticker] = {"lots": new_lots, "avg_price": curr["avg_price"], "total_cost": new_cost}

        portfolio_val = 0.0
        prices = current_prices or {}
        for sym, pos in positions.items():
            mkt_price = prices.get(sym, prices.get(f"{sym}.JK", pos["avg_price"]))
            portfolio_val += float(pos["lots"] * 100 * mkt_price)

        total_trades = len(trades)
        quota_completed = bool(total_trades >= 10 and len(unique_tickers) >= 2)

        return {
            "total_trades": total_trades,
            "unique_tickers": len(unique_tickers),
            "quota_completed": quota_completed,
            "cash": cash,
            "portfolio_value": portfolio_val,
            "total_assets": cash + portfolio_val,
            "positions": positions,
            "trades": trades
        }
