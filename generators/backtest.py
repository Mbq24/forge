"""
Backtest Engine — simulate trades from signal columns, compute P&L and metrics.

Takes a DataFrame with signal_entry and signal_exit boolean columns and
simulates a simple long-only trading system.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import numpy as np


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    bars_held: int


@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return_pct: float
    avg_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    sharpe_ratio: float
    avg_bars_held: float
    trades: List[dict] = field(default_factory=list)
    equity_curve: List[dict] = field(default_factory=list)
    error: Optional[str] = None


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 10000.0,
) -> BacktestResult:
    """Run a simple long-only backtest using signal_entry and signal_exit columns.

    Args:
        df: DataFrame with columns 'signal_entry' and 'signal_exit' (boolean).
        initial_capital: Starting account balance.

    Returns:
        BacktestResult with trades, metrics, and equity curve.
    """
    if "signal_entry" not in df.columns or "signal_exit" not in df.columns:
        return BacktestResult(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, total_return_pct=0, avg_return_pct=0,
            max_drawdown_pct=0, profit_factor=0, sharpe_ratio=0,
            avg_bars_held=0, error="Missing signal_entry or signal_exit columns",
        )

    entry = df["signal_entry"].fillna(0).astype(bool)
    exit_sig = df["signal_exit"].fillna(0).astype(bool)
    close = df["close"]
    dates = [str(d) for d in df.index]

    trades: List[Trade] = []
    in_position = False
    entry_idx = -1
    entry_price = 0.0

    # Equity curve (daily portfolio value)
    equity = [initial_capital]
    peak_equity = initial_capital
    max_drawdown = 0.0

    for i in range(len(df)):
        current_equity = equity[-1]

        if in_position:
            # Track floating equity
            current_price = float(close.iloc[i])
            floating_return = (current_price - entry_price) / entry_price
            floating_equity = initial_capital + (initial_capital * floating_return)
            current_equity = floating_equity

            # Check exit signal
            if exit_sig.iloc[i]:
                exit_price_val = float(close.iloc[i])
                trade_return = (exit_price_val - entry_price) / entry_price
                trades.append(Trade(
                    entry_date=dates[entry_idx],
                    exit_date=dates[i],
                    entry_price=round(float(entry_price), 2),
                    exit_price=round(exit_price_val, 2),
                    return_pct=round(trade_return * 100, 2),
                    bars_held=i - entry_idx,
                ))
                # Update equity on exit
                current_equity = initial_capital + (initial_capital * trade_return)
                in_position = False
        else:
            # Check entry signal
            if entry.iloc[i]:
                entry_price = float(close.iloc[i])
                entry_idx = i
                in_position = True

        equity.append(current_equity)
        peak_equity = max(peak_equity, current_equity)
        dd = (peak_equity - current_equity) / peak_equity * 100
        max_drawdown = max(max_drawdown, dd)

    # Close any open position at the end
    if in_position:
        exit_price_val = float(close.iloc[-1])
        trade_return = (exit_price_val - entry_price) / entry_price
        trades.append(Trade(
            entry_date=dates[entry_idx],
            exit_date=dates[-1],
            entry_price=round(float(entry_price), 2),
            exit_price=round(exit_price_val, 2),
            return_pct=round(trade_return * 100, 2),
            bars_held=len(df) - entry_idx,
        ))
        equity[-1] = initial_capital + (initial_capital * trade_return)

    # Calculate metrics
    total_trades = len(trades)
    if total_trades == 0:
        return BacktestResult(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, total_return_pct=0, avg_return_pct=0,
            max_drawdown_pct=round(max_drawdown, 2),
            profit_factor=0, sharpe_ratio=0,
            avg_bars_held=0, trades=[],
            equity_curve=[{"date": dates[i], "equity": round(float(equity[i+1]), 2)} for i in range(len(dates))],
            error="No trades generated — check your entry/exit conditions",
        )

    winning = [t for t in trades if t.return_pct > 0]
    losing = [t for t in trades if t.return_pct <= 0]

    win_rate = len(winning) / total_trades * 100 if total_trades > 0 else 0
    total_return = sum(t.return_pct for t in trades)
    avg_return = total_return / total_trades if total_trades > 0 else 0
    avg_bars = sum(t.bars_held for t in trades) / total_trades if total_trades > 0 else 0

    gross_profit = sum(t.return_pct for t in winning)
    gross_loss = abs(sum(t.return_pct for t in losing))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)

    # Simplified Sharpe: avg return / std of returns, annualized
    returns_arr = np.array([t.return_pct for t in trades])
    sharpe = float(np.mean(returns_arr) / np.std(returns_arr) * np.sqrt(252)) if np.std(returns_arr) > 0 and len(returns_arr) > 1 else 0

    # Build equity curve
    equity_curve = [{"date": dates[i], "equity": round(float(equity[i+1]), 2)} for i in range(len(dates))]

    return BacktestResult(
        total_trades=total_trades,
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(win_rate, 1),
        total_return_pct=round(total_return, 2),
        avg_return_pct=round(avg_return, 2),
        max_drawdown_pct=round(max_drawdown, 2),
        profit_factor=round(profit_factor, 2),
        sharpe_ratio=round(sharpe, 2),
        avg_bars_held=round(avg_bars, 1),
        trades=[{
            "entry_date": t.entry_date,
            "exit_date": t.exit_date,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "return_pct": t.return_pct,
            "bars_held": t.bars_held,
        } for t in trades],
        equity_curve=equity_curve,
    )
