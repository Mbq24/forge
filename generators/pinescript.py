"""
Pine Script v5 Generator

Converts a parsed IndicatorDSL into valid TradingView Pine Script v5 code.

Supports:
  - Standard indicators (EMA, SMA, RSI, ATR, BB, Stochastic, MACD, CCI, VWAP)
  - VT concepts (ema_alignment, ema_spread, candle_proximity, pull_count)
  - Candlestick patterns (doji, hammer, engulfing, etc.)
  - Signal conditions with buy/sell markers
  - Session/time-of-day blocks (for Gold market hours)
"""

from typing import List, Set, Dict
from dsl.schema import IndicatorDSL, IndicatorDef, CompoundIndicator, PlotDef, SignalDef
from dsl.indicators import INDICATOR_REGISTRY, PATTERN_MAP, IndicatorInfo
from dsl.conditions import parse_condition, to_pine_condition, collect_identifiers

# ── Helpers ─────────────────────────────────────────────────────────────────

def _pine_var_name(name: str) -> str:
    """Convert a DSL id to a valid Pine Script variable name.
    Replace hyphens with underscores (Pine doesn't allow hyphens in names)."""
    return name.replace("-", "_").replace(" ", "_")


def _resolve_indicator_ref(ref: str, dsl: IndicatorDSL) -> str:
    """Get the Pine variable name for an indicator/compound ID, or pass through
    for built-in price references (close, open, high, low, volume)."""
    price_refs = {"open", "high", "low", "close", "volume", "hlc3", "hl2", "ohlc4"}
    if ref in price_refs:
        return ref
    return _pine_var_name(ref)


def _indent(level: int = 1) -> str:
    return "  " * level


# ── Main Generator ──────────────────────────────────────────────────────────

def generate_pinescript(dsl: IndicatorDSL) -> str:
    """Generate Pine Script v5 code from a parsed DSL definition."""
    lines: List[str] = []
    _add_header(lines, dsl)

    # Track variable names for each indicator
    ind_vars: Dict[str, str] = {}  # dsl id -> pine var name

    # ── Standard indicators ──
    if dsl.indicators:
        lines.append("// === INDICATOR COMPUTATIONS ===")
        for ind in dsl.indicators:
            var_name = _pine_var_name(ind.id)
            ind_vars[ind.id] = var_name
            line = _render_indicator(ind, var_name)
            lines.append(line)

    # ── Compound indicators (VT concepts) ──
    if dsl.compounds:
        if not dsl.indicators:
            lines.append("// === INDICATOR COMPUTATIONS ===")
        lines.append("")
        lines.append("// === VT CONCEPTS (derived indicators) ===")
        for comp in dsl.compounds:
            var_name = _pine_var_name(comp.id)
            ind_vars[comp.id] = var_name
            code_lines = _render_compound(comp, ind_vars, dsl)
            lines.extend(code_lines)

    # ── Candlestick pattern vars ──
    pattern_vars: Dict[str, str] = {}
    for pat_name in dsl.patterns:
        pat_var = _pine_var_name(pat_name)
        pattern_vars[pat_name] = pat_var
        if pat_name in PATTERN_MAP:
            pine_fn = PATTERN_MAP[pat_name]
            lines.append(f"{pat_var} = {pine_fn}")

    # ── Session/time vars (if referenced in signals) ──
    all_signal_exprs = [s.condition for s in dsl.signals.values()]
    all_refs: Set[str] = set()
    for expr in all_signal_exprs:
        try:
            ast = parse_condition(expr)
            all_refs.update(collect_identifiers(ast))
        except Exception:
            pass

    session_refs = {"session_asian", "session_london", "session_ny",
                    "session_london_ny_overlap", "session_slow"}
    has_sessions = bool(session_refs & all_refs)

    if has_sessions:
        lines.append("")
        lines.append("// === SESSION ENCODING (Gold market hours) ===")
        lines.append("hour = hour(time)")
        lines.append("session_asian = hour >= 0 and hour < 8")
        lines.append("session_london = hour >= 8 and hour < 16")
        lines.append("session_ny = hour >= 13 and hour < 22")
        lines.append("session_london_ny_overlap = hour >= 13 and hour < 16")
        lines.append("session_slow = hour >= 22 or hour < 2")

    # ── Auto-generate VT concepts referenced in signals but not in compounds ──
    existing_compound_ids = {comp.id for comp in dsl.compounds}
    # Find available EMAs sorted by period (shortest first)
    ema_ids = sorted(
        [ind for ind in dsl.indicators if ind.type == "ema"],
        key=lambda i: i.params.get("period", 999)
    )
    ema_names = [e.id for e in ema_ids]
    auto_generated = False

    def _ensure_concept_section():
        nonlocal auto_generated
        if not auto_generated:
            if dsl.compounds:
                lines.append("")
            else:
                lines.append("")
                lines.append("// === VT CONCEPTS (derived indicators) ===")
            auto_generated = True

    for ref_name in all_refs:
        if ref_name in existing_compound_ids:
            continue  # already explicitly defined

        if ref_name in ("alignment", "spread") and len(ema_names) >= 2:
            # Use whatever EMAs are available (shortest 3, or 2 if that's all)
            used_emas = ema_names[:3]
            _ensure_concept_section()
            comp = CompoundIndicator(
                id=ref_name, type=f"ema_{ref_name}",
                params={"emas": used_emas}
            )
            var_name = _pine_var_name(ref_name)
            ind_vars[ref_name] = var_name
            lines.append(f"// auto-generated from signal reference ({', '.join(used_emas)})")
            lines.extend(_render_compound(comp, ind_vars, dsl))

        elif ref_name in ("pull", "proximity") and ema_names:
            # Use shortest-period EMA
            target_ema = ema_names[0]
            _ensure_concept_section()
            comp = CompoundIndicator(
                id=ref_name, type="pull_count" if ref_name == "pull" else "candle_proximity",
                params={"ema": target_ema}
            )
            var_name = _pine_var_name(ref_name)
            ind_vars[ref_name] = var_name
            lines.append(f"// auto-generated from signal reference ({target_ema})")
            lines.extend(_render_compound(comp, ind_vars, dsl))

    # ── Plots ──
    lines.append("")
    lines.append("// === PLOTS ===")

    # Determine which indicators go in overlay vs separate pane
    overlay_plots: List[str] = []  # var names for overlay
    pane_plots: List[str] = []     # var names for separate pane

    if dsl.plots:
        # User-defined plots — use explicit PlotDefs
        for plot in dsl.plots:
            info = _get_indicator_info_for_plot(plot, dsl)
            var_ref = _resolve_indicator_ref(plot.ref, dsl)
            color = plot.color or _auto_color(len(lines), info.type_name if info else "")
            if info and info.category in ("momentum",) and info.type_name not in ("macd",):
                pane_plots.append(f"plot({var_ref}, \"{_pine_var_name(plot.ref)}\", {color})")
            else:
                overlay_plots.append(f"plot({var_ref}, \"{_pine_var_name(plot.ref)}\", {color})")
    else:
        # Auto-plot all standard indicators so lines show up on the chart
        for ind in dsl.indicators:
            info = INDICATOR_REGISTRY.get(ind.type)
            if not info or info.vt_concept:
                continue
            var_name = _pine_var_name(ind.id)
            period = ind.params.get("period", 0)
            color = _auto_color(0, ind.type, period)
            if info.category in ("momentum",) and ind.type not in ("macd",):
                pane_plots.append(f"plot({var_name}, \"{var_name}\", {color})")
            else:
                overlay_plots.append(f"plot({var_name}, \"{var_name}\", {color})")

    if overlay_plots:
        lines.append("// Overlay plots (on price chart)")
        for p in overlay_plots:
            lines.append(p)

    if pane_plots:
        lines.append("")
        lines.append("// Separate-pane plots")
        for p in pane_plots:
            lines.append(p)

    # ── Signals ──
    if dsl.signals:
        lines.append("")
        lines.append("// === SIGNALS ===")
        for sig_name, sig_def in dsl.signals.items():
            try:
                ast = parse_condition(sig_def.condition)
                # Replace identifiers with Pine variable names
                pine_cond = to_pine_condition(ast)
                cond_var = f"{_pine_var_name(sig_name)}_cond"
                lines.append(f"{cond_var} = {pine_cond}")
            except Exception as e:
                lines.append(f"// ERROR parsing '{sig_name}': {e}")
                lines.append(f"{_pine_var_name(sig_name)}_cond = false")

        # Plot entry/exit markers
        if "entry" in dsl.signals:
            lines.append("")
            lines.append(
                'plotshape(entry_cond, style=shape.triangleup, '
                'location=location.belowbar, color=color.green, size=size.small, '
                'title="Entry")'
            )
        if "exit" in dsl.signals:
            lines.append(
                'plotshape(exit_cond, style=shape.triangledown, '
                'location=location.abovebar, color=color.red, size=size.small, '
                'title="Exit")'
            )

    lines.append("")
    return "\n".join(lines)


# ── Internal renderers ──────────────────────────────────────────────────────

def _add_header(lines: List[str], dsl: IndicatorDSL) -> None:
    """Add the Pine Script header."""
    lines.append("//@version=5")
    short_name = dsl.name[:12] if len(dsl.name) > 12 else dsl.name
    # Default overlay=false; we'll set it based on what's plotted
    overlay = _is_overlay_indicator(dsl)
    lines.append(
        f'indicator(title="{dsl.name}", shorttitle="{short_name}", '
        f'overlay={str(overlay).lower()})'
    )
    lines.append("")


def _is_overlay_indicator(dsl: IndicatorDSL) -> bool:
    """Determine if this indicator should be an overlay (on price chart)
    or a separate pane. If there are only overlay-type indicators, return True.
    If there are pane-type oscillators, return False."""
    oscillator_types = {"rsi", "stochastic", "cci"}
    for ind in dsl.indicators:
        info = INDICATOR_REGISTRY.get(ind.type)
        if info and info.type_name in oscillator_types:
            return False
    return True


def _render_indicator(ind: IndicatorDef, var_name: str) -> str:
    """Render a single indicator computation as a Pine Script line."""
    info = INDICATOR_REGISTRY.get(ind.type)
    if not info:
        return f"// Unknown indicator type: {ind.type}"

    if ind.type == "bb":
        # Bollinger Bands are special — 3 output lines
        src = ind.params.get("source", "close")
        period = ind.params.get("period", 20)
        stddev = ind.params.get("stddev", 2.0)
        base = _pine_var_name(f"{ind.id}_middle")
        upper = _pine_var_name(f"{ind.id}_upper")
        lower = _pine_var_name(f"{ind.id}_lower")
        return (
            f"{base} = ta.sma({src}, {period})\n"
            f"dev = {stddev} * ta.stdev({src}, {period})\n"
            f"{upper} = {base} + dev\n"
            f"{lower} = {base} - dev"
        )
    elif ind.type == "stochastic":
        k_period = ind.params.get("k_period", 14)
        d_period = ind.params.get("d_period", 3)
        k_var = _pine_var_name(f"{ind.id}_k")
        d_var = _pine_var_name(f"{ind.id}_d")
        return (
            f"{k_var} = ta.stoch(close, high, low, {k_period})\n"
            f"{d_var} = ta.sma({k_var}, {d_period})"
        )
    elif ind.type == "macd":
        fast = ind.params.get("fast", 12)
        slow = ind.params.get("slow", 26)
        signal = ind.params.get("signal", 9)
        src = ind.params.get("source", "close")
        macd_var = _pine_var_name(f"{ind.id}_line")
        sig_var = _pine_var_name(f"{ind.id}_signal")
        hist_var = _pine_var_name(f"{ind.id}_hist")
        return (
            f"[{macd_var}, {sig_var}, {hist_var}] = ta.macd({src}, {fast}, {slow}, {signal})"
        )
    else:
        # Standard single-output indicator
        snippet = info.pine_snippet
        src = ind.params.get("source", info.default_source)
        period = ind.params.get("period", None)
        rendered = snippet.format(
            source=src,
            period=period,
            stddev=ind.params.get("stddev", 2.0),
        )
        return f"{var_name} = {rendered}"


def _render_compound(comp: CompoundIndicator, ind_vars: Dict[str, str],
                     dsl: IndicatorDSL) -> List[str]:
    """Render a VT compound indicator computation."""
    lines: List[str] = []
    var_name = _pine_var_name(comp.id)

    if comp.type == "ema_alignment":
        ema_ids = comp.params.get("emas", [])
        if len(ema_ids) < 2:
            return [f"// ema_alignment requires at least 2 EMAs, got {len(ema_ids)}"]
        ema_vars = [_resolve_indicator_ref(eid, dsl) for eid in ema_ids]
        # Build pairwise comparison chain
        pairs = " and ".join(
            f"{ema_vars[i]} > {ema_vars[i+1]}"
            for i in range(len(ema_vars) - 1)
        )
        bear_pairs = " and ".join(
            f"{ema_vars[i]} < {ema_vars[i+1]}"
            for i in range(len(ema_vars) - 1)
        )
        lines.append(f"// {comp.id}: EMA alignment ({', '.join(ema_ids)})")
        lines.append(
            f"{var_name} = {pairs} ? 1 : ({bear_pairs} ? -1 : 0)"
        )

    elif comp.type == "ema_spread":
        ema_ids = comp.params.get("emas", [])
        if len(ema_ids) < 2:
            return [f"// ema_spread requires at least 2 EMAs, got {len(ema_ids)}"]
        ema_vars = [_resolve_indicator_ref(eid, dsl) for eid in ema_ids]
        max_expr = f"math.max({', '.join(ema_vars)})"
        min_expr = f"math.min({', '.join(ema_vars)})"
        lines.append(f"// {comp.id}: EMA spread ({', '.join(ema_ids)})")
        lines.append(f"{var_name} = ({max_expr} - {min_expr}) / close")

    elif comp.type == "candle_proximity":
        ema_id = comp.params.get("ema", "")
        ema_var = _resolve_indicator_ref(ema_id, dsl)
        lines.append(f"// {comp.id}: Candle proximity to {ema_id}")
        lines.append(f"{var_name} = (close - {ema_var}) / ta.atr(14)")

    elif comp.type == "pull_count":
        ema_id = comp.params.get("ema", "ema_5")
        ema_var = _resolve_indicator_ref(ema_id, dsl)
        lines.append(f"// {comp.id}: Green candle pull count from {ema_id}")
        # Stateful counter in Pine: count consecutive closes above EMA
        lines.append(f"var {var_name} = 0")
        lines.append(f"{var_name} := close > {ema_var} ? nz({var_name}[1]) + 1 : 0")

    else:
        lines.append(f"// Unknown compound type: {comp.type}")

    return lines


def _get_indicator_info_for_plot(plot: PlotDef, dsl: IndicatorDSL) -> IndicatorInfo | None:
    """Try to find the indicator info for a plot reference."""
    for ind in dsl.indicators:
        if ind.id == plot.ref:
            return INDICATOR_REGISTRY.get(ind.type)
    return None


def _auto_color(index: int, indicator_type: str = "", period: int = 0) -> str:
    """Assign a color from a rotating palette, with some type-based defaults."""
    type_colors = {
        "ema": "color.blue",
        "sma": "color.orange",
        "rsi": "color.purple",
        "atr": "color.teal",
        "bb": "color.navy",
        "macd": "color.green",
        "stochastic": "color.fuchsia",
        "volume": "color.lime",
        "vwap": "color.maroon",
        "cci": "color.orange",
    }

    # If the indicator has a period, spread colors across the palette
    # so that sma_5, sma_10, sma_20, rsi_14, rsi_7 all get distinct hues
    if period:
        palette = [
            "color.blue", "color.orange", "color.green", "color.red",
            "color.purple", "color.teal", "color.maroon", "color.navy",
            "color.fuchsia", "color.lime",
        ]
        # Known EMA periods get stable, semantic colors
        if indicator_type == "ema":
            ema_known = {5: 0, 8: 1, 13: 2, 20: 3, 21: 3, 50: 4, 200: 7}
            idx = ema_known.get(period, period % len(palette))
        else:
            # Spread periods across palette using golden ratio to avoid
            # collisions (10 and 20 don't both land on the same color)
            idx = int((period * 0.618) % 1.0 * len(palette)) % len(palette)
        return palette[idx]

    if indicator_type in type_colors:
        return type_colors[indicator_type]
    colors = [
        "color.blue", "color.red", "color.green", "color.orange",
        "color.purple", "color.teal", "color.maroon", "color.navy",
        "color.fuchsia", "color.lime",
    ]
    return colors[index % len(colors)]
