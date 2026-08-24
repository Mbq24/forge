"""
Data Fetcher — pull OHLCV data from multiple sources.

Sources:
  1. yfinance (Yahoo Finance) — free, no API key needed
  2. Synthetic data generator — for testing and demos
  3. SQLite — existing webhook data

The synthetic generator creates realistic-ish OHLCV data with trends, volatility,
and patterns that the VT indicators can detect.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
import numpy as np

# Optional yfinance
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# yfinance rejects '1w' — it wants '1wk'. Normalize before download.
_YF_INTERVAL_FIX = {"1w": "1wk"}
# pandas date_range freq aliases (deprecated 'w' -> 'W')
_PD_FREQ_FIX = {"1w": "W", "1wk": "W"}


def _normalize_yf_interval(interval: str) -> str:
    return _YF_INTERVAL_FIX.get(interval, interval)


def _normalize_pd_freq(interval: str) -> str:
    return _PD_FREQ_FIX.get(interval, interval)


def fetch_ohlcv(
    ticker: str = "SYNTHETIC",
    interval: str = "1h",
    period: str = "7d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    allow_synthetic: bool = True,
) -> pd.DataFrame:
    """Fetch OHLCV data for a ticker.

    Falls back to synthetic data if yfinance fails or if ticker is 'SYNTHETIC'
    — UNLESS ``allow_synthetic`` is False, in which case a fetch failure
    raises RuntimeError instead. Trading/execution callers (portfolio-manager)
    MUST pass allow_synthetic=False: a synthetic fallback means trading on
    fabricated prices, which is worse than not trading at all.
    """
    if ticker == "SYNTHETIC":
        if not allow_synthetic:
            raise RuntimeError(f"Synthetic data requested for {ticker} but synthetic data is disallowed")
        return _generate_synthetic(interval=interval, period=period)

    if HAS_YFINANCE:
        try:
            yf_interval = _normalize_yf_interval(interval)
            if start and end:
                df = yf.download(ticker, start=start, end=end, interval=yf_interval, progress=False)
            else:
                df = yf.download(ticker, period=period, interval=yf_interval, progress=False)

            if df.empty:
                raise ValueError(f"No data returned for {ticker}")

            # Flatten MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]

            required = {"open", "high", "low", "close", "volume"}
            missing = required - set(df.columns)
            if missing:
                raise ValueError(f"Missing columns {missing}")

            return df
        except Exception as e:
            print(f"yfinance failed for {ticker}: {e}. Falling back to synthetic.")
            if not allow_synthetic:
                raise RuntimeError(
                    f"Real data unavailable for {ticker} ({e}); refusing synthetic fallback"
                ) from e
    else:
        print("yfinance not installed. Using synthetic data.")
        if not allow_synthetic:
            raise RuntimeError(f"yfinance not installed; cannot fetch real data for {ticker}")

    return _generate_synthetic(interval=interval, period=period)


def _generate_synthetic(interval: str = "1h", period: str = "7d") -> pd.DataFrame:
    """Generate realistic synthetic OHLCV data for demos.

    Creates data with:
      - A trend component (random walk with drift)
      - Volatility clusters
      - Occasional candlestick patterns (doji, hammers)
      - Realistic volume profile
    """
    np.random.seed(42)

    # Calculate number of bars
    intervals_per_day = {
        "1m": 1440, "5m": 288, "15m": 96, "30m": 48,
        "1h": 24, "4h": 6, "1d": 1,
    }
    npd = intervals_per_day.get(interval, 24)

    period_days = {"5d": 5, "7d": 7, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
    days = period_days.get(period, 7)
    n_bars = days * npd

    # Start date
    now = datetime.now()
    dates = pd.date_range(end=now, periods=n_bars, freq=_normalize_pd_freq(interval))

    # Price with drift + mean reversion
    np.random.seed(42)
    returns = np.random.randn(n_bars) * 0.003
    # Add some trending behavior
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.01
    # Add volatility clusters
    vol = 0.003 + 0.005 * (np.sin(np.linspace(0, 2 * np.pi, n_bars)) ** 2)
    noise = np.random.randn(n_bars) * vol

    log_returns = returns + trend + noise
    price = 50000 * np.exp(np.cumsum(log_returns)) + np.random.randn(n_bars) * 2
    price = np.maximum(price, 100)  # floor

    # Build OHLC from close price with realistic spreads
    close = price
    spread = close * 0.001 * np.random.rand(n_bars)
    open_p = close - spread + np.random.randn(n_bars) * 0.5
    high = np.maximum(close, open_p) + np.abs(np.random.randn(n_bars)) * close * 0.005
    low = np.minimum(close, open_p) - np.abs(np.random.randn(n_bars)) * close * 0.005

    # Volume
    volume = np.random.lognormal(mean=10, sigma=1.5, size=n_bars).astype(int)

    df = pd.DataFrame({
        "open": open_p,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)

    return df


def list_tickers(category: str = "crypto") -> list:
    """Return a list of common ticker symbols for the dropdown."""
    tickers = {
        "synthetic": ["SYNTHETIC"],
        "crypto": [
            "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
            "DOGE-USD", "ADA-USD", "LINK-USD", "AVAX-USD",
        ],
        "forex": [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "GC=F",
            "SI=F", "USDCAD=X", "AUDUSD=X",
        ],
        "stocks": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
            "META", "TSLA", "SPY", "QQQ", "IWM",
        ],
    }
    return tickers.get(category, tickers["synthetic"])


def format_data_preview(df: pd.DataFrame) -> str:
    """Return a string preview of the data for the LLM advisor."""
    close = df["close"]
    return (
        f"Shape: {df.shape}\n"
        f"Date range: {df.index[0]} to {df.index[-1]}\n"
        f"Close range: ${close.min():.2f} - ${close.max():.2f}\n"
        f"Latest close: ${close.iloc[-1]:.2f}\n"
        f"Volatility (ATR%): "
        f"{(df['high'] - df['low']).mean() / close.mean() * 100:.2f}%\n"
    )
