"""Simple moving-average crossover strategy.

This strategy keeps the most recent close prices and computes a short and
long simple moving average (SMA). When the short SMA crosses above the
long SMA the strategy emits a ``buy`` signal; when it crosses below it
emits a ``sell`` signal. The implementation is intentionally small and
framework-agnostic: it uses the `Strategy` interface defined in
`src/strategy/base.py`.

Config keys (in `config` dict passed to constructor):
- ``short_window``: int, default 5
- ``long_window``: int, default 20
- ``size``: optional order size when signaling (default 1)

Returned signal format (dict):
  {"signal": "buy"|"sell"|None, "size": int}

"""
from __future__ import annotations

from typing import Any, Dict, Optional
from collections import deque

import pandas as pd

from .base import Strategy


class MovingAverage(Strategy):
	def __init__(self, config: Dict[str, Any]):
		"""Create a moving-average crossover strategy.

		The constructor expects a `config` dict (see module docstring).
		"""
		super().__init__(config)
		self.short_window: int = int(config.get("short_window", 5))
		self.long_window: int = int(config.get("long_window", 20))
		if self.short_window >= self.long_window:
			raise ValueError("short_window must be smaller than long_window")
		self.size: int = int(config.get("size", 1))

		# store recent close prices; maxlen ensures we only keep needed history
		self.prices: deque[float] = deque(maxlen=self.long_window)

		# current position: positive = long, negative = short, 0 = flat
		self.position: int = 0

		# last computed SMAs (for cross detection)
		self._last_short_sma: Optional[float] = None
		self._last_long_sma: Optional[float] = None

	def on_start(self) -> None:
		"""Reset internal state on strategy start."""
		self.prices.clear()
		self.position = 0
		self._last_short_sma = None
		self._last_long_sma = None

	def on_bar(self, bar: pd.Series) -> None:
		"""Handle a new bar (expects `bar` to contain a `close` field)."""
		# Accept either a pandas Series with index 'close' or a mapping
		close = None
		if isinstance(bar, pd.Series) and "close" in bar.index:
			close = float(bar.loc["close"])
		elif isinstance(bar, dict) and "close" in bar:
			close = float(bar["close"])
		else:
			# try attribute access fallback
			try:
				close = float(getattr(bar, "close"))
			except Exception:
				raise ValueError("bar must provide a 'close' price (Series/dict/object)")

		self.prices.append(close)

	def generate_signals(self) -> Dict[str, Optional[Any]]:
		"""Compute SMAs and return a signal dict.

		Returns a dict: {"signal": "buy"/"sell"/None, "size": int}
		"""
		if len(self.prices) < self.long_window:
			return {"signal": None, "size": 0}

		ser = pd.Series(list(self.prices))
		short_sma = float(ser.rolling(window=self.short_window).mean().iloc[-1])
		long_sma = float(ser.rolling(window=self.long_window).mean().iloc[-1])

		signal = None

		# detect crossover using previous values when available
		if self._last_short_sma is not None and self._last_long_sma is not None:
			# short crosses above long -> buy
			if self._last_short_sma <= self._last_long_sma and short_sma > long_sma:
				signal = "buy"
			# short crosses below long -> sell
			elif self._last_short_sma >= self._last_long_sma and short_sma < long_sma:
				signal = "sell"

		# update last sma values for next call
		self._last_short_sma = short_sma
		self._last_long_sma = long_sma

		# update position tracker conservatively (framework should execute orders)
		if signal == "buy":
			self.position = 1
		elif signal == "sell":
			self.position = 0

		return {"signal": signal, "size": (self.size if signal else 0)}

	def on_stop(self) -> None:
		"""Called when strategy is stopped; no-op for this simple example."""
		return

