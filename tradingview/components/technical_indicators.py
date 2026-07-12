from logicflow import check_rsi_crossing, check_stochastic_crossing, check_ma_crossing

technical_indicators = {
    "RSI": {
        "RSI > 70": lambda rsi: rsi > 70,
        "RSI < 30": lambda rsi: rsi < 30,
        "RSI crossing above Trend Line": lambda rsi, trend_line: check_rsi_crossing(rsi, trend_line),
        "RSI crossing below Trend Line": lambda rsi, trend_line: check_rsi_crossing(rsi, trend_line)
    },
    # Similar logic for Stochastic indicators
    "Stochastic": {
        "Stochastic crossing above signal line": lambda stochastic, signal_line: check_stochastic_crossing(stochastic, signal_line),
        "Stochastic crossing below signal line": lambda stochastic, signal_line: check_stochastic_crossing(stochastic, signal_line)
    },
    # Add more technical indicators here
    # MA
    "MA": {
        "MA > 70": lambda ma: ma > 70,
        "MA < 30": lambda ma: ma < 30,
        "MA crossing above Trend Line": lambda ma, trend_line: check_ma_crossing(ma, trend_line),
        "MA crossing below Trend Line": lambda ma, trend_line: check_ma_crossing(ma, trend_line)
    }
}
