from typing import List, Dict, Any

def compute_ema(series: List[float], period: int) -> List[float]:
    if not series:
        return []
    if len(series) <= period:
        # If series is shorter than period, SMA fallback
        return [sum(series[:i + 1]) / (i + 1) for i in range(len(series))]
    
    multiplier = 2.0 / (period + 1.0)
    ema = [0.0] * len(series)
    # Seed with SMA of first `period`
    ema[period - 1] = sum(series[:period]) / period
    for i in range(period - 1):
        ema[i] = series[i]
        
    for i in range(period, len(series)):
        ema[i] = (series[i] - ema[i - 1]) * multiplier + ema[i - 1]
        
    return ema

def compute_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
        
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(0.0, d) for d in deltas]
    losses = [max(0.0, -d) for d in deltas]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0
        
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def compute_rvol(volumes: List[int], window: int = 20) -> float:
    if len(volumes) <= 1:
        return 1.0
    current_vol = volumes[-1]
    prev_vols = volumes[-min(len(volumes), window + 1):-1]
    if not prev_vols:
        return 1.0
    avg_vol = sum(prev_vols) / len(prev_vols)
    if avg_vol <= 0:
        return 0.0
    return round(float(current_vol) / float(avg_vol), 2)

def compute_momentum_score(candles: Dict[str, Any]) -> Dict[str, Any]:
    closes = candles.get("closes", [])
    volumes = candles.get("volumes", [])
    current_price = candles.get("current_price", closes[-1] if closes else 0.0)
    
    if len(closes) < 5:
        return {
            "score": 0.0,
            "rvol": 1.0,
            "rsi": 50.0,
            "ema_trend": False,
            "change_1d": 0.0,
            "change_5d": 0.0
        }
        
    rvol = compute_rvol(volumes, 20)
    rsi = compute_rsi(closes, 14)
    
    ema9 = compute_ema(closes, 9)
    ema20 = compute_ema(closes, 20)
    ema_trend = bool(current_price >= ema9[-1] >= ema20[-1])
    
    change_1d = ((closes[-1] - closes[-2]) / closes[-2] * 100.0) if len(closes) >= 2 else 0.0
    change_5d = ((closes[-1] - closes[-6]) / closes[-6] * 100.0) if len(closes) >= 6 else change_1d
    
    if 50.0 <= rsi <= 72.0:
        rsi_fitness = 100.0
    elif rsi > 72.0:
        rsi_fitness = max(0.0, 100.0 - (rsi - 72.0) * 3.5)
    else:
        rsi_fitness = max(0.0, (rsi / 50.0) * 80.0)
        
    trend_bonus = 100.0 if ema_trend else 0.0
    rvol_scaled = min(rvol * 35.0, 100.0)
    pct_score = max(0.0, min((change_1d * 4.0 + change_5d * 2.0), 100.0))
    
    composite_score = round(
        0.35 * rvol_scaled +
        0.25 * trend_bonus +
        0.20 * pct_score +
        0.20 * rsi_fitness,
        2
    )
    
    return {
        "score": composite_score,
        "rvol": rvol,
        "rsi": round(rsi, 2),
        "ema_trend": ema_trend,
        "change_1d": round(change_1d, 2),
        "change_5d": round(change_5d, 2)
    }
