import os

def normalize_ticker(ticker: str) -> str:
    cleaned = ticker.strip().upper()
    if not cleaned.endswith(".JK"):
        cleaned = f"{cleaned}.JK"
    return cleaned

def load_tickers(file_path: str = "idx80_tickers.txt") -> list[str]:
    if not os.path.exists(file_path):
        return []
    tickers = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            normalized = normalize_ticker(stripped)
            if normalized not in tickers:
                tickers.append(normalized)
    return tickers

def is_valid_ticker(ticker: str, allowed_tickers: list[str]) -> bool:
    norm = normalize_ticker(ticker)
    allowed_norm = {normalize_ticker(t) for t in allowed_tickers}
    return norm in allowed_norm
