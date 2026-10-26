# tests/test_indicators.py
import pytest
from fintrac_screener.indicators import compute_ema, compute_rsi, compute_rvol, compute_momentum_score

def test_compute_ema():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    ema = compute_ema(prices, period=3)
    assert len(ema) == len(prices)
    assert ema[-1] > ema[0]

def test_compute_rsi():
    # Continual up move -> high RSI
    closes = [float(100 + i * 2) for i in range(25)]
    rsi = compute_rsi(closes, period=14)
    assert rsi > 70.0

def test_compute_rvol_and_zero_division():
    vols = [1000] * 20 + [2500]
    assert compute_rvol(vols, window=20) == 2.5
    # Zero volume handling (Review Focus #2)
    assert compute_rvol([0] * 21, window=20) == 0.0

def test_compute_momentum_score():
    closes = [100.0 + i for i in range(30)]
    volumes = [10000] * 29 + [30000]
    candles = {
        "closes": closes,
        "volumes": volumes,
        "highs": [c + 1 for c in closes],
        "lows": [c - 1 for c in closes],
        "opens": closes,
        "current_price": closes[-1]
    }
    metrics = compute_momentum_score(candles)
    assert metrics["score"] > 0
    assert metrics["rvol"] >= 2.5
    assert metrics["ema_trend"] is True
