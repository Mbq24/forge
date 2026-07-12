# Stage 1: Build React app
FROM node:20-alpine AS react-build
WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci && npm cache clean --force
COPY web/ .
RUN npm run build

# Stage 2: Python Flask API + serve React SPA
FROM python:3.10-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python app code
COPY dsl/ dsl/
COPY generators/ generators/
COPY examples/ examples/
COPY tradingview/ tradingview/
COPY tv-indicator .

# Copy built React SPA
COPY --from=react-build /app/web/dist tradingview/web_dist/

# Set working directory to tradingview for Flask app
WORKDIR /app/tradingview

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
