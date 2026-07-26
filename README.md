# Forge — Indicator DSL Studio

A platform for defining, testing, and generating TradingView Pine Script indicators using a declarative YAML DSL.

## Architecture

```
web/            React SPA (Vite + TypeScript) — frontend UI
tradingview/    Flask API backend — serves endpoints + React SPA in production
dsl/            YAML DSL schema, indicator registry, condition builder
generators/     Pine Script generator, local computation, backtesting
examples/       Pre-built indicator templates (8 strategies)
```

## Local Development

### Backend (Flask)

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd tradingview && flask run --port 5000
```

### Frontend (React)

*Separate terminal:*

```sh
cd web
npm install
npm run dev       # starts on port 3000, proxies /api → localhost:5000
```

## Deploy

```sh
cd web && npm run build && cd ..
railway up
```

## Changelog

| Date | Change |
|------|--------|
| — | Initial scaffold from DockerTVWebhook. Flask + SQLite + Plotly Dash. |
| — | Pivot to YAML DSL indicator definitions with Pine Script generation. |
| — | React SPA frontend with DSL builder, advisor, templates, backtesting. |
| — | Railway deployment. Fixed stochastic generator (tuple destructure → explicit k/d). |
| Jul 24 | Cleaned up git tracking: removed `node_modules/`, `__pycache__/`, `.db` files from version control. Updated `.gitignore`. Added SPX to Advisor ticker list. |

> *Add your changes below this line as you make them.*

