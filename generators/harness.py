"""
Comparison Harness — the honest way to decide if indicators matter.

For each strategy (DSL) x instrument x window, we compute:

  1. Full backtest metrics (reuses generators.backtest.run_backtest)
  2. Regime label (trending / volatile / ranging) — same heuristics as the advisor
  3. Buy-and-hold baseline  — "did the strategy beat just holding the asset?"
  4. Random-entry baseline  — "did the strategy's entries beat random entries
     held for the same average duration?"  This is the null hypothesis.
     A z-score >= ~1.5 vs random noise is the minimum evidence of real edge.

The edge columns are the answer to "do these indicators make a difference?"
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from dsl.schema import IndicatorDSL
from generators.backtest import run_backtest
from tradingview.data_fetcher import fetch_ohlcv
from generators.local import compute_indicators


# ────────────────────────────────────────────────────────────────────────────
# Regime labeling (mirrors the advisor's heuristics so labels are consistent)
# ────────────────────────────────────────────────────────────────────────────

def label_regime(df: pd.DataFrame) -> str:
    """Label a window as trending / volatile / ranging.

    Trending: |mean change| / std of changes is high (directional persistence).
    Volatile: ATR% is high (wide bars relative to price).
    Ranging:  neither — low trend, low vol.
    """
    c = df["close"]
    h = df["high"]
    l = df["low"]
    diffs = c.diff().dropna()
    trend_strength = abs(diffs.mean()) / diffs.std() if diffs.std() > 0 else 0.0
    atr_pct = (h - l).mean() / c.mean()

    if trend_strength > 0.15:
        return "trending"
    if atr_pct > 0.02:
        return "volatile"
    return "ranging"


# ────────────────────────────────────────────────────────────────────────────
# Baselines
# ────────────────────────────────────────────────────────────────────────────

def buy_and_hold_return(df: pd.DataFrame) -> float:
    """Return % of holding the asset for the whole window (close-to-close)."""
    if len(df) < 2:
        return 0.0
    return float((df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100)


def random_entries_returns(
    df: pd.DataFrame,
    n_entries: int,
    hold_bars: int,
    iters: int = 60,
    seed: int = 42,
    cost_per_trade: float = 0.0,
) -> Dict[str, float]:
    """Simulate n_entries random entries, each held for hold_bars.

    Returns the distribution of TOTAL return % across `iters` shuffles — the
    SUM of the n_entries per-trade returns, so it is directly comparable to the
    strategy's `total_return_pct` (also a sum across its trades). This is the
    null hypothesis: if a strategy's return is not above the upper tail of this
    distribution, its entries carry no measurable edge.

    NOTE (Sep 2026 fix): this used to divide by n_entries, producing a MEAN
    per-trade return on the random side while the strategy side is a SUM —
    which inflated every z-score by roughly the trade count (36 trades →
    z≈80 where the honest value is ≈2-4). Both sides are sums now.

    cost_per_trade: fraction charged per random entry (round trip), so the
    null hypothesis pays the same costs the strategy does.
    """
    closes = df["close"].to_numpy()
    n = len(closes)
    if n_entries <= 0 or hold_bars <= 0 or n < 2:
        return {"mean": 0.0, "std": 0.0, "p5": 0.0, "p95": 0.0, "iters": iters}

    rng = np.random.default_rng(seed)
    max_start = n - hold_bars - 1
    if max_start < 1:
        return {"mean": 0.0, "std": 0.0, "p5": 0.0, "p95": 0.0, "iters": iters}

    totals = np.empty(iters)
    for i in range(iters):
        starts = rng.integers(0, max_start, size=n_entries)
        rets = closes[starts + hold_bars] / closes[starts] - 1.0
        totals[i] = (rets - cost_per_trade).sum() * 100.0

    return {
        "mean": round(float(totals.mean()), 2),
        "std": round(float(totals.std()), 2),
        "p5": round(float(np.percentile(totals, 5)), 2),
        "p95": round(float(np.percentile(totals, 95)), 2),
        "iters": iters,
    }


def edge_verdict(
    strat_return: float,
    rand: Dict[str, float],
    n_trades: int,
) -> Dict[str, object]:
    """Classify whether the strategy's return shows edge vs random entries."""
    if n_trades < 10:
        return {
            "z_score": 0.0,
            "verdict": "insufficient",
            "label": "Too few trades",
            "tone": "dim",
        }
    if rand["std"] <= 0:
        return {
            "z_score": 0.0,
            "verdict": "unknown",
            "label": "No noise estimate",
            "tone": "dim",
        }
    z = (strat_return - rand["mean"]) / rand["std"]
    if z >= 1.5:
        verdict, label, tone = "strong", "Strong edge", "emerald"
    elif z >= 1.0:
        verdict, label, tone = "edge", "Edge", "emerald"
    elif z >= 0.5:
        verdict, label, tone = "weak", "Weak edge", "amber"
    else:
        verdict, label, tone = "none", "No edge", "rose"
    return {"z_score": round(float(z), 2), "verdict": verdict, "label": label, "tone": tone}


# ────────────────────────────────────────────────────────────────────────────
# Per-strategy comparison
# ────────────────────────────────────────────────────────────────────────────

def compare_strategy(
    dsl: IndicatorDSL,
    ticker: str,
    interval: str,
    period: str,
    random_iters: int = 60,
    cost_bps_per_side: float = 0.0,
) -> Dict:
    """Run one strategy on one instrument/window and return the full comparison.

    cost_bps_per_side: trading cost (fees + slippage) per side in basis points
    of notional. The row reports BOTH gross metrics (unchanged field names) and
    net-of-cost metrics (`*_net` fields, plus `z_score_net` / `verdict_net`).
    The random-entry null pays the same costs, so the net verdict is a fair
    comparison rather than a penalty applied only to the strategy.
    """
    row: Dict = {
        "strategy": dsl.name,
        "ticker": ticker,
        "interval": interval,
        "period": period,
        "error": None,
    }

    df = fetch_ohlcv(ticker, interval=interval, period=period)
    if df is None or df.empty or len(df) < 20:
        row["error"] = "Not enough data"
        return row

    try:
        result = compute_indicators(df, dsl)
    except Exception as e:
        row["error"] = f"Compute failed: {type(e).__name__}: {e}"
        return row

    row["bars"] = len(result)
    row["regime"] = label_regime(result)
    idx0, idxn = result.index[0], result.index[-1]
    row["date_range"] = f"{idx0.strftime('%Y-%m-%d')} → {idxn.strftime('%Y-%m-%d')}"
    row["buy_hold_pct"] = round(buy_and_hold_return(result), 2)

    bt = run_backtest(result)
    row["total_trades"] = bt.total_trades
    row["win_rate"] = bt.win_rate
    row["total_return_pct"] = round(bt.total_return_pct, 2)
    row["avg_return_pct"] = bt.avg_return_pct
    row["max_drawdown_pct"] = bt.max_drawdown_pct
    row["profit_factor"] = bt.profit_factor
    row["sharpe_ratio"] = bt.sharpe_ratio
    row["avg_bars_held"] = bt.avg_bars_held

    # Baselines
    row["edge_vs_buyhold_pct"] = round(bt.total_return_pct - row["buy_hold_pct"], 2)
    rand = random_entries_returns(
        result,
        n_entries=max(bt.total_trades, 1),
        hold_bars=max(int(bt.avg_bars_held), 1),
        iters=random_iters,
    )
    row["random_mean_pct"] = rand["mean"]
    row["random_std_pct"] = rand["std"]
    row["random_p5_pct"] = rand["p5"]
    row["random_p95_pct"] = rand["p95"]
    row["edge_vs_random_pct"] = round(bt.total_return_pct - rand["mean"], 2)

    ev = edge_verdict(bt.total_return_pct, rand, bt.total_trades)
    row["z_score"] = ev["z_score"]
    row["verdict"] = ev["verdict"]
    row["verdict_label"] = ev["label"]
    row["verdict_tone"] = ev["tone"]

    # ── Net-of-cost block ──────────────────────────────────────────────────
    # Same simulation with fees+slippage charged on both fills of every trade.
    # The random-entry null pays the identical round-trip cost, so the net
    # verdict measures edge AFTER costs, not just the strategy's cost burden.
    cost_frac = max(0.0, float(cost_bps_per_side)) / 10000.0
    row["cost_bps_per_side"] = round(float(cost_bps_per_side), 4)
    if cost_frac > 0:
        bt_net = run_backtest(result, cost_bps_per_side=cost_bps_per_side)
        rand_net = random_entries_returns(
            result,
            n_entries=max(bt.total_trades, 1),
            hold_bars=max(int(bt.avg_bars_held), 1),
            iters=random_iters,
            cost_per_trade=2.0 * cost_frac,  # round trip per entry
        )
    else:
        bt_net, rand_net = bt, rand
    row["total_return_pct_net"] = round(bt_net.total_return_pct, 2)
    row["avg_return_pct_net"] = round(bt_net.avg_return_pct, 2)
    row["win_rate_net"] = bt_net.win_rate
    row["max_drawdown_pct_net"] = round(bt_net.max_drawdown_pct, 2)
    row["profit_factor_net"] = round(bt_net.profit_factor, 2)
    row["sharpe_ratio_net"] = round(bt_net.sharpe_ratio, 2)
    row["edge_vs_buyhold_net_pct"] = round(bt_net.total_return_pct - row["buy_hold_pct"], 2)
    row["random_mean_net_pct"] = rand_net["mean"]
    row["random_std_net_pct"] = rand_net["std"]
    row["edge_vs_random_net_pct"] = round(bt_net.total_return_pct - rand_net["mean"], 2)
    # Cost per round trip in return-% terms, and the per-side cost level at
    # which the strategy's gross edge is exactly consumed (break-even).
    row["cost_drag_pct"] = round(bt.total_return_pct - bt_net.total_return_pct, 2)
    row["breakeven_bps_per_side"] = (
        round(bt.total_return_pct * 10000.0 / (2.0 * bt.total_trades * 100.0), 2)
        if bt.total_trades > 0 else None
    )
    ev_net = edge_verdict(bt_net.total_return_pct, rand_net, bt_net.total_trades)
    row["z_score_net"] = ev_net["z_score"]
    row["verdict_net"] = ev_net["verdict"]
    row["verdict_label_net"] = ev_net["label"]
    row["verdict_tone_net"] = ev_net["tone"]

    return row


# ────────────────────────────────────────────────────────────────────────────
# Matrix runner
# ────────────────────────────────────────────────────────────────────────────

def run_comparison(
    dsls: List[IndicatorDSL],
    tickers: List[str],
    interval: str,
    period: str,
    random_iters: int = 60,
    cost_bps_per_side: float = 0.0,
) -> Dict:
    """Run the full strategy x ticker matrix.

    cost_bps_per_side: fees+slippage per side (bps of notional) applied to both
    the strategy and the random-entry null, so every `*_net` field and the
    net verdicts reflect trading after costs. 0.0 (default) = gross-only.
    """
    rows = []
    for dsl in dsls:
        for ticker in tickers:
            rows.append(compare_strategy(dsl, ticker, interval, period, random_iters,
                                         cost_bps_per_side=cost_bps_per_side))

    summary = {
        "strategies": len(dsls),
        "tickers": len(tickers),
        "cells": len(rows),
        "cost_bps_per_side": round(float(cost_bps_per_side), 4),
        "edges": sum(1 for r in rows if r.get("verdict") in ("edge", "strong")),
        "weak_edges": sum(1 for r in rows if r.get("verdict") == "weak"),
        "no_edges": sum(1 for r in rows if r.get("verdict") == "none"),
        "insufficient": sum(1 for r in rows if r.get("verdict") == "insufficient"),
        "errors": sum(1 for r in rows if r.get("error")),
        "edges_net": sum(1 for r in rows if r.get("verdict_net") in ("edge", "strong")),
        "weak_edges_net": sum(1 for r in rows if r.get("verdict_net") == "weak"),
        "no_edges_net": sum(1 for r in rows if r.get("verdict_net") == "none"),
        "insufficient_net": sum(1 for r in rows if r.get("verdict_net") == "insufficient"),
        "profitable_net": sum(1 for r in rows if (r.get("total_return_pct_net") or 0) > 0),
    }
    return {"rows": rows, "summary": summary}
