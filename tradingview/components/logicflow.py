from operators import operators

previous_rsi = None
previous_trend_line = None

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

def check_rsi_crossing(current_rsi, trend_line):
    global previous_rsi, previous_trend_line
    
    # Check for an upward crossover
    if previous_rsi is not None and previous_trend_line is not None:
        if previous_rsi < previous_trend_line and current_rsi > trend_line:
            return "RSI crossed above Trend Line"
        # Check for a downward crossover
        elif previous_rsi > previous_trend_line and current_rsi < trend_line:
            return "RSI crossed below Trend Line"
    
    # Update previous values
    previous_rsi = current_rsi
    previous_trend_line = trend_line
    
    return "No crossover"


def check_stochastic_crossing(current_stochastic, signal_line):
    global previous_stochastic, previous_signal_line
    
    # Check for an upward crossover
    if previous_stochastic is not None and previous_signal_line is not None:
        if previous_stochastic < previous_signal_line and current_stochastic > signal_line:
            return "Stochastic crossed above Signal Line"
        # Check for a downward crossover
        elif previous_stochastic > previous_signal_line and current_stochastic < signal_line:
            return "Stochastic crossed below Signal Line"
    
    # Update previous values
    previous_stochastic = current_stochastic
    previous_signal_line = signal_line
    
    return "No crossover"

def check_ma_crossing(current_ma, trend_line):
    global previous_ma, previous_trend_line
    
    # Check for an upward crossover
    if previous_ma is not None and previous_trend_line is not None:
        if previous_ma < previous_trend_line and current_ma > trend_line:
            return "MA crossed above Trend Line"
        # Check for a downward crossover
        elif previous_ma > previous_trend_line and current_ma < trend_line:
            return "MA crossed below Trend Line"
    
    # Update previous values
    previous_ma = current_ma
    previous_trend_line = trend_line
    
    return "No crossover"



import random

indicators = ['RSI', 'Stochastic', 'MA']
conditions = ['>', '<', '==', '>=', '<=', '!=']
logical_ops = ['and', 'or']

#test random choices

def test_random_choices_using_dictionaries_above():
    for _ in range(10):
        indicator = random.choice(indicators)
        condition = random.choice(list(technical_indicators[indicator].keys()))
        print(f"{indicator} {condition}")


def random_condition():
    ind1 = random.choice(indicators)
    ind2 = random.choice(indicators)
    cond = random.choice(conditions)
    return f"({ind1} {cond} {ind2})"

def generate_random_strategy():
    condition1 = random_condition()
    condition2 = random_condition()
    logical_op = random.choice(logical_ops)
    return f"{condition1} {logical_op} {condition2}"

for _ in range(10):
    strategy = generate_random_strategy()
    while strategy.count("RSI") > 1 or strategy.count("Stochastic") > 1 or strategy.count("Price") > 1 or strategy.count("MA50") > 1 or strategy.count("MA200") > 1:
        strategy = generate_random_strategy()
    print(strategy)

test_random_choices_using_dictionaries_above()