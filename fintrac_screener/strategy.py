from typing import List, Dict, Any, Tuple

def round_to_idx_tick(price: float) -> float:
    if price < 200:
        tick = 1.0
    elif price < 500:
        tick = 2.0
    elif price < 2000:
        tick = 5.0
    elif price < 5000:
        tick = 10.0
    else:
        tick = 25.0
        
    return round(round(price / tick) * tick, 2)

def calculate_lot_size(price: float, allocated_cash: float) -> Tuple[int, float]:
    if price <= 0 or allocated_cash <= 0:
        return 0, 0.0
    cost_per_lot = price * 100.0
    if allocated_cash < cost_per_lot:
        return 0, 0.0
    lots = int(allocated_cash // cost_per_lot)
    actual_capital = float(lots * cost_per_lot)
    return lots, actual_capital

def generate_trade_setups(
    scored_stocks: List[Dict[str, Any]], 
    capital: float = 200_000_000.0, 
    num_positions: int = 3
) -> List[Dict[str, Any]]:
    if not scored_stocks or num_positions <= 0:
        return []
        
    # Sort by score descending
    sorted_stocks = sorted(scored_stocks, key=lambda s: s.get("score", 0.0), reverse=True)
    top_candidates = sorted_stocks[:num_positions]
    
    cash_per_position = float(capital) / float(num_positions)
    setups = []
    
    for s in top_candidates:
        price = float(s.get("current_price", 0.0))
        lots, actual_cap = calculate_lot_size(price, cash_per_position)
        
        raw_tp1 = price * 1.045
        raw_tp2 = price * 1.085
        raw_sl = price * 0.972
        
        setups.append({
            "ticker": s.get("ticker", ""),
            "price": price,
            "target_lots": lots,
            "allocated_capital": actual_cap,
            "tp1": round_to_idx_tick(raw_tp1),
            "tp2": round_to_idx_tick(raw_tp2),
            "stop_loss": round_to_idx_tick(raw_sl),
            "score": s.get("score", 0.0),
            "rvol": s.get("rvol", 1.0),
            "rsi": s.get("rsi", 50.0)
        })
        
    return setups
