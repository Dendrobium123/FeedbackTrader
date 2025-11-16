import yfinance as yf
import pandas as pd
from ..exceptions import RateLimitError, AdapterError
# Use absolute import for logger (system package lives under src.system)
from src.system.log import get_logger

logger = get_logger(__name__)


def fetch(symbol, start, end, interval='1d', adjusted=True, **kwargs):
    """Fetch historical data using yfinance and return a DataFrame (DatetimeIndex).

    Map yfinance rate-limit or network errors to RateLimitError/AdapterError.
    """
    try:
        # specify auto_adjust to avoid future warnings
        logger.debug("yfinance adapter: fetching %s %s-%s interval=%s", symbol, start, end, interval)
        df = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=adjusted, progress=False)
        if df is None or df.empty:
            logger.info("yfinance adapter: no data for %s", symbol)
            return pd.DataFrame()
        # yfinance usually returns columns Open/High/Low/Close/Adj Close/Volume
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        logger.info("yfinance adapter: fetched %s rows for %s", len(df), symbol)
        return df
    except Exception as e:
        # map likely rate-limit messages to RateLimitError
        msg = str(e).lower()
        logger.exception("yfinance adapter error for %s: %s", symbol, e)
        if 'rate' in msg or 'limit' in msg or 'too many requests' in msg:
            raise RateLimitError(str(e))
        raise AdapterError(str(e))
