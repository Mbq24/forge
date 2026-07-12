"""
DSL Schema — YAML-backed indicator definition types.

Top-level structure:

  name: str                    # unique indicator name
  description: str             # what it does
  timeframe: str               # context hint (1h, 4h, 1d, etc.)
  indicators: list             # standard indicator computations
  compounds: list              # derived/composite indicators
  patterns: list               # candlestick patterns to detect
  plots: list                  # what to render
  signals: dict                # entry/exit/stop conditions

Example:

  name: "vt-breakout"
  description: "EMA alignment + candlestick confirmation"
  timeframe: "1h"
  indicators:
    - id: ema_fast
      type: ema
      params: { period: 5 }
    - id: rsi
      type: rsi
      params: { period: 14 }
  compounds:
    - id: alignment
      type: ema_alignment
      params: { emas: [ema_fast, ema_slow] }
  patterns: ["hammer", "doji"]
  plots:
    - ema_fast
    - close
  signals:
    entry: "alignment == 1 AND hammer"
    exit: "rsi > 70"
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
import yaml


# ── Indicator definition ────────────────────────────────────────────────────

@dataclass
class IndicatorDef:
    """A single indicator computation.

    id:      unique reference name (used in plots/signals/compounds)
    type:    one of the registered indicator types (ema, rsi, atr, bb, etc.)
    params:  type-specific parameters (period, source, stddev, etc.)
    """
    id: str
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


# ── Compound indicators ─────────────────────────────────────────────────────

@dataclass
class CompoundIndicator:
    """A derived indicator computed from other indicator IDs.

    id:      unique reference name
    type:    compound type (ema_alignment, ema_spread, candle_proximity, etc.)
    params:  type-specific; often includes an 'emas' or 'indicators' list of refs
    """
    id: str
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


# ── Pattern definitions ─────────────────────────────────────────────────────

@dataclass
class PatternDef:
    """One candlestick pattern to detect.

    Patterns map to Pine's built-in ta.*() functions and to local
    pandas equivalents. Common: doji, hammer, shooting_star,
    bullish_engulfing, bearish_engulfing, morning_star, evening_star.
    """
    name: str
    enabled: bool = True


# ── Plot definitions ────────────────────────────────────────────────────────

@dataclass
class PlotDef:
    """What to render on the chart.

    ref:    id of an indicator, compound, or price field (open/high/low/close/volume)
    style:  line, histogram, shape, hline, etc.
    color:  optional CSS/hex color
    """
    ref: str
    style: str = "line"
    color: Optional[str] = None


# ── Signal conditions ───────────────────────────────────────────────────────

@dataclass
class SignalDef:
    """Entry, exit, or stop condition expressed as a boolean expression.

    Expression language supports:
      - Indicator references:  ema_fast, rsi, alignment
      - Price references:      close, open, high, low, volume
      - Comparisons:           >, <, >=, <=, ==, !=
      - Logical:               AND, OR, NOT
      - Parentheses:           (expression)
      - Pattern names:         hammer, doji, engulfing  (treats as bool)
      - Session names:         session_ny, session_london

    Examples:
      "rsi > 70"
      "rsi < 30 AND hammer"
      "ema_alignment == 1 AND NOT doji"
      "close > ema_fast AND rsi > 50"
    """
    condition: str


# ── Top-level DSL definition ────────────────────────────────────────────────

@dataclass
class IndicatorDSL:
    """Complete indicator DSL definition, parsed from YAML."""

    name: str
    description: str = ""
    timeframe: str = "1h"

    indicators: List[IndicatorDef] = field(default_factory=list)
    compounds: List[CompoundIndicator] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    plots: List[PlotDef] = field(default_factory=list)
    signals: Dict[str, SignalDef] = field(default_factory=dict)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Convert to a plain dict for YAML serialisation."""
        d = {
            "name": self.name,
            "description": self.description,
            "timeframe": self.timeframe,
        }
        if self.indicators:
            d["indicators"] = [
                {"id": i.id, "type": i.type, "params": i.params}
                for i in self.indicators
            ]
        if self.compounds:
            d["compounds"] = [
                {"id": c.id, "type": c.type, "params": c.params}
                for c in self.compounds
            ]
        if self.patterns:
            d["patterns"] = self.patterns
        if self.plots:
            d["plots"] = [
                {"ref": p.ref, "style": p.style}
                if not p.color
                else {"ref": p.ref, "style": p.style, "color": p.color}
                for p in self.plots
            ]
        if self.signals:
            d["signals"] = {
                k: {"condition": v.condition}
                for k, v in self.signals.items()
            }
        return d

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    # ── Factory ────────────────────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, text: str) -> "IndicatorDSL":
        """Parse a YAML string into an IndicatorDSL."""
        raw = yaml.safe_load(text)
        if not raw:
            raise ValueError("Empty YAML")

        indicators = [
            IndicatorDef(id=i["id"], type=i["type"], params=i.get("params", {}))
            for i in raw.get("indicators", [])
        ]
        compounds = [
            CompoundIndicator(id=c["id"], type=c["type"], params=c.get("params", {}))
            for c in raw.get("compounds", [])
        ]
        patterns = raw.get("patterns", [])
        plots = [
            PlotDef(ref=p["ref"], style=p.get("style", "line"), color=p.get("color"))
            for p in raw.get("plots", [])
        ]
        signals = {}
        for k, v in raw.get("signals", {}).items():
            if isinstance(v, str):
                # Flat format:  entry: "rsi > 30"
                signals[k] = SignalDef(condition=v)
            elif isinstance(v, dict) and "condition" in v:
                # Nested format:  entry: { condition: "rsi > 30" }
                signals[k] = SignalDef(condition=v["condition"])
            else:
                raise ValueError(f"Invalid signal format for '{k}': {v}")

        return cls(
            name=raw["name"],
            description=raw.get("description", ""),
            timeframe=raw.get("timeframe", "1h"),
            indicators=indicators,
            compounds=compounds,
            patterns=patterns,
            plots=plots,
            signals=signals,
        )

    @classmethod
    def from_yaml_file(cls, path: str) -> "IndicatorDSL":
        """Load from a YAML file."""
        with open(path) as f:
            return cls.from_yaml(f.read())

    # ── Validation ─────────────────────────────────────────────────────────

    def validate(self) -> List[str]:
        """Run validation checks. Returns list of error messages (empty = valid)."""
        errors = []

        if not self.name:
            errors.append("name is required")
        if not self.indicators and not self.compounds and not self.patterns:
            errors.append("at least one indicator, compound, or pattern is required")

        # Check for duplicate IDs
        all_ids = [i.id for i in self.indicators] + [c.id for c in self.compounds]
        duplicates = set(i for i in all_ids if all_ids.count(i) > 1)
        for d in duplicates:
            errors.append(f"duplicate id: {d}")

        # Validate all references in plots — including multi-output subrefs
        valid_refs = set(all_ids) | {"open", "high", "low", "close", "volume"}
        # Add known sub-references from multi-output indicators
        for ind in self.indicators:
            if ind.type == "bb":
                valid_refs.add(f"{ind.id}_middle")
                valid_refs.add(f"{ind.id}_upper")
                valid_refs.add(f"{ind.id}_lower")
            elif ind.type == "stochastic":
                valid_refs.add(f"{ind.id}_k")
                valid_refs.add(f"{ind.id}_d")
            elif ind.type == "macd":
                valid_refs.add(f"{ind.id}_line")
                valid_refs.add(f"{ind.id}_signal")
                valid_refs.add(f"{ind.id}_hist")
        for p in self.plots:
            if p.ref not in valid_refs:
                errors.append(f"plot ref '{p.ref}' not found in indicators or compounds")

        # Validate signal conditions (basic check — full parse happens at runtime)
        valid_names = valid_refs | set(self.patterns) | {
            "session_asian", "session_london", "session_ny",
            "session_london_ny_overlap", "session_slow",
        }
        for name, sig in self.signals.items():
            # Check that referenced names exist
            tokens = sig.condition.replace("(", " ").replace(")", " ").split()
            refs = {
                t for t in tokens
                if t.upper() not in ("AND", "OR", "NOT", "TRUE", "FALSE")
                and not t.lstrip("-").replace(".", "").isdigit()
                and t not in (">", "<", ">=", "<=", "==", "!=", "+", "-", "*", "/")
            }
            unknown = refs - valid_names
            if unknown:
                errors.append(
                    f"signal '{name}': unknown references {sorted(unknown)}"
                )

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0
