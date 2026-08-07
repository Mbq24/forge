import datetime
import json
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from flask import Flask, render_template, request, g, jsonify
import random
import sys
import os
from pathlib import Path

# Add project root to path for DSL imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import yaml
import plotly.graph_objects as go
from dsl.schema import IndicatorDSL, SignalDef
from dsl.indicators import INDICATOR_REGISTRY, PATTERN_MAP
from generators.pinescript import generate_pinescript
from generators.local import compute_indicators
from generators.backtest import run_backtest
from generators.harness import run_comparison
from data_fetcher import fetch_ohlcv, list_tickers, format_data_preview

load_dotenv()

app = Flask(__name__)

# Serve production React SPA from web/dist/
_web_dist = _project_root / "web" / "dist"
if not _web_dist.exists():
    _web_dist = _project_root / "tradingview" / "web_dist"  # Docker fallback
if _web_dist.exists():
    app.static_folder = str(_web_dist)
    app.static_url_path = ""

    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        return app.send_static_file(f"assets/{filename}")

    # React SPA routes (must be before API routes)
    @app.route("/dsl/new")
    @app.route("/advisor")
    def serve_spa_pages():
        return app.send_static_file("index.html")

print(f"📦 React SPA: {'will serve from web/dist' if _web_dist.exists() else 'not found'}")

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('trade.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.route('/')
def dashboard():
    # Serve React SPA if built
    if _web_dist.exists():
        return app.send_static_file("index.html")
    db = get_db()

    cursor = db.cursor()
    cursor.execute("SELECT * FROM rsi")
    rsi = cursor.fetchall()

    cursor.execute("SELECT * FROM stochastic")
    stochastic = cursor.fetchall()

    cursor.execute("SELECT * FROM signals")
    signals = cursor.fetchall()

    cursor.execute("SELECT * FROM lines")
    lines = cursor.fetchall()
    
    return render_template('dashboard.html', signals=signals, rsi=rsi, stochastic=stochastic, lines=lines)

# @app.route('/post', methods=['GET'])
def dash_graph(conn, data):
    print("CALLING DASH GRAPH")

    # read indicator data from the database
    df_rsi = pd.read_sql_query("SELECT * FROM rsi", conn)
    df_stochastic = pd.read_sql_query("SELECT * FROM stochastic", conn)
    
    # check if df_rsi has data in it
    if not df_rsi.empty:
        print("df_rsi has data")
        print(df_rsi)
    else:
        print("df_rsi is empty")

    # check if df_stochastic has data in it
    if not df_stochastic.empty:
        print("df_stochastic has data")
        print(df_stochastic)
    else:
        print("df_stochastic is empty")

    if not df_rsi.empty and not df_stochastic.empty:
        df_merged = pd.concat([df_rsi, df_stochastic], axis=1)
    else:
        df_merged = pd.DataFrame()

    print("MERGED DATAFRAME:")
    print(df_merged.tail(15))

    df_merged['frequency'] = 0
    df_merged['direction'] = 0
    df_merged['strength'] = 0
    df_merged['rsi'] = 0
    df_merged['stochastic'] = 0
    df_merged['direction'] = 0
    df_merged['hemisphere'] = 0

    if not df_merged.empty:
        df_merged = df_merged.dropna(subset=['rsi', 'stochastic'])

    df_merged['rsi'] = df_merged['rsi'].replace('null', np.nan).astype(float).round(1)
    df_merged['stochastic'] = df_merged['stochastic'].astype(float).round(1)
    df_merged['direction'] = df_merged['direction'].astype(float).round(1)

    df_merged['hemisphere'] = np.where(df_merged['rsi'] > 50.0, 'Right', 'Left')
    
    print("LENGTH OF DATAFRAME: ", len(df_merged))  
    for index, row in df_merged.iterrows():
        
        strength_values = ['6+', '5-6', '4-5', '3-4', '2-3', '1-2', '0-1']
        df_merged.at[index, 'strength'] = random.choice(strength_values)
        # if 70.0 < row['rsi'] <= 100.0:
        #     df_merged.at[index, 'strength'] = '6+'
        # elif 60.0 < row['rsi'] <= 70.0:
        #     df_merged.at[index, 'strength'] = '5-6'
        # elif 50.0 < row['rsi'] <= 60.0:
        #     df_merged.at[index, 'strength'] = '4-5'
        # elif 40.0 < row['rsi'] <= 50.0:
        #     df_merged.at[index, 'strength'] = '3-4'
        # elif 30.0 < row['rsi'] <= 40.0:
        #     df_merged.at[index, 'strength'] = '2-3'
        # elif 20.0 < row['rsi'] <= 30.0:
        #     df_merged.at[index, 'strength'] = '1-2'
        # else:
        #     df_merged.at[index, 'strength'] = '0-1'
        
        # rsi greater than 50 is right hemisphere
        # if row['hemisphere'] == 'Right':

        # how to extract the numerical value of a string

        # need to create a direction function that fixes the the compass directions
        # for example, North should be equal to 90 degrees from East. e.g. 90 degrees = Value of N +/- X
        # where X is the value of the angle from the East direction to the North direction
        # e.g. 90 degrees = 90 +/- 0 degrees
        # e.g. 90 degrees = 90 +/- 0 degrees

        # if row['hemisphere'] == 'Right':
        
        # direction_value = ord('N')  # Replace 'N' with the actual character you want to get the numerical value of
        # print("DIRECTION VALUE: ", direction_value - 90)
        # if row['hemisphere'] == 'Right':

          # how to give theta a value of 90 degrees from East that maps to its corresponding compass direction
        # e.g. 90 degrees = N, 180 degrees = E, 270 degrees = S, 360 degrees = W
        
        if row['stochastic'] > 95.0:
            df_merged.at[index, 'direction'] = 90.0
        elif 90.0 < row['stochastic'] <= 95.0:
            df_merged.at[index, 'direction'] = 67.5
        elif 75.0 < row['stochastic'] <= 90.0:
            df_merged.at[index, 'direction'] = 45.0
        elif 67.5 < row['stochastic'] <= 75.0:
            df_merged.at[index, 'direction'] = 22.5
        elif 50.0 < row['stochastic'] <= 67.5:
            df_merged.at[index, 'direction'] = 0.0
        elif 37.5 < row['stochastic'] <= 50.0:
            df_merged.at[index, 'direction'] = -22.5
        elif 25.0 < row['stochastic'] <= 37.5:
            df_merged.at[index, 'direction'] = -45.0
        elif 10.0 < row['stochastic'] <= 25.0:
            df_merged.at[index, 'direction'] = -67.5
        else:
            df_merged.at[index, 'direction'] = -90.0
    
        # if row['hemisphere'] == 'Right':
        # randomly assign frequncy values to the dataframe
        df_merged.at[index, 'frequency'] = random.choice([0, 0.5, 1.0, 1.5, 2.0])

        # if 90.0 < row['stochastic'] <= 95.0:
        #     df_merged.at[index, 'frequency'] = 2.0
        # elif 75.0 < row['stochastic'] <= 90.0:
        #     df_merged.at[index, 'frequency'] = 1.5
        # elif 67.5 < row['stochastic'] <= 75.0:
        #     df_merged.at[index, 'frequency'] = 1.0
        # elif 50.0 < row['stochastic'] <= 67.5:
        #     df_merged.at[index, 'frequency'] = 0.5
        # elif 37.5 < row['stochastic'] <= 50.0:
        #     df_merged.at[index, 'frequency'] = 0.0
        # elif 25.0 < row['stochastic'] <= 37.5:
        #     df_merged.at[index, 'frequency'] = 1.0
        # elif 10.0 < row['stochastic'] <= 25.0:
        #     df_merged.at[index, 'frequency'] = 1.5
        # else:
        #     df_merged.at[index, 'frequency'] = 2.0

    print("CONDITIONED DATAFRAME:")
    print(df_merged.tail(25))
    return df_merged

@app.route('/webhook', methods=['POST'])
def webhook():
    PRICE = 'signals'
    LINES = 'lines'
    RSI = 'rsi'
    STOCHASTIC = 'stochastic'


    if request.json['type'] != PRICE:
        data = json.dumps(request.json)
        if data:
            conn = sqlite3.connect('trade.db')
            # dash_graph(conn, data)
        
    if request.json['type'] == LINES:
        data_dict = request.json
        data = json.dumps(data_dict)
        print(data)
        if data:
            # r.publish('tradingview', data)
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO {} (ticker, condition) VALUES (?, ?)".format(LINES),
                           (data_dict['ticker'], data_dict['condition']))
            db.commit()
            print(db)
    if request.json['type'] == RSI:
        data_dict = request.json
        
        data = json.dumps(data_dict)
        print(data)
        if data:
            # r.publish('tradingview', data)
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO {} (ticker, rsi) VALUES (?, ?)".format(RSI),
                           (data_dict['ticker'], data_dict['rsi']))
            db.commit()

    if request.json['type'] == STOCHASTIC:
        data_dict = request.json
        data = json.dumps(data_dict)
        print(data)
        if data:
            # r.publish('tradingview', data)
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO {} (ticker, stochastic) VALUES (?, ?)".format(STOCHASTIC),
                           (data_dict['ticker'], data_dict['stochastic']))
            db.commit()

    if request.json['type'] == PRICE:
        data_dict = request.json
        data_dict['open'] = data_dict['bar']['open']
        data_dict['high'] = data_dict['bar']['high']
        data_dict['low'] = data_dict['bar']['low']
        data_dict['close'] = data_dict['bar']['close']
        data_dict['volume'] = data_dict['bar']['volume']
        data = json.dumps(data_dict)
        if data:
            # r.publish('tradingview', data)
            db = get_db()
            cursor = db.cursor()
            cursor.execute(f"""
                INSERT INTO {PRICE} (ticker, order_action, order_contracts, order_price,
                        open, high, low, close, volume)          
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                
            """, (data_dict['ticker'], data_dict['strategy']['order_action'],
                  data_dict['strategy']['order_contracts'], data_dict['strategy']['order_price'],
                  data_dict['open'], data_dict['high'], data_dict['low'],
                  data_dict['close'], data_dict['volume']))
            db.commit()

        print(data)
        return data

    return {"code": "success"}


# ════════════════════════════════════════════════════════════════════════════
# INDICATOR DSL ROUTES
# ════════════════════════════════════════════════════════════════════════════

DSL_EXAMPLES_DIR = _project_root / "examples"


@app.route('/dsl')
def dsl_list():
    """List all available DSL definitions."""
    dsls = []
    if DSL_EXAMPLES_DIR.exists():
        for f in sorted(DSL_EXAMPLES_DIR.glob("*.yaml")):
            try:
                d = IndicatorDSL.from_yaml_file(str(f))
                dsls.append({
                    "name": d.name,
                    "description": d.description or "No description",
                    "timeframe": d.timeframe,
                    "indicators": d.indicators,
                    "compounds": d.compounds,
                    "patterns": d.patterns,
                    "signals": {k: {"condition": v.condition} for k, v in d.signals.items()},
                })
            except Exception as e:
                dsls.append({
                    "name": f.stem,
                    "description": f"Error: {e}",
                    "timeframe": "-",
                    "indicators": [],
                    "compounds": [],
                    "patterns": [],
                    "signals": {},
                })
    return render_template("dsl_list.html", dsls=dsls)


@app.route('/dsl/<name>')
def dsl_detail(name):
    """Show DSL detail with data, chart, and Pine Script."""
    # Find the DSL file
    dsl_file = DSL_EXAMPLES_DIR / f"{name}.yaml"
    if not dsl_file.exists():
        # Try matching by stem (in case name has .yaml)
        for f in DSL_EXAMPLES_DIR.glob("*.yaml"):
            d = IndicatorDSL.from_yaml_file(str(f))
            if d.name == name:
                dsl_file = f
                break
        else:
            return render_template("dsl_detail.html", error=f"DSL '{name}' not found",
                                   dsl_name=name, dsls=[]), 404

    try:
        dsl = IndicatorDSL.from_yaml_file(str(dsl_file))
    except Exception as e:
        return render_template("dsl_detail.html", error=f"Failed to parse DSL: {e}",
                               dsl_name=name, dsls=[]), 400

    # Get query params
    ticker = request.args.get("ticker", "BTC-USD")
    interval = request.args.get("interval", "1h")
    period = request.args.get("period", "7d")
    source = request.args.get("source", "yfinance")

    context = {
        "dsl_name": dsl.name,
        "indicators": dsl.indicators,
        "compounds": dsl.compounds,
        "timeframe": dsl.timeframe,
        "tickers": {"crypto": list_tickers("crypto"), "forex": list_tickers("forex"),
                     "stocks": list_tickers("stocks"), "commodities": list_tickers("commodities")},
        "ticker": ticker,
        "interval": interval,
        "period": period,
        "source": source,
        "yaml_content": dsl_file.read_text(),
        "chart_html": None,
        "pine_code": None,
        "error": None,
        "stats": {"entry_count": 0, "exit_count": 0, "total_bars": 0, "signal_density": 0},
        "entry_cond": "",
        "exit_cond": "",
        "date_range": "",
    }

    # Generate Pine Script
    try:
        context["pine_code"] = generate_pinescript(dsl)
    except Exception as e:
        context["pine_code"] = f"// Pine generation error: {e}"

    # Entry/exit conditions for display
    context["entry_cond"] = dsl.signals.get("entry", SignalDef("")).condition if dsl.signals.get("entry") else ""
    context["exit_cond"] = dsl.signals.get("exit", SignalDef("")).condition if dsl.signals.get("exit") else ""

    # Fetch data and compute
    try:
        if source == "yfinance":
            df = fetch_ohlcv(ticker, interval=interval, period=period)
        else:
            # Try loading from SQLite
            db = get_db()
            df = pd.read_sql_query(
                "SELECT timestamp, open, high, low, close, volume FROM signals ORDER BY timestamp",
                db
            )
            if df.empty:
                raise ValueError("No data in database")
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)

        result = compute_indicators(df, dsl)

        context["date_range"] = f"{result.index[0].strftime('%Y-%m-%d')} → {result.index[-1].strftime('%Y-%m-%d')} ({len(result)} bars)"
        context["stats"]["total_bars"] = len(result)

        # Count signals
        if "signal_entry" in result.columns:
            context["stats"]["entry_count"] = int(result["signal_entry"].sum())
        if "signal_exit" in result.columns:
            context["stats"]["exit_count"] = int(result["signal_exit"].sum())

        total = context["stats"]["entry_count"] + context["stats"]["exit_count"]
        context["stats"]["signal_density"] = round(total / len(result) * 100, 1) if len(result) > 0 else 0

        # Build Plotly chart
        fig = go.Figure()

        # Price trace
        fig.add_trace(go.Scatter(
            x=result.index, y=result["close"],
            mode="lines", name="Close",
            line=dict(color="#94a3b8", width=1.2),
        ))

        # Indicator traces
        indicator_colors = ["#2962FF", "#00C853", "#FF6D00", "#D50000", "#7C4DFF"]
        color_idx = 0
        for ind in dsl.indicators:
            if ind.id in result.columns:
                fig.add_trace(go.Scatter(
                    x=result.index, y=result[ind.id],
                    mode="lines", name=ind.id,
                    line=dict(color=indicator_colors[color_idx % len(indicator_colors)], width=1),
                ))
                color_idx += 1

        # Entry signals (green triangles below)
        if "signal_entry" in result.columns:
            entry_idx = result["signal_entry"] > 0
            fig.add_trace(go.Scatter(
                x=result.index[entry_idx], y=result["close"][entry_idx],
                mode="markers", name="Entry",
                marker=dict(color="#34d399", size=8, symbol="triangle-up"),
            ))

        # Exit signals (red triangles above)
        if "signal_exit" in result.columns:
            exit_idx = result["signal_exit"] > 0
            fig.add_trace(go.Scatter(
                x=result.index[exit_idx], y=result["close"][exit_idx],
                mode="markers", name="Exit",
                marker=dict(color="#fb7185", size=8, symbol="triangle-down"),
            ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            margin=dict(t=10, r=10, b=30, l=40),
            font=dict(color="#94a3b8", size=10),
            xaxis=dict(gridcolor="#1e293b", showgrid=True),
            yaxis=dict(gridcolor="#1e293b", showgrid=True),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, font=dict(size=9)),
            dragmode="pan",
        )

        context["chart_html"] = fig.to_html(full_html=False, config={"responsive": True, "displayModeBar": False})

    except Exception as e:
        context["error"] = f"Data error: {e}"

    return render_template("dsl_detail.html", **context)


# ════════════════════════════════════════════════════════════════════════════
# JSON API (for React frontend)
# ════════════════════════════════════════════════════════════════════════════

@app.route('/api/dsl')
def api_dsl_list():
    """JSON list of all available DSL definitions."""
    dsls = []
    if DSL_EXAMPLES_DIR.exists():
        for f in sorted(DSL_EXAMPLES_DIR.glob("*.yaml")):
            try:
                d = IndicatorDSL.from_yaml_file(str(f))
                dsls.append({
                    "name": d.name,
                    "description": d.description or "No description",
                    "timeframe": d.timeframe,
                    "indicators": [{"id": i.id, "type": i.type, "params": i.params} for i in d.indicators],
                    "compounds": [{"id": c.id, "type": c.type, "params": c.params} for c in d.compounds],
                    "patterns": d.patterns,
                    "signals": {k: {"condition": v.condition} for k, v in d.signals.items()},
                })
            except Exception as e:
                dsls.append({"name": f.stem, "description": f"Parse error: {e}", "indicators": [], "compounds": [], "patterns": [], "signals": {}})
    return jsonify(dsls)


@app.route('/api/dsl/<name>')
def api_dsl_detail(name):
    """JSON detail for a DSL with computed chart data."""
    # Find DSL file
    dsl_file = DSL_EXAMPLES_DIR / f"{name}.yaml"
    if not dsl_file.exists():
        for f in DSL_EXAMPLES_DIR.glob("*.yaml"):
            try:
                d = IndicatorDSL.from_yaml_file(str(f))
                if d.name == name:
                    dsl_file = f
                    break
            except Exception:
                continue
        else:
            return jsonify({"error": f"DSL '{name}' not found"}), 404

    try:
        dsl = IndicatorDSL.from_yaml_file(str(dsl_file))
    except Exception as e:
        return jsonify({"error": f"Failed to parse DSL: {e}"}), 400

    # If mode=edit, return just the definition without computing
    if request.args.get("mode") == "edit":
        return jsonify({
            "name": dsl.name,
            "description": dsl.description,
            "timeframe": dsl.timeframe,
            "indicators": [{"id": i.id, "type": i.type, "params": i.params} for i in dsl.indicators],
            "compounds": [{"id": c.id, "type": c.type, "params": c.params} for c in dsl.compounds],
            "patterns": dsl.patterns,
            "signals": {k: v.condition for k, v in dsl.signals.items()},
            "yaml_content": dsl_file.read_text(),
        })

    ticker = request.args.get("ticker", "SYNTHETIC")
    interval = request.args.get("interval", "1h")
    period = request.args.get("period", "7d")

    result_data = {
        "dsl_name": dsl.name,
        "indicators": [{"id": i.id, "type": i.type, "params": i.params} for i in dsl.indicators],
        "compounds": [{"id": c.id, "type": c.type, "params": c.params} for c in dsl.compounds],
        "timeframe": dsl.timeframe,
        "ticker": ticker,
        "interval": interval,
        "period": period,
        "yaml_content": dsl_file.read_text(),
        "chart_data": None,
        "pine_code": None,
        "error": None,
        "stats": {"entry_count": 0, "exit_count": 0, "total_bars": 0, "signal_density": 0},
        "entry_cond": "",
        "exit_cond": "",
        "date_range": "",
    }

    # Pine Script
    try:
        result_data["pine_code"] = generate_pinescript(dsl)
    except Exception as e:
        result_data["pine_code"] = f"// Pine generation error: {e}"

    # Conditions
    result_data["entry_cond"] = dsl.signals.get("entry", SignalDef("")).condition if dsl.signals.get("entry") else ""
    result_data["exit_cond"] = dsl.signals.get("exit", SignalDef("")).condition if dsl.signals.get("exit") else ""

    # Fetch + compute
    try:
        df = fetch_ohlcv(ticker, interval=interval, period=period)
        result = compute_indicators(df, dsl)

        result_data["date_range"] = f"{result.index[0].strftime('%Y-%m-%d')} → {result.index[-1].strftime('%Y-%m-%d')} ({len(result)} bars)"
        result_data["stats"]["total_bars"] = len(result)

        if "signal_entry" in result.columns:
            result_data["stats"]["entry_count"] = int(result["signal_entry"].sum())
        if "signal_exit" in result.columns:
            result_data["stats"]["exit_count"] = int(result["signal_exit"].sum())
        total = result_data["stats"]["entry_count"] + result_data["stats"]["exit_count"]
        result_data["stats"]["signal_density"] = round(total / len(result) * 100, 1) if len(result) > 0 else 0

        # Build chart data as JSON for Plotly.js
        def _sanitize(v):
            """Replace NaN/Inf with None for valid JSON."""
            return None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else float(round(v, 2))

        def _sanitize_series(s):
            return [_sanitize(v) for v in s]

        dates_str = [str(d) for d in result.index]
        traces = [
            {"x": dates_str, "y": _sanitize_series(result["close"]), "type": "scatter", "mode": "lines", "name": "Close", "line": {"color": "#94a3b8", "width": 1.2}},
        ]

        indicator_colors = ["#2962FF", "#00C853", "#FF6D00", "#D50000", "#7C4DFF"]
        for idx, ind in enumerate(dsl.indicators):
            if ind.id in result.columns:
                traces.append({
                    "x": dates_str,
                    "y": _sanitize_series(result[ind.id]),
                    "type": "scatter", "mode": "lines", "name": ind.id,
                    "line": {"color": indicator_colors[idx % len(indicator_colors)], "width": 1},
                })

        if "signal_entry" in result.columns:
            entry_idx = result["signal_entry"] > 0
            traces.append({
                "x": [str(d) for d in result.index[entry_idx]],
                "y": _sanitize_series(result["close"][entry_idx]),
                "type": "scatter", "mode": "markers", "name": "Entry",
                "marker": {"color": "#34d399", "size": 8, "symbol": "triangle-up"},
            })

        if "signal_exit" in result.columns:
            exit_idx = result["signal_exit"] > 0
            traces.append({
                "x": [str(d) for d in result.index[exit_idx]],
                "y": _sanitize_series(result["close"][exit_idx]),
                "type": "scatter", "mode": "markers", "name": "Exit",
                "marker": {"color": "#fb7185", "size": 8, "symbol": "triangle-down"},
            })

        result_data["chart_data"] = {
            "traces": traces,
            "layout": {
                "dragmode": "pan",
                "hovermode": "x unified",
                "showlegend": True,
                "legend": {"orientation": "h", "y": 1.1, "font": {"size": 9}},
            }
        }

        # Backtest (if requested via ?backtest=true)
        if request.args.get("backtest") == "true":
            bt = run_backtest(result)
            result_data["backtest"] = {
                "total_trades": bt.total_trades,
                "winning_trades": bt.winning_trades,
                "losing_trades": bt.losing_trades,
                "win_rate": bt.win_rate,
                "total_return_pct": bt.total_return_pct,
                "avg_return_pct": bt.avg_return_pct,
                "max_drawdown_pct": bt.max_drawdown_pct,
                "profit_factor": bt.profit_factor,
                "sharpe_ratio": bt.sharpe_ratio,
                "avg_bars_held": bt.avg_bars_held,
                "trades": bt.trades,
                "equity_curve": bt.equity_curve,
                "error": bt.error,
            }
        else:
            result_data["backtest"] = None

    except Exception as e:
        result_data["error"] = str(e)

    return jsonify(result_data)


@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """JSON stats about stored webhook data."""
    try:
        db = get_db()
        cursor = db.cursor()
        stats = {}
        for table in ["signals", "rsi", "stochastic", "lines"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except Exception:
                stats[table] = 0
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dashboard/table/<table_name>')
def api_dashboard_table(table_name):
    """JSON data for a specific webhook table."""
    if table_name not in ("signals", "rsi", "stochastic", "lines"):
        return jsonify({"error": f"Unknown table: {table_name}"}), 400
    try:
        db = get_db()
        df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 100", db)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/indicators')
def api_indicators():
    """List all available indicator types with their params."""
    from dsl.indicators import INDICATOR_REGISTRY, PATTERN_MAP
    indicators = []
    for name, info in sorted(INDICATOR_REGISTRY.items()):
        indicators.append({
            "type": info.type_name,
            "category": info.category,
            "description": info.description,
            "params": {k: v for k, v in info.params.items()},
            "vt_concept": info.vt_concept,
        })
    return jsonify({
        "indicators": indicators,
        "patterns": sorted(PATTERN_MAP.keys()),
        "categories": sorted(set(i["category"] for i in indicators)),
    })


def _auto_fix_compound_emas(indicators: list, compounds: list) -> list:
    """Replace compound EMA references with only EMAs that actually exist.
    
    Old strategies may reference ema_13 in compounds when only ema_5, ema_8, ema_20
    are defined. This auto-fixes them on save so users don't get validation errors.
    """
    ema_ids = {i["id"] for i in indicators if i.get("type") == "ema"}
    if not ema_ids:
        return compounds
    fixed = []
    for c in compounds:
        ctype = c.get("type", "")
        if ctype in ("ema_alignment", "ema_spread"):
            old_emas = c.get("params", {}).get("emas", [])
            valid = [e for e in old_emas if e in ema_ids]
            if len(valid) < 2:
                # Not enough valid EMAs — use the shortest ones available
                sorted_emas = sorted(ema_ids, key=lambda x: int(x.split("_")[-1]) if x.split("_")[-1].isdigit() else 999)
                valid = sorted_emas[:min(3, len(sorted_emas))]
            c["params"]["emas"] = valid
        elif ctype in ("pull_count", "candle_proximity"):
            old_ema = c.get("params", {}).get("ema", "")
            if old_ema and old_ema not in ema_ids:
                # Pick the shortest-period EMA
                sorted_emas = sorted(ema_ids, key=lambda x: int(x.split("_")[-1]) if x.split("_")[-1].isdigit() else 999)
                if sorted_emas:
                    c["params"]["ema"] = sorted_emas[0]
        fixed.append(c)
    return fixed


@app.route('/api/dsl', methods=['POST'])
def api_dsl_create():
    """Create a new DSL definition from JSON body."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "name is required"}), 400

        # Sanitize name for filename
        safe_name = name.lower().replace(" ", "-")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "-_")
        if not safe_name:
            return jsonify({"error": "Invalid name"}), 400

        dsl_file = DSL_EXAMPLES_DIR / f"{safe_name}.yaml"
        if dsl_file.exists():
            return jsonify({"error": f"DSL '{name}' already exists"}), 409

        # Build the YAML from the request
        yaml_data = {
            "name": name,
            "description": data.get("description", ""),
            "timeframe": data.get("timeframe", "1h"),
        }

        indicators = data.get("indicators", [])
        if indicators:
            yaml_data["indicators"] = [
                {"id": i["id"], "type": i["type"], "params": i.get("params", {})}
                for i in indicators
            ]

        compounds = data.get("compounds", [])
        if compounds:
            compounds = _auto_fix_compound_emas(data.get("indicators", []), compounds)
            yaml_data["compounds"] = [
                {"id": c["id"], "type": c["type"], "params": c.get("params", {})}
                for c in compounds
            ]

        patterns = data.get("patterns", [])
        if patterns:
            yaml_data["patterns"] = patterns

        plots = data.get("plots", [])
        if plots:
            yaml_data["plots"] = plots

        signals = data.get("signals", {})
        if signals:
            yaml_data["signals"] = {k: v for k, v in signals.items()}

        # Write YAML
        import yaml as _yaml
        with open(dsl_file, "w") as f:
            _yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        # Try parsing and validating
        dsl = IndicatorDSL.from_yaml_file(str(dsl_file))
        errors = dsl.validate()
        if errors:
            dsl_file.unlink()
            return jsonify({"error": f"Validation errors: {errors}"}), 400

        return jsonify({
            "status": "created",
            "name": dsl.name,
            "filename": f"{safe_name}.yaml",
            "path": str(dsl_file),
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dsl/test', methods=['POST'])
def api_dsl_test():
    """Test a DSL definition without saving: compute chart data and return."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        name = data.get("name", "test-indicator")
        # Build a temporary IndicatorDSL from the request data
        from dsl.schema import IndicatorDef, CompoundIndicator, PlotDef, SignalDef

        indicators = [IndicatorDef(id=i["id"], type=i["type"], params=i.get("params", {}))
                      for i in data.get("indicators", [])]
        compounds = [CompoundIndicator(id=c["id"], type=c["type"], params=c.get("params", {}))
                     for c in data.get("compounds", [])]
        patterns = data.get("patterns", [])
        signals = {}
        sigs = data.get("signals", {})
        if isinstance(sigs, dict):
            for k, v in sigs.items():
                if isinstance(v, str):
                    signals[k] = SignalDef(condition=v)
                elif isinstance(v, dict) and "condition" in v:
                    signals[k] = SignalDef(condition=v["condition"])

        dsl = IndicatorDSL(
            name=name,
            description=data.get("description", ""),
            timeframe=data.get("timeframe", "1h"),
            indicators=indicators,
            compounds=compounds,
            patterns=patterns,
            signals=signals,
        )

        errors = dsl.validate()
        if errors:
            return jsonify({"error": f"Validation errors: {errors}"}), 400

        # Compute
        ticker = data.get("ticker", "SYNTHETIC")
        interval = data.get("interval", "1h")
        period = data.get("period", "5d")
        df = fetch_ohlcv(ticker, interval=interval, period=period)
        result = compute_indicators(df, dsl)

        # Build result (same as api_dsl_detail chart builder)
        def _sanitize(v):
            return None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else float(round(v, 2))
        def _sanitize_series(s):
            return [_sanitize(v) for v in s]

        dates_str = [str(d) for d in result.index]
        traces = [
            {"x": dates_str, "y": _sanitize_series(result["close"]), "type": "scatter", "mode": "lines", "name": "Close", "line": {"color": "#94a3b8", "width": 1.2}},
        ]

        indicator_colors = ["#2962FF", "#00C853", "#FF6D00", "#D50000", "#7C4DFF"]
        for idx, ind in enumerate(dsl.indicators):
            if ind.id in result.columns:
                traces.append({
                    "x": dates_str, "y": _sanitize_series(result[ind.id]),
                    "type": "scatter", "mode": "lines", "name": ind.id,
                    "line": {"color": indicator_colors[idx % len(indicator_colors)], "width": 1},
                })

        if "signal_entry" in result.columns:
            entry_idx = result["signal_entry"] > 0
            traces.append({
                "x": [str(d) for d in result.index[entry_idx]],
                "y": _sanitize_series(result["close"][entry_idx]),
                "type": "scatter", "mode": "markers", "name": "Entry",
                "marker": {"color": "#34d399", "size": 8, "symbol": "triangle-up"},
            })
        if "signal_exit" in result.columns:
            exit_idx = result["signal_exit"] > 0
            traces.append({
                "x": [str(d) for d in result.index[exit_idx]],
                "y": _sanitize_series(result["close"][exit_idx]),
                "type": "scatter", "mode": "markers", "name": "Exit",
                "marker": {"color": "#fb7185", "size": 8, "symbol": "triangle-down"},
            })

        return jsonify({
            "chart_data": {"traces": traces, "layout": {"dragmode": "pan", "hovermode": "x unified", "showlegend": True, "legend": {"orientation": "h", "y": 1.1}}},
            "stats": {
                "entry_count": int(result["signal_entry"].sum()) if "signal_entry" in result.columns else 0,
                "exit_count": int(result["signal_exit"].sum()) if "signal_exit" in result.columns else 0,
                "total_bars": len(result),
                "signal_density": round((int(result.get("signal_entry", pd.Series([0])).sum()) + int(result.get("signal_exit", pd.Series([0])).sum())) / len(result) * 100, 1),
            },
            "date_range": f"{result.index[0].strftime('%Y-%m-%d')} → {result.index[-1].strftime('%Y-%m-%d')} ({len(result)} bars)",
            "pine_code": generate_pinescript(dsl),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500




@app.route('/api/dsl/<name>', methods=['PUT'])
def api_dsl_update(name):
    """Update an existing DSL definition."""
    dsl_file = DSL_EXAMPLES_DIR / f"{name}.yaml"
    if not dsl_file.exists():
        for f in DSL_EXAMPLES_DIR.glob("*.yaml"):
            try:
                d = IndicatorDSL.from_yaml_file(str(f))
                if d.name == name or f.stem == name:
                    dsl_file = f
                    break
            except Exception:
                continue
        else:
            return jsonify({"error": f"DSL '{name}' not found"}), 404

    try:
        data = request.get_json()
        new_name = data.get("name", name).strip()
        safe_name = new_name.lower().replace(" ", "-")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "-_")

        # If renaming, handle old file
        new_file = DSL_EXAMPLES_DIR / f"{safe_name}.yaml"
        if new_file != dsl_file and new_file.exists():
            return jsonify({"error": f"DSL '{new_name}' already exists"}), 409

        yaml_data = {
            "name": new_name,
            "description": data.get("description", ""),
            "timeframe": data.get("timeframe", "1h"),
        }
        indicators = data.get("indicators", [])
        if indicators:
            yaml_data["indicators"] = [
                {"id": i["id"], "type": i["type"], "params": i.get("params", {})}
                for i in indicators
            ]
        compounds = data.get("compounds", [])
        if compounds:
            compounds = _auto_fix_compound_emas(data.get("indicators", []), compounds)
            yaml_data["compounds"] = [
                {"id": c["id"], "type": c["type"], "params": c.get("params", {})}
                for c in compounds
            ]
        patterns = data.get("patterns", [])
        if patterns:
            yaml_data["patterns"] = patterns
        signals = data.get("signals", {})
        if signals:
            yaml_data["signals"] = {k: v for k, v in signals.items()}

        import yaml as _yaml
        with open(new_file, "w") as f:
            _yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        # Validate
        dsl = IndicatorDSL.from_yaml_file(str(new_file))
        errors = dsl.validate()
        if errors:
            new_file.unlink()
            return jsonify({"error": f"Validation errors: {errors}"}), 400

        # Clean up old file if renamed
        if new_file != dsl_file and dsl_file.exists():
            dsl_file.unlink()

        return jsonify({
            "status": "updated",
            "name": dsl.name,
            "filename": f"{safe_name}.yaml",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dsl/<name>', methods=['DELETE'])
def api_dsl_delete(name):
    """Delete a DSL definition."""
    dsl_file = DSL_EXAMPLES_DIR / f"{name}.yaml"
    if not dsl_file.exists():
        for f in DSL_EXAMPLES_DIR.glob("*.yaml"):
            try:
                d = IndicatorDSL.from_yaml_file(str(f))
                if d.name == name or f.stem == name:
                    dsl_file = f
                    break
            except Exception:
                continue
        else:
            return jsonify({"error": f"DSL '{name}' not found"}), 404

    dsl_file.unlink()
    return jsonify({"status": "deleted", "name": name})


@app.route('/api/advisor/suggest', methods=['POST'])
def api_advisor_suggest():
    """Analyze market data and suggest an indicator combo.

    Accepts optional user preferences for personalized strategy suggestions
    and multi-timeframe analysis for trend alignment.
    """
    try:
        data = request.get_json() or {}
        ticker = data.get("ticker", "BTC-USD")
        interval = data.get("interval", "1h")
        period = data.get("period", "7d")
        preferences = data.get("preferences", {})

        trade_style = preferences.get("trade_style", "intraday")
        risk_level = preferences.get("risk_level", "moderate")
        instrument_type = preferences.get("instrument_type", "crypto")
        direction_bias = preferences.get("direction_bias", "both")

        # ── Higher timeframe for multi-TF analysis ──
        tf_map = {"15m": "1h", "30m": "1h", "1h": "4h", "4h": "1d", "1d": "1w"}
        higher_tf = tf_map.get(interval, "4h")

        # Fetch current TF data
        df = fetch_ohlcv(ticker, interval=interval, period=period)
        if df.empty or len(df) < 20:
            return jsonify({"error": f"Not enough data for {ticker} ({len(df)} bars, need 20+)"}), 400

        # Fetch higher TF data for alignment check
        df_higher = fetch_ohlcv(ticker, interval=higher_tf, period="1mo" if higher_tf == "1w" else "2mo")
        has_higher_tf = not df_higher.empty and len(df_higher) >= 5

        c = df["close"]
        h = df["high"]
        l = df["low"]
        v = df["volume"]

        # ── Analysis ──
        returns = c.pct_change().dropna()

        # Trend strength
        trend_strength = abs(c.diff().mean()) / c.diff().std() if c.diff().std() > 0 else 0
        is_trending = trend_strength > 0.15

        # Volatility regime
        atr_val = (h - l).mean() / c.mean()
        is_volatile = atr_val > 0.02

        # RSI estimate
        rsi_val = 100 - (100 / (1 + returns[returns > 0].mean() / abs(returns[returns < 0].mean()))) if returns[returns < 0].mean() != 0 else 50
        is_overbought = rsi_val > 60
        is_oversold = rsi_val < 40

        # Volume
        vol_ratio = v.iloc[-20:].mean() / v.mean() if v.mean() > 0 else 1
        high_volume = vol_ratio > 1.2
        low_volume = vol_ratio < 0.8

        # MA50
        ma50 = c.rolling(50).mean().iloc[-1] if len(c) >= 50 else c.mean()
        above_ma = c.iloc[-1] > ma50

        # ── Multi-TF analysis ──
        multi_tf = {}
        if has_higher_tf:
            ch = df_higher["close"]
            hh = df_higher["high"]
            lh = df_higher["low"]
            # Higher TF trend direction
            ma20_h = ch.rolling(20).mean()
            ma50_h = ch.rolling(50).mean() if len(ch) >= 50 else None
            higher_trend = "up" if (not ma50_h is None and ch.iloc[-1] > ma50_h.iloc[-1]) else \
                           "down" if (not ma50_h is None and ch.iloc[-1] < ma50_h.iloc[-1]) else "sideways"
            # Higher TF ATR
            atr_h = (hh - lh).mean() / ch.mean()
            # Higher TF RSI
            ret_h = ch.pct_change().dropna()
            rsi_h = 100 - (100 / (1 + ret_h[ret_h > 0].mean() / abs(ret_h[ret_h < 0].mean()))) if ret_h[ret_h < 0].mean() != 0 else 50
            # Trend alignment between TFs
            trend_aligned = (higher_trend == "up" and above_ma) or (higher_trend == "down" and not above_ma)
            multi_tf = {
                "higher_interval": higher_tf,
                "higher_trend": higher_trend,
                "higher_rsi": round(float(rsi_h), 1),
                "higher_atr_pct": round(float(atr_h * 100), 2),
                "trend_aligned": bool(trend_aligned),
            }
        else:
            multi_tf = {
                "higher_interval": higher_tf,
                "higher_trend": "unknown",
                "higher_rsi": 0,
                "higher_atr_pct": 0,
                "trend_aligned": True,  # no conflicting info
            }

        # ── Instrument personality ──
        inst_profiles = {
            "crypto": {
                "name": "crypto",
                "atr_threshold": 0.025,  # naturally more volatile
                "trend_threshold": 0.20,  # needs stronger trend
                "prefers": "momentum",
                "avoids": "tight mean reversion",
                "note": "24/7 market, gap risk, news-driven spikes",
            },
            "forex": {
                "name": "forex",
                "atr_threshold": 0.008,  # lower vol
                "trend_threshold": 0.12,
                "prefers": "session-based trend",
                "avoids": "overnight holds without stop",
                "note": "Session matters (London/NY overlap is prime)",
            },
            "stocks": {
                "name": "stocks",
                "atr_threshold": 0.015,
                "trend_threshold": 0.15,
                "prefers": "trend following",
                "avoids": "trading through earnings",
                "note": "Smoother, after-hours gaps, earnings events",
            },
            "indices": {
                "name": "indices",
                "atr_threshold": 0.01,
                "trend_threshold": 0.15,
                "prefers": "mean reversion on short TFs, trend on long",
                "avoids": "over-leveraging in low vol",
                "note": "Mean reverting intraday, trending on daily+",
            },
        }
        inst = inst_profiles.get(instrument_type, inst_profiles["crypto"])

        # ── Build personalized suggestion ──
        suggestion_id = f"advisor-{ticker.lower().replace('-', '').replace('=', '')}"
        indicators = []
        compounds = []
        patterns = []
        signals = {}
        explanation_parts = []

        def add_standard_emas():
            if trade_style == "scalp":
                return [3, 5, 8]
            elif trade_style == "intraday":
                return [5, 8, 13]
            else:  # swing
                return [8, 13, 21]

        ema_periods = add_standard_emas()
        for p in ema_periods:
            indicators.append({"id": f"ema_{p}", "type": "ema", "params": {"period": p}})

        indicators.append({"id": "rsi", "type": "rsi", "params": {"period": 14}})
        indicators.append({"id": "atr", "type": "atr", "params": {"period": 14}})

        compounds.append({
            "id": "alignment",
            "type": "ema_alignment",
            "params": {"emas": [f"ema_{p}" for p in ema_periods]},
        })
        compounds.append({
            "id": "spread",
            "type": "ema_spread",
            "params": {"emas": [f"ema_{p}" for p in ema_periods]},
        })
        compounds.append({
            "id": "pull",
            "type": "pull_count",
            "params": {"ema": f"ema_{ema_periods[0]}"},
        })
        compounds.append({
            "id": "proximity",
            "type": "candle_proximity",
            "params": {"ema": f"ema_{ema_periods[0]}"},
        })

        # ── Strategy selection ──
        # Override volatility detection for instrument type
        local_volatile = atr_val > inst["atr_threshold"]
        local_trending = trend_strength > inst["trend_threshold"]

        # Adjust signals based on risk
        rsi_entry_threshold = 30 if risk_level == "aggressive" else 35 if risk_level == "moderate" else 40
        rsi_exit_threshold = 70 if risk_level == "aggressive" else 65 if risk_level == "moderate" else 60
        pull_exit_threshold = 2 if risk_level == "aggressive" else 3 if risk_level == "moderate" else 4

        if direction_bias == "short":
            rsi_entry_threshold, rsi_exit_threshold = 70, 30

        # Strategy: Trending
        if local_trending and (not local_volatile or risk_level == "aggressive"):
            explanation_parts.append(f"📈 Trending on {interval} (strength={trend_strength:.2f})")
            if has_higher_tf:
                if multi_tf["trend_aligned"]:
                    explanation_parts.append(f"✅ {higher_tf} trend aligns — higher confidence")
                else:
                    explanation_parts.append(f"⚠️ {higher_tf} trend ({multi_tf['higher_trend']}) conflicts — reduce position size")
            if above_ma:
                if direction_bias != "short":
                    signals["entry"] = f"alignment == 1 AND rsi > 50 AND proximity < 0"
                    signals["exit"] = f"alignment == -1 OR (pull >= {pull_exit_threshold} AND rsi > 70)"
                    explanation_parts.append(f"→ Bull trend: EMA alignment + RSI>50, exit on trend reversal or {pull_exit_threshold}+ candles above EMA if overbought")
                else:
                    signals["entry"] = "false"
                    explanation_parts.append("→ Skipping long entries (short bias)")
            else:
                if direction_bias != "long":
                    signals["entry"] = f"alignment == -1 AND rsi < 50 AND proximity > 0"
                    signals["exit"] = f"alignment == 1 OR (pull >= {pull_exit_threshold} AND rsi < 30)"
                    explanation_parts.append(f"→ Bear trend: EMA alignment + RSI<50, exit on trend reversal or oversold pullback")
                else:
                    signals["entry"] = "false"
                    explanation_parts.append("→ Skipping short entries (long bias)")

        # Strategy: Volatile / Squeeze
        elif local_volatile:
            explanation_parts.append(f"⚡ Volatile market (ATR={atr_val*100:.1f}%)")
            patterns.extend(["hammer", "shooting_star"])
            if instrument_type == "crypto":
                signals["entry"] = f"CROSSOVER(ema_{ema_periods[0]}, ema_{ema_periods[-1]}) AND rsi > 50"
                signals["exit"] = f"pull >= {pull_exit_threshold} AND rsi < 45"
                explanation_parts.append("→ Crypto vol: EMA crossover + RSI confirmation, exit when momentum fades")
            elif instrument_type == "forex":
                signals["entry"] = f"spread < 0.003 AND CROSSOVER(ema_{ema_periods[0]}, ema_{ema_periods[-1]})"
                signals["exit"] = f"pull >= {pull_exit_threshold} AND spread > 0.008"
                explanation_parts.append("→ Forex vol: squeeze breakout, exit on EMA spread expansion")
            else:
                signals["entry"] = f"spread < 0.005 AND (hammer OR proximity > 2)"
                signals["exit"] = f"pull >= {pull_exit_threshold} AND proximity < -1"
                explanation_parts.append("→ Tight spread + candle pattern = breakout entry, exit on pullback below EMA")

        # Strategy: Ranging / Mean Reversion
        else:
            explanation_parts.append(f"🌊 Ranging (RSI ≈ {rsi_val:.0f})")
            patterns.append("hammer")
            if instrument_type == "forex":
                signals["entry"] = f"rsi < {rsi_entry_threshold} AND proximity < -1 AND NOT session_slow"
                explanation_parts.append("→ Oversold during active sessions at EMA touch")
            else:
                signals["entry"] = f"proximity < -1 AND rsi < {rsi_entry_threshold}"
                explanation_parts.append("→ Price at EMA touch + oversold RSI — mean reversion entry")
            # Exit at the other side of the range: price back above EMA + mid-range RSI
            signals["exit"] = f"proximity > 0.5 AND rsi > {rsi_exit_threshold - 10}"

        if high_volume:
            explanation_parts.append(f"📊 High volume (x{vol_ratio:.1f}) — confirms conviction")
        elif low_volume:
            explanation_parts.append(f"📊 Low volume (x{vol_ratio:.1f}) — weak moves, cautious")

        # Sentiment
        if is_overbought:
            explanation_parts.append("⚠️ Market near overbought — exits may trigger")
        elif is_oversold:
            explanation_parts.append("⚠️ Market near oversold — entries may trigger")

        # Risk note
        if risk_level == "conservative":
            explanation_parts.append("🛡️ Conservative: prefer tight stops, smaller positions")
        elif risk_level == "aggressive":
            explanation_parts.append("🔥 Aggressive: wider stops, higher frequency")

        # Instrument note
        explanation_parts.append(f"ℹ️ {inst['note']}")

        # Build suggested DSL
        suggested_dsl = {
            "name": f"{ticker} Advisor",
            "description": f"Advisor-suggested for {ticker} ({interval}) — {inst['name']}, {trade_style}",
            "timeframe": interval,
            "indicators": indicators,
            "compounds": compounds,
            "patterns": patterns,
            "signals": signals,
            "plots": [{"ref": f"ema_{p}", "style": "line"} for p in ema_periods],
        }

        # Verify signals against real data
        signal_verified = False
        entry_bar_count = 0
        exit_bar_count = 0
        if signals.get("entry") and signals["entry"] != "false":
            try:
                from dsl.schema import IndicatorDSL as TestDSL, IndicatorDef as TID, CompoundIndicator as TC, SignalDef as TSD
                from generators.local import compute_indicators
                test_indicators = [TID(id=f"ema_{p}", type="ema", params={"period": p}) for p in ema_periods]
                test_indicators.append(TID(id="rsi", type="rsi", params={"period": 14}))
                test_indicators.append(TID(id="atr", type="atr", params={"period": 14}))
                test_compounds = [
                    TC(id="alignment", type="ema_alignment", params={"emas": [f"ema_{p}" for p in ema_periods]}),
                    TC(id="spread", type="ema_spread", params={"emas": [f"ema_{p}" for p in ema_periods]}),
                    TC(id="pull", type="pull_count", params={"ema": f"ema_{ema_periods[0]}"}),
                    TC(id="proximity", type="candle_proximity", params={"ema": f"ema_{ema_periods[0]}"}),
                ]
                test_dsl = TestDSL(
                    name="_verify", timeframe=interval,
                    indicators=test_indicators, compounds=test_compounds,
                    patterns=patterns, signals={
                        k: TSD(condition=v) for k, v in signals.items()
                    }, plots=[],
                )
                result_df = compute_indicators(df, test_dsl)
                if "signal_entry" in result_df.columns:
                    entry_bar_count = int(result_df["signal_entry"].sum())
                    exit_bar_count = int(result_df["signal_exit"].sum()) if "signal_exit" in result_df.columns else 0
                    signal_verified = True
                    total = len(result_df)
                    if entry_bar_count == 0:
                        explanation_parts.append(
                            f"⚠️ 0 entry signals in {total} bars — thresholds may be too tight"
                        )
                    else:
                        explanation_parts.append(
                            f"📊 {entry_bar_count} entries, {exit_bar_count} exits in {total} bars ({entry_bar_count/total*100:.1f}% hit rate)"
                        )
            except Exception as e:
                import traceback
                traceback.print_exc()
                explanation_parts.append(f"⚠️ Signal verification failed: {type(e).__name__}: {e}")

        return jsonify({
            "ticker": ticker,
            "interval": interval,
            "period": period,
            "preferences": {
                "trade_style": trade_style,
                "risk_level": risk_level,
                "instrument_type": instrument_type,
                "direction_bias": direction_bias,
            },
            "multi_tf": multi_tf,
            "analysis": {
                "trend_strength": round(float(trend_strength), 3),
                "is_trending": bool(is_trending),
                "is_volatile": bool(is_volatile),
                "atr_pct": round(float(atr_val * 100), 2),
                "rsi_estimate": round(float(rsi_val), 1),
                "above_ma": bool(above_ma),
                "volume_ratio": round(float(vol_ratio), 2),
                "bar_count": int(len(df)),
                "date_range": f"{df.index[0].strftime('%Y-%m-%d')} → {df.index[-1].strftime('%Y-%m-%d')}",
                "entry_signals": entry_bar_count,
                "exit_signals": exit_bar_count,
                "signal_verified": signal_verified,
            },
            "explanation": explanation_parts,
            "suggested_dsl": suggested_dsl,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# COMPARISON HARNESS
# ════════════════════════════════════════════════════════════════════════════

@app.route('/api/harness/compare', methods=['POST'])
def api_harness_compare():
    """Compare multiple strategies across instruments on identical data.

    Body: {
      "dsls": [ {name, indicators, compounds, patterns, signals}, ... ],
      "tickers": ["BTC-USD", ...],
      "interval": "1h",
      "period": "1mo",
      "random_iters": 60
    }

    Returns a matrix of rows, one per strategy x ticker, with backtest
    metrics plus baselines (buy & hold, random entries) and an edge verdict.
    """
    try:
        data = request.get_json() or {}
        raw_dsls = data.get("dsls", [])
        tickers = data.get("tickers", ["BTC-USD"])
        interval = data.get("interval", "1h")
        period = data.get("period", "1mo")
        random_iters = int(data.get("random_iters", 60))

        if not raw_dsls:
            return jsonify({"error": "Provide at least one DSL definition"}), 400
        if not tickers:
            return jsonify({"error": "Provide at least one ticker"}), 400

        from dsl.schema import IndicatorDef, CompoundIndicator, PlotDef, SignalDef

        dsls = []
        for raw in raw_dsls:
            indicators = [IndicatorDef(id=i["id"], type=i["type"], params=i.get("params", {}))
                          for i in raw.get("indicators", [])]
            compounds = [CompoundIndicator(id=c["id"], type=c["type"], params=c.get("params", {}))
                         for c in raw.get("compounds", [])]
            patterns = raw.get("patterns", [])
            signals = {}
            sigs = raw.get("signals", {})
            if isinstance(sigs, dict):
                for k, v in sigs.items():
                    if isinstance(v, str):
                        signals[k] = SignalDef(condition=v)
                    elif isinstance(v, dict) and "condition" in v:
                        signals[k] = SignalDef(condition=v["condition"])
            dsls.append(IndicatorDSL(
                name=raw.get("name", "unnamed"),
                description=raw.get("description", ""),
                timeframe=raw.get("timeframe", interval),
                indicators=indicators,
                compounds=compounds,
                patterns=patterns,
                signals=signals,
            ))

        result = run_comparison(dsls, tickers, interval, period, random_iters)
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ════════════════════════════════════════════════════════════════════════════

conn = sqlite3.connect('trade.db')
print("CONNECTED TO DATABASE: ", conn)
cursor = conn.cursor()

cursor.execute(
    """
     CREATE TABLE IF NOT EXISTS lines (
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ticker TEXT,
        condition REAL

    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS signals (
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ticker TEXT,
        order_action TEXT,
        order_contracts INTEGER,
        order_price REAL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS rsi (
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ticker TEXT,
        rsi REAL
    )
    """
)
conn.commit()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS stochastic (
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ticker TEXT,
        stochastic REAL
    )
    """
)
conn.commit()



# SPA catch-all: serve index.html for client-side routing
if _web_dist.exists():
    @app.errorhandler(404)
    def spa_fallback(e):
        return app.send_static_file("index.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


'''
logged output: 


conditions: 
    - if rsi > 50 --> isabove50
    - if rsi < 50 --> isbelow50
    - "name": "TL1", "id": "", "timeStart": "", ....


    "top1": "", count, hits, 
    "bottom1: ""

    - 

    



" if rsi > xx and ....

ML:
output = [[0.1],[0.22],[]]

'''