"""
Generators — output targets for DSL indicator definitions.

  - pinescript.py:  DSL → Pine Script v5 (paste into TradingView)
  - local.py:       DSL → pandas computation + Plotly charts
"""

from .pinescript import generate_pinescript
from .local import compute_indicators
