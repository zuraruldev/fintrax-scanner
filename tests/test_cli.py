# tests/test_cli.py
import os
import subprocess
import pytest
from fintrac_screener.reporter import render_markdown_report

def test_render_markdown_report():
    setups = [{
        "ticker": "BBCA.JK",
        "current_price": 10200.0,
        "target_lots": 65,
        "allocated_capital": 66300000.0,
        "tp1": 10650.0,
        "tp2": 11050.0,
        "stop_loss": 9925.0,
        "score": 88.5,
        "rvol": 2.4,
        "rsi": 64.2
    }]
    status = {
        "total_trades": 4,
        "unique_tickers": 2,
        "quota_completed": False,
        "cash": 133700000.0,
        "total_assets": 200000000.0
    }
    md = render_markdown_report(setups, status)
    assert "# FINTRAC 2026 - Trading Setup & Signals" in md
    assert "BBCA.JK" in md
    assert "65 Lots" in md
    assert "4 / 10" in md

def test_cli_help():
    result = subprocess.run(["python3", "screener.py", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "scan" in result.stdout
    assert "log" in result.stdout
    assert "status" in result.stdout
