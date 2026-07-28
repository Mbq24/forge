import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchAdvisorSuggestion, AdvisorSuggestion, AdvisorPrefs } from '../api'

const TICKERS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AAPL', 'MSFT', 'NVDA', 'SPY', 'XAUUSD=X', 'EURUSD=X', 'SPX']
const INTERVALS = ['15m', '30m', '1h', '4h', '1d']
const PERIODS = ['5d', '7d', '1mo']
const TRADE_STYLES: AdvisorPrefs['trade_style'][] = ['scalp', 'intraday', 'swing']
const RISK_LEVELS: AdvisorPrefs['risk_level'][] = ['conservative', 'moderate', 'aggressive']
const INSTRUMENTS: { value: AdvisorPrefs['instrument_type']; label: string }[] = [
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
  { value: 'stocks', label: 'Stocks' },
  { value: 'indices', label: 'Indices' },
]
const DIRECTION_BIASES: AdvisorPrefs['direction_bias'][] = ['both', 'long', 'short']

const STORAGE_KEY = 'forge-advisor-prefs'

function loadPrefs(): AdvisorPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {}
  return { trade_style: 'intraday', risk_level: 'moderate', instrument_type: 'crypto', direction_bias: 'both' }
}

export default function Advisor() {
  const navigate = useNavigate()
  const [savedPrefs, setSavedPrefs] = useState<AdvisorPrefs>(loadPrefs)

  // Controls
  const [ticker, setTicker] = useState('BTC-USD')
  const [interval, setInterval] = useState('1h')
  const [period, setPeriod] = useState('7d')
  const [prefs, setPrefs] = useState<AdvisorPrefs>(savedPrefs)
  const [showPrefs, setShowPrefs] = useState(false)

  const [result, setResult] = useState<AdvisorSuggestion | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const savePrefs = (p: AdvisorPrefs) => {
    setPrefs(p)
    setSavedPrefs(p)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p))
  }

  // Reset preferences to match the saved defaults when toggling panel
  const resetPrefs = () => {
    setPrefs(savedPrefs)
  }

  const handleSuggest = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await fetchAdvisorSuggestion(ticker, interval, period, prefs)
      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTestSuggestion = async () => {
    if (!result) return
    try {
      const res = await fetch('/api/dsl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result.suggested_dsl),
      })
      if (!res.ok) {
        const err = await res.json()
        if (res.status === 409) {
          // Already exists — update with the new suggestion
          const safeName = result.suggested_dsl.name.toLowerCase().replace(/ /g, '-').replace(/[^a-z0-9_-]/g, '')
          const updateRes = await fetch(`/api/dsl/${encodeURIComponent(safeName)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(result.suggested_dsl),
          })
          if (!updateRes.ok) {
            const updateErr = await updateRes.json()
            throw new Error(updateErr.error || 'Failed to update')
          }
          navigate(`/dsl/${encodeURIComponent(safeName)}`)
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
          <div className="page-title">🔮 Advisor</div>
          <div className="page-subtitle">Personalized indicator suggestions based on market data + your preferences</div>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Data Source</span>
          <button className="btn btn-sm" onClick={() => { setShowPrefs(!showPrefs); if (!showPrefs) resetPrefs() }}>
            {showPrefs ? '▲ Hide' : '▼ Customize'}
          </button>
        </div>
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

          {/* Preferences panel */}
          {showPrefs && (
            <div style={{ marginTop: '0.75rem', padding: '0.75rem', border: '1px solid var(--border)', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>
                These are saved to your browser — set once, used every time.
              </div>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <div>
                  <label className="form-label">Trade Style</label>
                  <select className="form-select" value={prefs.trade_style} onChange={e => savePrefs({ ...prefs, trade_style: e.target.value as any })} style={{ minWidth: 110 }}>
                    {TRADE_STYLES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">Risk Level</label>
                  <select className="form-select" value={prefs.risk_level} onChange={e => savePrefs({ ...prefs, risk_level: e.target.value as any })} style={{ minWidth: 120 }}>
                    {RISK_LEVELS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">Instrument</label>
                  <select className="form-select" value={prefs.instrument_type} onChange={e => savePrefs({ ...prefs, instrument_type: e.target.value as any })} style={{ minWidth: 100 }}>
                    {INSTRUMENTS.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">Direction</label>
                  <select className="form-select" value={prefs.direction_bias} onChange={e => savePrefs({ ...prefs, direction_bias: e.target.value as any })} style={{ minWidth: 90 }}>
                    {DIRECTION_BIASES.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="grid grid-2" style={{ gridTemplateColumns: '1.3fr 1fr' }}>
          {/* Left: Analysis */}
          <div>
            {/* Current TF analysis */}
            <div className="card">
              <div className="card-header">{result.ticker} ({result.interval}) — {result.preferences.instrument_type}, {result.preferences.trade_style}</div>
              <div className="card-body">
                <div className="grid grid-3" style={{ marginBottom: '0.75rem' }}>
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
                <div className="grid grid-2" style={{ fontSize: '0.8rem', marginBottom: '0.5rem' }}>
                  <div><strong>RSI:</strong> {result.analysis.rsi_estimate}</div>
                  <div><strong>Trend Strength:</strong> {result.analysis.trend_strength}</div>
                  <div><strong>Above MA50:</strong> {result.analysis.above_ma ? '✅ Yes' : '❌ No'}</div>
                  <div><strong>Volume Ratio:</strong> x{result.analysis.volume_ratio}</div>
                </div>
                {result.analysis.signal_verified && (
                  <div style={{ fontSize: '0.8rem', padding: '4px 8px', background: 'var(--bg-secondary)', borderRadius: '4px', marginTop: '4px' }}>
                    <strong>Signals:</strong> {result.analysis.entry_signals} entries, {result.analysis.exit_signals} exits / {result.analysis.bar_count} bars
                  </div>
                )}
                <div style={{ color: 'var(--text-dim)', fontSize: '0.78rem' }}>
                  {result.analysis.date_range}
                </div>
              </div>
            </div>

            {/* Multi-TF analysis */}
            {result.multi_tf && result.multi_tf.higher_trend !== 'unknown' && (
              <div className="card">
                <div className="card-header">Multi-Timeframe — {result.multi_tf.higher_interval}</div>
                <div className="card-body">
                  <div className="grid grid-3" style={{ marginBottom: '0.5rem' }}>
                    <div className="stat-box" style={{ borderColor: result.multi_tf.higher_trend === 'up' ? 'var(--emerald)' : result.multi_tf.higher_trend === 'down' ? 'var(--rose)' : 'var(--border)' }}>
                      <div className="value" style={{ color: result.multi_tf.higher_trend === 'up' ? 'var(--emerald)' : result.multi_tf.higher_trend === 'down' ? 'var(--rose)' : 'var(--text-dim)' }}>
                        {result.multi_tf.higher_trend === 'up' ? '📈 Up' : result.multi_tf.higher_trend === 'down' ? '📉 Down' : '➡️ Sideways'}
                      </div>
                      <div className="label">Trend</div>
                    </div>
                    <div className="stat-box amber">
                      <div className="value">{result.multi_tf.higher_atr_pct}%</div>
                      <div className="label">ATR</div>
                    </div>
                    <div className="stat-box" style={{ borderColor: result.multi_tf.trend_aligned ? 'var(--emerald)' : 'var(--amber)' }}>
                      <div className="value" style={{ color: result.multi_tf.trend_aligned ? 'var(--emerald)' : 'var(--amber)' }}>
                        {result.multi_tf.trend_aligned ? '✅ Aligned' : '⚠️ Conflict'}
                      </div>
                      <div className="label">vs {result.interval}</div>
                    </div>
                  </div>
                  <div style={{ fontSize: '0.8rem' }}>
                    <strong>RSI:</strong> {result.multi_tf.higher_rsi}
                  </div>
                </div>
              </div>
            )}

            {/* Explanation */}
            <div className="card">
              <div className="card-header">Strategy Rationale</div>
              <div className="card-body">
                {result.explanation.map((line, i) => (
                  <div key={i} style={{ padding: '4px 0', fontSize: '0.85rem', borderBottom: i < result.explanation.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    {line}
                  </div>
                ))}
              </div>
            </div>

            {/* Save button */}
            {result.suggested_dsl.signals?.entry && result.suggested_dsl.signals?.entry !== 'false' && (
              <div className="card">
                <div className="card-body">
                  <button className="btn btn-primary" onClick={handleTestSuggestion}>
                    🧪 Test This Strategy
                  </button>
                </div>
              </div>
            )}
            {result.suggested_dsl.signals?.entry === 'false' && (
              <div className="card">
                <div className="card-body" style={{ color: 'var(--amber)', fontSize: '0.85rem' }}>
                  ⚠️ No entry signal generated — your direction bias excludes this market's current regime.
                </div>
              </div>
            )}
          </div>

          {/* Right: DSL YAML Preview */}
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
