import json
import subprocess
import pytest

def test_status_json():
    result = subprocess.run(
        ["python3", "screener.py", "status", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "cash" in data
    assert "total_assets" in data
    assert "realized_pnl" in data

def test_quote_json(monkeypatch):
    # Test quote command with --json
    result = subprocess.run(
        ["python3", "screener.py", "quote", "BBCA", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ticker"] in ["BBCA", "BBCA.JK"]
    assert "price" in data
    assert "tp1" in data
    assert "tp2" in data
    assert "stop_loss" in data

def test_quote_invalid_ticker_json():
    result = subprocess.run(
        ["python3", "screener.py", "quote", "XYZ999", "--json"],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    assert data.get("success") is False
    assert "error" in data
