"""
Demo script: fetch data via akshare adapter through the unified `fetcher` API
and save to cache (handled by `fetcher`).

Usage (PowerShell):
$env:PYTHONPATH="D:\Code\FeedbackTrader"; & D:/Code/FeedbackTrader/.venv/Scripts/python.exe scripts/fetch_akshare_save.py

The script will handle missing `akshare` gracefully and print helpful messages.
"""
from datetime import datetime
from src.data import fetcher
from src.data.exceptions import AdapterError


def main():
    symbol = "sh600000"      # example: 浦发银行
    start_date = "20200101"
    end_date = "20251112"

    print(f"Fetching {symbol} from {start_date} to {end_date} via akshare...")
    try:
        df = fetcher.get_history(symbol, start_date, end_date, source='akshare', cache=True, refresh=False)
        print(f"Fetched rows: {len(df)}")
        if not df.empty:
            print("Cached to disk under data/ (parquet or csv fallback)")
    except AdapterError as ae:
        print("Adapter error:", ae)
        print("Hint: ensure `akshare` is installed in your environment: `pip install akshare`")
    except Exception as e:
        print("Failed to fetch:", e)


if __name__ == '__main__':
    main()
