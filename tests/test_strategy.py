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
