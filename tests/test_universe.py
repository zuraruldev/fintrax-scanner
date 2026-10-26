# tests/test_universe.py
import os
import pytest
from fintrac_screener.universe import load_tickers, is_valid_ticker

def test_load_tickers_default(tmp_path):
    sample_file = tmp_path / "tickers.txt"
    sample_file.write_text("BBCA\nBBRI\n# comment\nBMRI\n\n")
    tickers = load_tickers(str(sample_file))
    assert tickers == ["BBCA.JK", "BBRI.JK", "BMRI.JK"]

def test_is_valid_ticker():
    allowed = ["BBCA.JK", "BBRI.JK"]
    assert is_valid_ticker("BBCA", allowed) is True
    assert is_valid_ticker("BBCA.JK", allowed) is True
    assert is_valid_ticker("GOTO", allowed) is False
