"""
Local Engine — Python/pandas computation of DSL indicators.

Evaluates an IndicatorDSL definition against a DataFrame of OHLCV data
using pandas/numpy. Produces the same output as the Pine Script version
but runs locally for backtesting and analysis.

This mirrors the volatility-trader master_indicators.py approach.
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np

from dsl.schema import IndicatorDSL
from dsl.indicators import INDICATOR_REGISTRY, PATTERN_MAP


def compute_indicators(df: pd.DataFrame, dsl: IndicatorDSL) -> pd.DataFrame:
    """Compute all indicators defined in a DSL against OHLCV data.

    Args:
        df: DataFrame with columns: open, high, low, close, volume (lowercase).
        dsl: Parsed indicator definition.

    Returns:
        DataFrame with original columns plus computed indicator columns.
    """
    result = df.copy()

    # Ensure required columns
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(result.columns.str.lower())
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # ── 1. Standard indicators ──
    for ind in dsl.indicators:
        _compute_standard(result, ind)

    # ── 2. Compound indicators (VT concepts) ──
    for comp in dsl.compounds:
        _compute_compound(result, comp, dsl)

    # ── 3. Candlestick patterns ──
    for pat_name in dsl.patterns:
        _compute_pattern(result, pat_name)

    # ── 4. Session encoding (if referenced in signals) ──
    if dsl.signals:
        all_text = " ".join(s.condition for s in dsl.signals.values())
        session_refs = {"session_asian", "session_london", "session_ny",
                        "session_london_ny_overlap", "session_slow"}
        if any(ref in all_text for ref in session_refs):
            _compute_session_features(result)

    # ── 5. Signals ──
    for sig_name, sig_def in dsl.signals.items():
        _compute_signal(result, sig_name, sig_def, dsl)

    return result


# ── Internal compute helpers ────────────────────────────────────────────────

def _compute_standard(df: pd.DataFrame, ind) -> None:
    """Compute a single standard indicator."""
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]
    info = INDICATOR_REGISTRY.get(ind.type)
    if not info:
        return

    src_name = ind.params.get("source", info.default_source)
    src = _resolve_source(df, src_name)

    if ind.type == "ema":
        period = ind.params.get("period", 20)
        df[ind.id] = src.ewm(span=period, adjust=False).mean()

    elif ind.type == "sma":
        period = ind.params.get("period", 20)
        df[ind.id] = src.rolling(period).mean()

    elif ind.type == "rsi":
        period = ind.params.get("period", 14)
        df[ind.id] = _rsi(src, period)

    elif ind.type == "atr":
        period = ind.params.get("period", 14)
        df[ind.id] = _atr(h, l, c, period)

    elif ind.type == "bb":
        period = ind.params.get("period", 20)
        stddev = ind.params.get("stddev", 2.0)
        middle = src.rolling(period).mean()
        dev = stddev * src.rolling(period).std()
        df[f"{ind.id}_middle"] = middle
        df[f"{ind.id}_upper"] = middle + dev
        df[f"{ind.id}_lower"] = middle - dev

    elif ind.type == "stochastic":
        k_period = ind.params.get("k_period", 14)
        d_period = ind.params.get("d_period", 3)
        k = _stoch(c, h, l, k_period)
        d = k.rolling(d_period).mean()
        df[f"{ind.id}_k"] = k
        df[f"{ind.id}_d"] = d

    elif ind.type == "macd":
        fast = ind.params.get("fast", 12)
        slow = ind.params.get("slow", 26)
        signal = ind.params.get("signal", 9)
        ema_fast = src.ewm(span=fast, adjust=False).mean()
        ema_slow = src.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        sig_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - sig_line
        df[f"{ind.id}_line"] = macd_line
        df[f"{ind.id}_signal"] = sig_line
        df[f"{ind.id}_hist"] = hist

    elif ind.type == "cci":
        period = ind.params.get("period", 20)
        tp = (h + l + c) / 3
        mean = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
        df[ind.id] = (tp - mean) / (0.015 * mad)

    elif ind.type == "vwap":
        df[ind.id] = (v * c).cumsum() / v.cumsum()

    elif ind.type == "volume":
        df[ind.id] = v

    elif ind.type == "obv":
        df[ind.id] = (np.sign(c.diff()) * v).fillna(0).cumsum()


def _compute_compound(df: pd.DataFrame, comp, dsl: IndicatorDSL) -> None:
    """Compute a VT compound indicator."""
    if comp.type == "ema_alignment":
        ema_ids = comp.params.get("emas", [])
        ema_cols = [eid for eid in ema_ids if eid in df.columns]
        if len(ema_cols) < 2:
            return
        bull = pd.DataFrame({
            f"{ema_cols[i]}_gt_{ema_cols[i+1]}": df[ema_cols[i]] > df[ema_cols[i+1]]
            for i in range(len(ema_cols) - 1)
        }).all(axis=1)
        bear = pd.DataFrame({
            f"{ema_cols[i]}_lt_{ema_cols[i+1]}": df[ema_cols[i]] < df[ema_cols[i+1]]
            for i in range(len(ema_cols) - 1)
        }).all(axis=1)
        df[comp.id] = np.select(
            [bull, bear],
            [1, -1],
            default=0
        ).astype(int)

    elif comp.type == "ema_spread":
        ema_ids = comp.params.get("emas", [])
        ema_cols = [eid for eid in ema_ids if eid in df.columns]
        if len(ema_cols) < 2:
            return
        max_vals = df[ema_cols].max(axis=1)
        min_vals = df[ema_cols].min(axis=1)
        df[comp.id] = (max_vals - min_vals) / df["close"]

    elif comp.type == "candle_proximity":
        ema_id = comp.params.get("ema", "")
        if ema_id in df.columns:
            atr = _atr(df["high"], df["low"], df["close"], 14)
            df[comp.id] = (df["close"] - df[ema_id]) / atr

    elif comp.type == "pull_count":
        ema_id = comp.params.get("ema", "ema_5")
        if ema_id in df.columns:
            above = df["close"] > df[ema_id]
            group = (above != above.shift()).cumsum()
            df[comp.id] = above.groupby(group).cumcount() + 1
            df[comp.id] = df[comp.id].where(above, 0)


def _compute_pattern(df: pd.DataFrame, pattern_name: str) -> None:
    """Compute a candlestick pattern boolean column."""
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]

    if pattern_name == "doji":
        body = abs(c - o)
        candle_range = h - l + 1e-10
        df[pattern_name] = ((body / candle_range) < 0.05).astype(int)
    elif pattern_name == "hammer":
        body = abs(c - o)
        upper_wick = h - np.maximum(c, o)
        lower_wick = np.minimum(c, o) - l
        candle_range = h - l + 1e-10
        df[pattern_name] = (
            (lower_wick >= 2 * body) &
            (upper_wick <= 0.3 * body) &
            (body / candle_range < 0.3)
        ).astype(int)
    elif pattern_name == "shooting_star":
        body = abs(c - o)
        upper_wick = h - np.maximum(c, o)
        lower_wick = np.minimum(c, o) - l
        candle_range = h - l + 1e-10
        df[pattern_name] = (
            (upper_wick >= 2 * body) &
            (lower_wick <= 0.3 * body) &
            (body / candle_range < 0.3)
        ).astype(int)
    elif pattern_name == "bullish_engulfing":
        prev_red = c.shift(1) < o.shift(1)
        prev_body = abs(c.shift(1) - o.shift(1))
        body = abs(c - o)
        df[pattern_name] = (
            prev_red & (c > o) &
            (o < o.shift(1)) & (c > c.shift(1)) &
            (body > prev_body)
        ).astype(int)
    elif pattern_name == "bearish_engulfing":
        prev_green = c.shift(1) > o.shift(1)
        prev_body = abs(c.shift(1) - o.shift(1))
        body = abs(c - o)
        df[pattern_name] = (
            prev_green & (c < o) &
            (o > o.shift(1)) & (c < c.shift(1)) &
            (body > prev_body)
        ).astype(int)
    elif pattern_name == "harami":
        prev_red = c.shift(1) < o.shift(1)
        prev_green = c.shift(1) > o.shift(1)
        df[pattern_name] = (
            ((prev_red & (c > o) & (o > c.shift(1)) & (c < o.shift(1))) |
             (prev_green & (c < o) & (o < c.shift(1)) & (c > o.shift(1))))
        ).astype(int)
    elif pattern_name == "morning_star":
        body = abs(c - o)
        avg_body = body.rolling(20).mean()
        long_red_2 = (c.shift(2) < o.shift(2)) & (abs(c.shift(2) - o.shift(2)) > avg_body.shift(2) * 1.5)
        doji_1 = (abs(c.shift(1) - o.shift(1)) / (h.shift(1) - l.shift(1) + 1e-10) < 0.05)
        df[pattern_name] = (
            long_red_2 & doji_1 & (c > o) &
            (c > (c.shift(2) + o.shift(2)) / 2)
        ).astype(int)
    elif pattern_name == "evening_star":
        body = abs(c - o)
        avg_body = body.rolling(20).mean()
        long_green_2 = (c.shift(2) > o.shift(2)) & (abs(c.shift(2) - o.shift(2)) > avg_body.shift(2) * 1.5)
        doji_1 = (abs(c.shift(1) - o.shift(1)) / (h.shift(1) - l.shift(1) + 1e-10) < 0.05)
        df[pattern_name] = (
            long_green_2 & doji_1 & (c < o) &
            (c < (c.shift(2) + o.shift(2)) / 2)
        ).astype(int)


def _compute_session_features(df: pd.DataFrame) -> None:
    """Add session encoding columns for gold market hours."""
    if not isinstance(df.index, pd.DatetimeIndex) and "timestamp" in df.columns:
        dt = pd.to_datetime(df["timestamp"])
        hour = dt.dt.hour
    elif isinstance(df.index, pd.DatetimeIndex):
        hour = df.index.hour
    else:
        return
    df["session_asian"] = ((hour >= 0) & (hour < 8)).astype(int)
    df["session_london"] = ((hour >= 8) & (hour < 16)).astype(int)
    df["session_ny"] = ((hour >= 13) & (hour < 22)).astype(int)
    df["session_london_ny_overlap"] = ((hour >= 13) & (hour < 16)).astype(int)
    df["session_slow"] = ((hour >= 22) | (hour < 2)).astype(int)


def _compute_signal(df: pd.DataFrame, sig_name: str, sig_def, dsl: IndicatorDSL) -> None:
    """Evaluate a signal condition and add a boolean column."""
    from dsl.conditions import parse_condition, collect_identifiers
    try:
        ast = parse_condition(sig_def.condition)
        col_name = f"signal_{sig_name}"
        df[col_name] = _evaluate_ast(df, ast)
    except Exception as e:
        col_name = f"signal_{sig_name}"
        df[col_name] = False


def _evaluate_ast(df: pd.DataFrame, node) -> pd.Series:
    """Recursively evaluate a condition AST against a DataFrame."""
    from dsl.conditions import Identifier, Number, Compare, LogicOp, Not, Crossover, Crossunder
    if isinstance(node, Identifier):
        if node.name in df.columns:
            return df[node.name].astype(float)
        # Check for pattern name
        from dsl.indicators import PATTERN_MAP
        if node.name in PATTERN_MAP:
            df_pat = df.copy()
            _compute_pattern(df_pat, node.name)
            return df_pat[node.name].astype(float)
        # Session features
        session_cols = {"session_asian", "session_london", "session_ny",
                        "session_london_ny_overlap", "session_slow"}
        if node.name in session_cols:
            if node.name in df.columns:
                return df[node.name].astype(float)
            _compute_session_features(df)
            return df[node.name].astype(float)
        return pd.Series(0.0, index=df.index)
    elif isinstance(node, Number):
        return pd.Series(node.value, index=df.index)
    elif isinstance(node, Compare):
        left = _evaluate_ast(df, node.left)
        right = _evaluate_ast(df, node.right)
        if node.op == ">":    return (left > right).astype(float)
        if node.op == "<":    return (left < right).astype(float)
        if node.op == ">=":   return (left >= right).astype(float)
        if node.op == "<=":   return (left <= right).astype(float)
        if node.op == "==":   return (left == right).astype(float)
        if node.op == "!=":   return (left != right).astype(float)
    elif isinstance(node, LogicOp):
        left = _evaluate_ast(df, node.left)
        right = _evaluate_ast(df, node.right)
        if node.op.upper() == "AND":
            return (left.astype(bool) & right.astype(bool)).astype(float)
        if node.op.upper() == "OR":
            return (left.astype(bool) | right.astype(bool)).astype(float)
    elif isinstance(node, Not):
        operand = _evaluate_ast(df, node.operand)
        return (~operand.astype(bool)).astype(float)
    elif isinstance(node, Crossover):
        left = _evaluate_ast(df, node.left)
        right = _evaluate_ast(df, node.right)
        # Crossover: left was <= right last bar, and is > right this bar
        prev_left = left.shift(1)
        prev_right = right.shift(1)
        return ((prev_left <= prev_right) & (left > right)).astype(float)
    elif isinstance(node, Crossunder):
        left = _evaluate_ast(df, node.left)
        right = _evaluate_ast(df, node.right)
        prev_left = left.shift(1)
        prev_right = right.shift(1)
        return ((prev_left >= prev_right) & (left < right)).astype(float)
    raise ValueError(f"Unknown node: {node}")


# ── Math helpers ────────────────────────────────────────────────────────────

def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - close.shift(1)),
            np.abs(low - close.shift(1))
        )
    )
    return tr.rolling(period).mean()


def _stoch(close: pd.Series, high: pd.Series, low: pd.Series, period: int) -> pd.Series:
    low_min = low.rolling(period).min()
    high_max = high.rolling(period).max()
    return 100 * (close - low_min) / (high_max - low_min + 1e-10)


def _resolve_source(df: pd.DataFrame, src_name: str) -> pd.Series:
    """Resolve a source expression like 'hlc3' or 'ohlc4'."""
    if src_name == "close":  return df["close"]
    if src_name == "open":   return df["open"]
    if src_name == "high":   return df["high"]
    if src_name == "low":    return df["low"]
    if src_name == "volume": return df["volume"]
    if src_name == "hlc3":   return (df["high"] + df["low"] + df["close"]) / 3
    if src_name == "hl2":    return (df["high"] + df["low"]) / 2
    if src_name == "ohlc4":  return (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    return df.get(src_name, df["close"])
