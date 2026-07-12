"""
DockerTVWebhook DSL — Declarative Indicator Definition Language

Defines indicators in YAML, compiles to Pine Script (TradingView) or
local Python/pandas computation.

Key concepts borrowed from volatility-trader's Master Indicator Suite:
  - EMA families (5/8/13/21/50/75) with alignment scoring
  - Candle-to-EMA proximity (body touching EMA = entry trigger)
  - Candlestick pattern detection (doji, hammer, engulfing, etc.)
  - Green candle pull count (consecutive candles above EMA)
  - Session encoding (Asian/London/NY time blocks)
"""

from dsl.schema import IndicatorDSL, IndicatorDef, CompoundIndicator, PatternDef, SignalDef, PlotDef
from dsl.indicators import INDICATOR_REGISTRY, get_indicator_info
from dsl.conditions import parse_condition, to_pine_condition, collect_identifiers

__all__ = [
    "IndicatorDSL", "IndicatorDef", "CompoundIndicator",
    "PatternDef", "SignalDef", "PlotDef",
    "INDICATOR_REGISTRY", "get_indicator_info",
    "parse_condition", "to_pine_condition", "collect_identifiers",
]
