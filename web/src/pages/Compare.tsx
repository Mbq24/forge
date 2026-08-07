import { useEffect, useState } from 'react'
import { fetchDslList, DslListItem, fetchHarnessCompare, HarnessResult } from '../api'

const TICKER_GROUPS: { label: string; tickers: string[] }[] = [
  { label: 'Crypto', tickers: ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD'] },
  { label: 'Metals', tickers: ['GC=F', 'SI=F'] },
  { label: 'Forex', tickers: ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'] },
  { label: 'Stocks', tickers: ['AAPL', 'MSFT', 'NVDA', 'SPY', 'QQQ'] },
]
const ALL_TICKERS = TICKER_GROUPS.flatMap(g => g.tickers)
const INTERVALS = ['15m', '30m', '1h', '4h', '1d']
const PERIODS = ['5d', '7d', '1mo', '3mo']

const TONE_COLOR: Record<string, string> = {
  emerald: 'var(--emerald)',
  amber: 'var(--amber)',
  rose: 'var(--rose)',
  dim: 'var(--text-dim)',
}
const REGIME_COLOR: Record<string, string> = {
  trending: 'var(--emerald)',
  volatile: 'var(--rose)',
  ranging: 'var(--amber)',
}

function fmtPct(v: number, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  return `${v > 0 ? '+' : ''}${v.toFixed(digits)}%`
}

function numCell(v: number, color?: string, bold = false): React.ReactNode {
  return (
    <td style={{ padding: '0.3rem 0.5rem', color: color || 'var(--text)', fontWeight: bold ? 600 : 400, textAlign: 'right' }}>
      {v ?? '—'}
    </td>
  )
}

export default function Compare() {
  const [dsls, setDsls] = useState<DslListItem[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [tickers, setTickers] = useState<Set<string>>(new Set(['BTC-USD', 'GC=F']))
  const [interval, setInterval] = useState('1h')
  const [period, setPeriod] = useState('1mo')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<HarnessResult | null>(null)
  const [runId, setRunId] = useState(0)

  useEffect(() => {
    fetchDslList()
      .then(list => {
        setDsls(list)
        // Pre-select a few real strategies
        const want = ['RSI-EMA-Simple1', 'Trend Pullback', 'BTC-USD Advisor']
        setSelected(new Set(list.filter(d => want.includes(d.name)).map(d => d.name)))
      })
      .catch(e => setError(e.message))
  }, [])

  const toggle = (set: Set<string>, v: string): Set<string> => {
    const next = new Set(set)
    if (next.has(v)) next.delete(v)
    else next.add(v)
    return next
  }

  const handleRun = async () => {
    if (selected.size === 0 || tickers.size === 0) {
      setError('Select at least one strategy and one ticker')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const payload = dsls
        .filter(d => selected.has(d.name))
        .map(d => ({
          name: d.name,
          description: d.description,
          timeframe: d.timeframe,
          indicators: d.indicators,
          compounds: d.compounds,
          patterns: d.patterns,
          signals: Object.fromEntries(Object.entries(d.signals).map(([k, v]) => [k, (v as any).condition ?? v])),
        }))
      const data = await fetchHarnessCompare(payload, Array.from(tickers), interval, period)
      setResult(data)
      setRunId(id => id + 1)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const s = result?.summary

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">🧪 Comparison Harness</div>
          <div className="page-subtitle">
            Test strategies against each other AND against doing nothing — buy & hold and random entries.
            A positive z-score means the strategy's entries beat pure noise.
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="card-header">1 · Pick Strategies</div>
        <div className="card-body">
          {dsls.length === 0 && <div className="loading">Loading strategies...</div>}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
            <button className="btn btn-sm" onClick={() => setSelected(new Set(dsls.map(d => d.name)))}>Select all</button>
            <button className="btn btn-sm" onClick={() => setSelected(new Set())}>Clear</button>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', alignSelf: 'center' }}>
              {selected.size}/{dsls.length} selected
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '0.35rem' }}>
            {dsls.map(d => (
              <label key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={selected.has(d.name)}
                  onChange={() => setSelected(toggle(selected, d.name))}
                />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.name}</span>
                {d.signals.entry && <span className="tag tag-cyan" style={{ marginLeft: 'auto' }}>entry</span>}
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">2 · Instruments & Window</div>
        <div className="card-body">
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
            {TICKER_GROUPS.map(g => (
              <div key={g.label}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.3rem' }}>{g.label}</div>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {g.tickers.map(t => (
                    <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', cursor: 'pointer' }}>
                      <input type="checkbox" checked={tickers.has(t)} onChange={() => setTickers(toggle(tickers, t))} />
                      {t}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'end', flexWrap: 'wrap' }}>
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
              <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
                {loading ? 'Running matrix...' : '🧪 Run Comparison'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Summary */}
      {s && (
        <div className="card">
          <div className="card-header">3 · Verdict</div>
          <div className="card-body">
            <div className="grid grid-4">
              <div className="stat-box" style={{ borderColor: s.edges > 0 ? 'var(--emerald)' : 'var(--border)' }}>
                <div className="value" style={{ color: s.edges > 0 ? 'var(--emerald)' : 'var(--text)' }}>{s.edges}</div>
                <div className="label">Cells with real edge (z≥1)</div>
              </div>
              <div className="stat-box">
                <div className="value" style={{ color: 'var(--amber)' }}>{s.weak_edges}</div>
                <div className="label">Weak edge (0.5≤z&lt;1)</div>
              </div>
              <div className="stat-box">
                <div className="value" style={{ color: 'var(--rose)' }}>{s.no_edges}</div>
                <div className="label">No edge (below noise)</div>
              </div>
              <div className="stat-box">
                <div className="value" style={{ color: 'var(--text-dim)' }}>{s.insufficient}</div>
                <div className="label">Too few trades to judge</div>
              </div>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
              {s.cells} cells · {s.strategies} strategies × {s.tickers} instruments · {s.errors > 0 && `${s.errors} errored`}
            </div>
          </div>
        </div>
      )}

      {/* Matrix table */}
      {result && result.rows.length > 0 && (
        <div className="card">
          <div className="card-header">4 · Comparison Matrix</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-dim)', fontWeight: 500 }}>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'left' }}>Strategy</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'left' }}>Ticker</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'left' }}>Regime</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>Trades</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>Return</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>Buy&Hold</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>vs Buy&Hold</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>Random (μ±σ)</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>vs Random</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>z-score</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'left' }}>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {result.rows.map((r, i) => {
                  if (r.error) {
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '0.3rem 0.5rem' }}>{r.strategy}</td>
                        <td style={{ padding: '0.3rem 0.5rem' }}>{r.ticker}</td>
                        <td colSpan={9} style={{ padding: '0.3rem 0.5rem', color: 'var(--rose)' }}>{r.error}</td>
                      </tr>
                    )
                  }
                  const retColor = r.total_return_pct >= 0 ? 'var(--emerald)' : 'var(--rose)'
                  const bhColor = r.edge_vs_buyhold_pct >= 0 ? 'var(--emerald)' : 'var(--rose)'
                  const randColor = r.edge_vs_random_pct >= 0 ? 'var(--emerald)' : 'var(--rose)'
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.3rem 0.5rem', fontWeight: 500 }}>{r.strategy}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{r.ticker}</td>
                      <td style={{ padding: '0.3rem 0.5rem', color: REGIME_COLOR[r.regime] || 'var(--text)' }}>{r.regime}</td>
                      {numCell(r.total_trades)}
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: retColor, fontWeight: 600 }}>{fmtPct(r.total_return_pct)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: 'var(--text-dim)' }}>{fmtPct(r.buy_hold_pct)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: bhColor }}>{fmtPct(r.edge_vs_buyhold_pct)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: 'var(--text-dim)' }}>
                        {fmtPct(r.random_mean_pct)}±{r.random_std_pct?.toFixed(2)}
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: randColor, fontWeight: 600 }}>{fmtPct(r.edge_vs_random_pct)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: TONE_COLOR[r.verdict_tone] || 'var(--text)', fontWeight: 600 }}>
                        {r.z_score ? r.z_score.toFixed(2) : '—'}
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>
                        <span className="tag" style={{
                          color: TONE_COLOR[r.verdict_tone] || 'var(--text-dim)',
                          borderColor: TONE_COLOR[r.verdict_tone] || 'var(--border)',
                        }}>
                          {r.verdict_label}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '0.5rem 1rem', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
            Random baseline: same trade count, held for the strategy's average hold time, shuffled 60× per cell.
            z = (strategy return − random mean) / random std. z ≥ 1.5 = strong edge, ≥ 1.0 = edge, 0.5–1 = weak, below = no better than noise.
            Trades &lt; 10 = not enough data to judge. Returns are gross of fees/slippage — subtract ~0.1–0.2%/trade for realistic edge.
          </div>
        </div>
      )}
    </div>
  )
}
