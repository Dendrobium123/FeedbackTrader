import os
import pandas as pd
# Use absolute import to reach the centralized system logger under `src.system`.
from src.system.log import get_logger

logger = get_logger(__name__)


def fetch(symbol, start, end, interval='1d', **kwargs):
    """Read historical data from a local CSV file.

    Behavior: if `symbol` is a file path ending with `.csv`, read it directly;
    otherwise look for `<symbol>.csv` under `data/csv/` (or `csv_base` if provided).

    Returns a pandas DataFrame with a DatetimeIndex and standard columns
    (Open, High, Low, Close, Adj Close, Volume) when available.
    """
    # support either a file path or a symbol name
    if symbol.lower().endswith('.csv'):
        path = symbol
    else:
        base = kwargs.get('csv_base', os.path.join(os.getcwd(), 'data', 'csv'))
        path = os.path.join(base, f"{symbol}.csv")

    if not os.path.exists(path):
        logger.debug("CSV adapter: file not found for %s -> %s", symbol, path)
        return pd.DataFrame()

    try:
        df = pd.read_csv(path, parse_dates=True, index_col=0)
    except Exception as e:
        logger.exception("CSV adapter failed to read %s: %s", path, e)
        return pd.DataFrame()

    # try to normalize common column names
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        if lc in ('open', 'open_price'):
            rename_map[c] = 'Open'
        elif lc in ('high',):
            rename_map[c] = 'High'
        elif lc in ('low',):
            rename_map[c] = 'Low'
        elif lc in ('close', 'close_price'):
            rename_map[c] = 'Close'
        elif lc in ('adj close', 'adj_close', 'adjclose'):
            rename_map[c] = 'Adj Close'
        elif lc in ('volume', 'vol'):
            rename_map[c] = 'Volume'

    if rename_map:
        df = df.rename(columns=rename_map)

    # ensure time index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # filter by time range
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    logger.info("CSV adapter: fetched %s rows for %s", len(df), symbol)
    return df
