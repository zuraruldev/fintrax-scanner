# tests/test_market_data.py
import pytest
from unittest.mock import patch, MagicMock
from fintrac_screener.market_data import fetch_candles, parse_yahoo_chart_response

def test_parse_yahoo_chart_response_valid():
    sample_payload = {
        "chart": {
            "result": [{
                "meta": {"regularMarketPrice": 10200.0},
                "timestamp": [1700000000, 1700086400],
                "indicators": {
                    "quote": [{
                        "open": [10000.0, 10100.0],
                        "high": [10200.0, 10300.0],
                        "low": [9950.0, 10050.0],
                        "close": [10100.0, 10200.0],
                        "volume": [50000000, 65000000]
                    }]
                }
            }],
            "error": None
        }
    }
    result = parse_yahoo_chart_response(sample_payload)
    assert result is not None
    assert result["current_price"] == 10200.0
    assert len(result["closes"]) == 2
    assert result["volumes"][-1] == 65000000

def test_parse_yahoo_chart_response_error_or_empty():
    assert parse_yahoo_chart_response({"chart": {"result": None, "error": {"code": "Not Found"}}}) is None
    assert parse_yahoo_chart_response({}) is None

@patch("fintrac_screener.market_data.requests.get")
def test_fetch_candles_handles_network_error(mock_get):
    mock_get.side_effect = Exception("Connection error")
    assert fetch_candles("BBCA.JK") is None
