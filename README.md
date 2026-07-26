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

You need **two terminals** — one for the backend, one for the frontend.

### Prerequisites

- Python 3.10+ (`python3 --version`)
- Node 20+ (`node --version`)

### 1. Backend (Flask API)

```sh
# From the project root
cd "/Users/mark/Library/Mobile Documents/com~apple~CloudDocs/VisualStudioProjects/Forge"

# One-time setup (skip if already done)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the server (cd into tradingview/ so Flask finds app.py + .flaskenv)
cd tradingview
flask run --port 5000
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

> **Note:** The `.flaskenv` file in `tradingview/` sets `FLASK_APP=app` and `FLASK_DEBUG=1` automatically. That's why you need to `cd tradingview` before running `flask run`.

### 2. Frontend (React SPA)

*Open a **second terminal** and run:*

```sh
cd "/Users/mark/Library/Mobile Documents/com~apple~CloudDocs/VisualStudioProjects/Forge/web"

# One-time setup (skip if already done)
npm install

# Start dev server
npm run dev
```

You should see:
```
  VITE v4.x  ready in XXXms
  ➜  Local:   http://localhost:3000/
```

### 3. Open the app

- **UI:** http://localhost:3000
- **API (direct):** http://localhost:5000

The Vite dev server proxies `/api/*` calls to Flask on port 5000, so everything works together.

### 4. Verify it works

1. Backend terminal shows Flask running on port 5000
2. Frontend terminal shows Vite running on port 3000
3. Open http://localhost:3000 — you should see the Forge dashboard

## Push changes & Deploy

### 1. Commit and push to GitHub

```sh
cd "/Users/mark/Library/Mobile Documents/com~apple~CloudDocs/VisualStudioProjects/Forge"

# Stage your changes
git add -A

# Commit with a descriptive message
git commit -m "What you changed — be specific"

# Push to GitHub
git push
```

Check it at https://github.com/Mbq24/forge

### 2. Deploy to Railway

```sh
cd "/Users/mark/Library/Mobile Documents/com~apple~CloudDocs/VisualStudioProjects/Forge"

# Build the React frontend for production
cd web && npm run build && cd ..

# Deploy to Railway
railway up
```

That's it. Railway reads the `Dockerfile` at the project root, which:
1. Builds the React app in a Node container
2. Copies the Python app into a slim container
3. Serves everything via gunicorn on port 8080

The app will be live at https://forge-production-0c60.up.railway.app (or whatever URL Railway assigns).

## Changelog

| Date | Change |
|------|--------|
| — | Initial scaffold from DockerTVWebhook. Flask + SQLite + Plotly Dash. |
| — | Pivot to YAML DSL indicator definitions with Pine Script generation. |
| — | React SPA frontend with DSL builder, advisor, templates, backtesting. |
| — | Railway deployment. Fixed stochastic generator (tuple destructure → explicit k/d). |
| Jul 24 | Cleaned up git tracking: removed `node_modules/`, `__pycache__/`, `.db` files from version control. Updated `.gitignore`. Added SPX to Advisor ticker list. |

> *Add your changes below this line as you make them.*

