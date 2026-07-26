import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchAdvisorSuggestion, AdvisorSuggestion } from '../api'

const TICKERS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AAPL', 'MSFT', 'NVDA', 'SPY', 'XAUUSD=X', 'EURUSD=X', 'SPX']
const INTERVALS = ['1h', '4h', '1d']
const PERIODS = ['5d', '7d', '1mo']

export default function Advisor() {
  const navigate = useNavigate()
  const [ticker, setTicker] = useState('BTC-USD')
  const [interval, setInterval] = useState('1h')
  const [period, setPeriod] = useState('7d')
  const [result, setResult] = useState<AdvisorSuggestion | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSuggest = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await fetchAdvisorSuggestion(ticker, interval, period)
      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTestSuggestion = async () => {
    if (!result) return
    // Save the suggested DSL, then navigate to its detail page
    try {
      const res = await fetch('/api/dsl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result.suggested_dsl),
      })
      if (!res.ok) {
        const err = await res.json()
        // If already exists, navigate to edit
        if (res.status === 409) {
          navigate(`/dsl/new?edit=${encodeURIComponent(result.suggested_dsl.name)}`)
          return
        }
        throw new Error(err.error || 'Failed to save')
      }
      const created = await res.json()
      navigate(`/dsl/${encodeURIComponent(created.name)}`)
    } catch (e: any) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">LLM Advisor</div>
          <div className="page-subtitle">Analyze market data and get indicator suggestions</div>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="card-header">Data Source</div>
        <div className="card-body">
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'end', flexWrap: 'wrap' }}>
            <div>
              <label className="form-label">Ticker</label>
              <select className="form-select" value={ticker} onChange={e => setTicker(e.target.value)} style={{ minWidth: 140 }}>
                {TICKERS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Interval</label>
              <select className="form-select" value={interval} onChange={e => setInterval(e.target.value)}>
                {INTERVALS.map(iv => <option key={iv} value={iv}>{iv}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Period</label>
              <select className="form-select" value={period} onChange={e => setPeriod(e.target.value)}>
                {PERIODS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <button className="btn btn-primary" onClick={handleSuggest} disabled={loading}>
                {loading ? 'Analyzing...' : '🔮 Suggest'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="grid grid-2" style={{ gridTemplateColumns: '1.3fr 1fr' }}>
          {/* Left: Analysis */}
          <div>
            <div className="card">
              <div className="card-header">Market Analysis — {result.ticker} ({result.interval})</div>
              <div className="card-body">
                <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
                  <div className="stat-box cyan">
                    <div className="value">{result.analysis.bar_count}</div>
                    <div className="label">Bars</div>
                  </div>
                  <div className="stat-box amber">
                    <div className="value">{result.analysis.atr_pct}%</div>
                    <div className="label">ATR</div>
                  </div>
                  <div className="stat-box" style={{ borderColor: result.analysis.is_trending ? 'var(--emerald)' : 'var(--border)' }}>
                    <div className="value" style={{ color: result.analysis.is_trending ? 'var(--emerald)' : 'var(--text-dim)' }}>
                      {result.analysis.is_trending ? 'Trending' : result.analysis.is_volatile ? 'Volatile' : 'Ranging'}
                    </div>
                    <div className="label">Regime</div>
                  </div>
                </div>

                <div className="grid grid-2" style={{ fontSize: '0.8rem', marginBottom: '1rem' }}>
                  <div><strong>RSI (est):</strong> {result.analysis.rsi_estimate}</div>
                  <div><strong>Trend Strength:</strong> {result.analysis.trend_strength}</div>
                  <div><strong>Above MA50:</strong> {result.analysis.above_ma ? '✅ Yes' : '❌ No'}</div>
                  <div><strong>Volume Ratio:</strong> x{result.analysis.volume_ratio}</div>
                </div>

                <div style={{ color: 'var(--text-dim)', fontSize: '0.78rem' }}>
                  {result.analysis.date_range}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">Explanation</div>
              <div className="card-body">
                {result.explanation.map((line, i) => (
                  <div key={i} style={{ padding: '4px 0', fontSize: '0.85rem', borderBottom: i < result.explanation.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    {line}
                  </div>
                ))}
              </div>
            </div>

            {/* Suggested DSL */}
            <div className="card">
              <div className="card-header">Suggested DSL</div>
              <div style={{ padding: 0 }}>
                <pre className="code-block" style={{ borderRadius: 0, border: 'none', maxHeight: '300px' }}>
                  {JSON.stringify(result.suggested_dsl, null, 2)}
                </pre>
              </div>
              <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--border)' }}>
                <button className="btn btn-primary" onClick={handleTestSuggestion}>
                  🧪 Test This Indicator
                </button>
              </div>
            </div>
          </div>

          {/* Right: DSL YAML + Pine */}
          <div>
            <div className="card">
              <div className="card-header">DSL (YAML Preview)</div>
              <div style={{ padding: 0 }}>
                <pre className="code-block" style={{ borderRadius: 0, border: 'none' }}>
                  {(() => {
                    const d = result.suggested_dsl
                    let y = `name: "${d.name}"\ndescription: "${d.description || ''}"\ntimeframe: "${d.timeframe}"\n`
                    if (d.indicators?.length) {
                      y += 'indicators:\n'
                      d.indicators.forEach((i: any) => {
                        const p = Object.keys(i.params || {}).length ? `  params: { ${Object.entries(i.params).map(([k, v]) => `${k}: ${v}`).join(', ')} }` : ''
                        y += `  - id: ${i.id}    type: ${i.type}    ${p}\n`
                      })
                    }
                    if (d.compounds?.length) {
                      y += 'compounds:\n'
                      d.compounds.forEach((c: any) => {
                        const p = Object.keys(c.params || {}).length ? `  params: { ${Object.entries(c.params).map(([k, v]) => `${k}: ${Array.isArray(v) ? `[${v.join(', ')}]` : v}`).join(', ')} }` : ''
                        y += `  - id: ${c.id}    type: ${c.type}    ${p}\n`
                      })
                    }
                    if (d.patterns?.length) y += `patterns: [${d.patterns.join(', ')}]\n`
                    if (d.signals) {
                      y += 'signals:\n'
                      Object.entries(d.signals).forEach(([k, v]) => y += `  ${k}: "${v}"\n`)
                    }
                    return y
                  })()}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
