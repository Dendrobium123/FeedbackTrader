import os
import pandas as pd
from ..exceptions import RateLimitError, AdapterError
# Use absolute import to reach the centralized system logger under `src.system`.
from src.system.log import get_logger

logger = get_logger(__name__)

def fetch(symbol, start, end, interval='1d', adjusted=True, **kwargs): 
    """Fetch historical data using akshare and return a DataFrame (DatetimeIndex).

    Currently supports daily data via `ak.stock_zh_a_daily`. Other intervals are
    not implemented and will raise an AdapterError.
    """
    try:
        # import akshare lazily to avoid import-time dependency
        try:
            import akshare as ak  # type: ignore
        except Exception as ie:
            logger.exception("akshare import failed: %s", ie)
            raise AdapterError("akshare is not installed") from ie

        logger.debug("akshare adapter: fetching %s %s-%s interval=%s", symbol, start, end, interval)
        if interval in ('1d', 'daily'):
            # akshare expects dates like YYYYMMDD or YYYY-MM-DD depending on function
            df = ak.stock_zh_a_daily(symbol=symbol, start_date=start, end_date=end)
            if df is None or df.empty:
                logger.info("akshare adapter: no data for %s", symbol)
                return pd.DataFrame()

            # akshare may return a 'date' column; convert to DatetimeIndex if present
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            logger.info("akshare adapter: fetched %s rows for %s", len(df), symbol)
            return df
        else:
            raise AdapterError(f"Interval not supported by akshare adapter: {interval}")
    except AdapterError:
        # re-raise AdapterError directly
        raise
    except Exception as e:
        msg = str(e).lower()
        logger.exception("akshare adapter error for %s: %s", symbol, e)
        if 'rate' in msg or 'limit' in msg or 'too many requests' in msg:
            raise RateLimitError(str(e))
        raise AdapterError(str(e))