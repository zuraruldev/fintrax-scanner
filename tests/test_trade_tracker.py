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

def test_trade_validation_and_realized_pnl(tmp_path):
    ledger_file = tmp_path / "trades.json"
    tracker = TradeTracker(file_path=str(ledger_file), initial_capital=200_000_000.0)

    # Invalid lots / price
    with pytest.raises(ValueError):
        tracker.record_trade("buy", "BBCA", 0, 10000.0)
    with pytest.raises(ValueError):
        tracker.record_trade("buy", "BBCA", 10, -500.0)

    # Cannot sell unowned stock or oversell
    with pytest.raises(ValueError):
        tracker.record_trade("sell", "BBCA", 10, 10000.0)

    tracker.record_trade("buy", "BBCA", 100, 10000.0)
    with pytest.raises(ValueError):
        tracker.record_trade("sell", "BBCA", 150, 11000.0)

    # Valid sell records realized PnL
    trade = tracker.record_trade("sell", "BBCA", 40, 11000.0)
    assert trade["realized_pnl"] == 40 * 100 * (11000.0 - 10000.0) # +4,000,000
    status = tracker.get_status()
    assert status["realized_pnl"] == 4_000_000.0

