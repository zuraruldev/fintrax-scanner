import requests
from typing import Optional, Dict, Any

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def parse_yahoo_chart_response(data: dict) -> Optional[Dict[str, Any]]:
    if not isinstance(data, dict):
        return None
    chart = data.get("chart")
    if not chart or not isinstance(chart, dict):
        return None
    results = chart.get("result")
    if not results or not isinstance(results, list) or len(results) == 0:
        return None
    
    first = results[0]
    meta = first.get("meta", {})
    timestamps = first.get("timestamp", [])
    indicators = first.get("indicators", {})
    quotes = indicators.get("quote", [])
    if not quotes or len(quotes) == 0:
        return None
    
    quote = quotes[0]
    raw_opens = quote.get("open", [])
    raw_highs = quote.get("high", [])
    raw_lows = quote.get("low", [])
    raw_closes = quote.get("close", [])
    raw_volumes = quote.get("volume", [])
    
    clean_timestamps = []
    clean_opens = []
    clean_highs = []
    clean_lows = []
    clean_closes = []
    clean_volumes = []
    
    for i in range(len(timestamps)):
        o = raw_opens[i] if i < len(raw_opens) else None
        h = raw_highs[i] if i < len(raw_highs) else None
        l = raw_lows[i] if i < len(raw_lows) else None
        c = raw_closes[i] if i < len(raw_closes) else None
        v = raw_volumes[i] if i < len(raw_volumes) else None
        
        if c is not None and o is not None and h is not None and l is not None:
            clean_timestamps.append(timestamps[i])
            clean_opens.append(float(o))
            clean_highs.append(float(h))
            clean_lows.append(float(l))
            clean_closes.append(float(c))
            clean_volumes.append(int(v if v is not None else 0))
            
    if not clean_closes:
        return None
        
    current_price = meta.get("regularMarketPrice")
    if current_price is None:
        current_price = clean_closes[-1]
    else:
        current_price = float(current_price)
        
    return {
        "dates": clean_timestamps,
        "opens": clean_opens,
        "highs": clean_highs,
        "lows": clean_lows,
        "closes": clean_closes,
        "volumes": clean_volumes,
        "current_price": current_price
    }

def fetch_candles(ticker: str, interval: str = "1d", range_str: str = "3mo") -> Optional[Dict[str, Any]]:
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith(".JK"):
        ticker_clean = f"{ticker_clean}.JK"
        
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_clean}?interval={interval}&range={range_str}"
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=8)
        if response.status_code != 200:
            return None
        return parse_yahoo_chart_response(response.json())
    except Exception:
        return None
