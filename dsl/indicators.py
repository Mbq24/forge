"""
Indicator Registry — maps indicator types to their metadata.

Each entry defines:
  - name / category
  - required & optional params with defaults
  - pine_snippet: Pine Script v5 expression (with {param} placeholders)
  - description: what it measures
  - vt_concept: True if derived from volatility-trader's Master Indicator Suite

VT concepts integrated:
  ema_alignment, ema_spread, candle_proximity, pull_count,
  candlestick patterns, session encoding
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class IndicatorInfo:
    type_name: str
    category: str
    description: str
    params: Dict[str, dict] = field(default_factory=dict)
    pine_snippet: str = ""
    vt_concept: bool = False
    returns: str = "float"  # what the indicator returns
    default_source: str = "close"


# ── REGISTRY ────────────────────────────────────────────────────────────────

INDICATOR_REGISTRY: Dict[str, IndicatorInfo] = {}


def _reg(info: IndicatorInfo) -> None:
    INDICATOR_REGISTRY[info.type_name] = info


# ════════════════════════════════════════════════════════════════════════════
# STANDARD INDICATORS (overlay / pane)
# ════════════════════════════════════════════════════════════════════════════

_reg(IndicatorInfo(
    type_name="ema",
    category="moving_average",
    description="Exponential Moving Average — weights recent prices more heavily",
    params={
        "period": {"type": "int", "required": True, "default": 20, "min": 1},
        "source": {"type": "source", "required": False, "default": "close"},
    },
    pine_snippet="ta.ema({source}, {period})",
    default_source="close",
))

_reg(IndicatorInfo(
    type_name="sma",
    category="moving_average",
    description="Simple Moving Average — average over N periods",
    params={
        "period": {"type": "int", "required": True, "default": 20, "min": 1},
        "source": {"type": "source", "required": False, "default": "close"},
    },
    pine_snippet="ta.sma({source}, {period})",
    default_source="close",
))

_reg(IndicatorInfo(
    type_name="rsi",
    category="momentum",
    description="Relative Strength Index — overbought/oversold (0-100)",
    params={
        "period": {"type": "int", "required": False, "default": 14, "min": 1},
        "source": {"type": "source", "required": False, "default": "close"},
    },
    pine_snippet="ta.rsi({source}, {period})",
))

_reg(IndicatorInfo(
    type_name="atr",
    category="volatility",
    description="Average True Range — volatility measure",
    params={
        "period": {"type": "int", "required": False, "default": 14, "min": 1},
    },
    pine_snippet="ta.atr({period})",
))

_reg(IndicatorInfo(
    type_name="bb",
    category="volatility",
    description="Bollinger Bands — 3 lines: middle, upper, lower",
    params={
        "period": {"type": "int", "required": False, "default": 20, "min": 2},
        "stddev": {"type": "float", "required": False, "default": 2.0, "min": 0.5},
        "source": {"type": "source", "required": False, "default": "close"},
    },
    pine_snippet="""
middle = ta.sma({source}, {period})
dev = {stddev} * ta.stdev({source}, {period})
upper = middle + dev
lower = middle - dev""".strip(),
))

_reg(IndicatorInfo(
    type_name="stochastic",
    category="momentum",
    description="Stochastic Oscillator — %K and %D lines (0-100)",
    params={
        "k_period": {"type": "int", "required": False, "default": 14, "min": 1},
        "d_period": {"type": "int", "required": False, "default": 3, "min": 1},
    },
    pine_snippet="""
k = ta.stoch({source}, high, low, {k_period})
d = ta.sma(k, {d_period})""".strip(),
    default_source="close",
))

_reg(IndicatorInfo(
    type_name="macd",
    category="momentum",
    description="MACD — Moving Average Convergence/Divergence",
    params={
        "fast": {"type": "int", "required": False, "default": 12, "min": 1},
        "slow": {"type": "int", "required": False, "default": 26, "min": 1},
        "signal": {"type": "int", "required": False, "default": 9, "min": 1},
    },
    pine_snippet="""
[macd_line, signal_line, hist_line] = ta.macd({source}, {fast}, {slow}, {signal})""".strip(),
    default_source="close",
))

_reg(IndicatorInfo(
    type_name="cci",
    category="momentum",
    description="Commodity Channel Index — cyclical deviation from mean",
    params={
        "period": {"type": "int", "required": False, "default": 20, "min": 1},
        "source": {"type": "source", "required": False, "default": "hlc3"},
    },
    pine_snippet="ta.cci(high, low, close, {period})",
    default_source="close",
))

_reg(IndicatorInfo(
    type_name="vwap",
    category="volume",
    description="Volume Weighted Average Price",
    params={},
    pine_snippet="ta.vwap",
))

_reg(IndicatorInfo(
    type_name="volume",
    category="volume",
    description="Raw volume",
    params={},
    pine_snippet="volume",
))

_reg(IndicatorInfo(
    type_name="obv",
    category="volume",
    description="On-Balance Volume — cumulative volume flow",
    params={},
    pine_snippet="ta.obv",
))


# ════════════════════════════════════════════════════════════════════════════
# VT CONCEPTS (volatility-trader Master Indicator Suite)
# ════════════════════════════════════════════════════════════════════════════

_reg(IndicatorInfo(
    type_name="ema_alignment",
    category="vt_concept",
    description="""EMA alignment score: +1 if all EMAs are bull-ordered
    (fastest > second > third > ... > slowest), -1 if bear-reversed, 0 if mixed.
    Requires 2+ EMA indicators referenced by id.""",
    params={
        "emas": {
            "type": "list[str]",
            "required": True,
            "description": "Ordered list of EMA indicator IDs, fastest first",
        },
    },
    vt_concept=True,
    returns="int",
))

_reg(IndicatorInfo(
    type_name="ema_spread",
    category="vt_concept",
    description="""Normalised spread between widest and narrowest EMA.
    Tight spread = consolidation = breakout imminent.""",
    params={
        "emas": {
            "type": "list[str]",
            "required": True,
            "description": "List of EMA indicator IDs",
        },
    },
    vt_concept=True,
    returns="float",
))

_reg(IndicatorInfo(
    type_name="candle_proximity",
    category="vt_concept",
    description="""Distance from close to a reference EMA, normalised by ATR.
    Used for the Legacy Class concept: candle body touching the EMA = entry trigger.""",
    params={
        "ema": {
            "type": "str",
            "required": True,
            "description": "Reference EMA indicator ID",
        },
    },
    vt_concept=True,
    returns="float",
))

_reg(IndicatorInfo(
    type_name="pull_count",
    category="vt_concept",
    description="""Consecutive candles above the 5 EMA (pull count).
    After 3+ candles, expect a pullback / mean reversion.""",
    params={
        "ema": {
            "type": "str",
            "required": False,
            "default": "ema_5",
            "description": "EMA indicator ID to measure pull from",
        },
    },
    vt_concept=True,
    returns="int",
))


# ════════════════════════════════════════════════════════════════════════════
# CANDLESTICK PATTERNS (mapped by name in DSL, not computed as indicators)
# These are detected by Pine's built-in ta.*() functions.
# ════════════════════════════════════════════════════════════════════════════

PATTERN_MAP = {
    "doji":               "math.abs(close - open) <= (high - low) * 0.05",
    "hammer":             "(high - low) > 3 * math.abs(close - open) and (close - math.min(open, close)) >= 2 * math.abs(close - open) and (math.max(open, close) - low) / (high - low) > 0.6",
    "shooting_star":      "(high - low) > 3 * math.abs(close - open) and (math.max(open, close) - close) >= 2 * math.abs(close - open) and (high - math.min(open, close)) / (high - low) > 0.6",
    "bullish_engulfing":  "close > open and close[1] < open[1] and close >= open[1] and open <= close[1]",
    "bearish_engulfing":  "close < open and close[1] > open[1] and close <= open[1] and open >= close[1]",
    "harami":             "(close < open and close[1] > open[1] and close > close[1] and open < open[1]) or (close > open and close[1] < open[1] and close < close[1] and open > open[1])",
    "morning_star":       "close[2] < open[2] and math.abs(close[2] - open[2]) > math.abs(close[1] - open[1]) * 2 and math.abs(close[1] - open[1]) <= (high[1] - low[1]) * 0.1 and close > open and close > (close[2] + open[2]) / 2",
    "evening_star":       "close[2] > open[2] and math.abs(close[2] - open[2]) > math.abs(close[1] - open[1]) * 2 and math.abs(close[1] - open[1]) <= (high[1] - low[1]) * 0.1 and close < open and close < (close[2] + open[2]) / 2",
    "three_white_soldiers": "close > open and close[1] > open[1] and close[2] > open[2] and close > close[1] and close[1] > close[2]",
    "three_black_crows":  "close < open and close[1] < open[1] and close[2] < open[2] and close < close[1] and close[1] < close[2]",
}

# ── Helper ──────────────────────────────────────────────────────────────────

def get_indicator_info(type_name: str) -> Optional[IndicatorInfo]:
    """Look up an indicator or pattern by name."""
    return INDICATOR_REGISTRY.get(type_name)


def list_indicators(category: Optional[str] = None) -> List[IndicatorInfo]:
    """List all registered indicators, optionally filtered by category."""
    items = list(INDICATOR_REGISTRY.values())
    if category:
        items = [i for i in items if i.category == category]
    return sorted(items, key=lambda i: i.type_name)
