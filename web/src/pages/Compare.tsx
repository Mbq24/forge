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
const PERIODS = ['5d', '7d', '1mo', '3mo', '6mo', '1y']
// Fees + slippage per side, in bps of notional. A long pays it twice.
// 10 bps/side ≈ 0.2% round trip (typical crypto market-order cost).
const COST_LEVELS: { value: number; label: string }[] = [
  { value: 0, label: '0 bps — gross (no costs)' },
  { value: 5, label: '5 bps/side — 0.1% round trip (maker/low-fee)' },
  { value: 10, label: '10 bps/side — 0.2% round trip (typical)' },
  { value: 25, label: '25 bps/side — 0.5% round trip (retail fees)' },
  { value: 50, label: '50 bps/side — 1.0% round trip (worst case)' },
]

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
  const [costBps, setCostBps] = useState(10)
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
      const data = await fetchHarnessCompare(payload, Array.from(tickers), interval, period, 60, costBps)
      setResult(data)
      setRunId(id => id + 1)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const s = result?.summary
  // When a cost level is set, judge the verdict counts net of costs.
  const netView = costBps > 0
  const nEdges = netView ? (s?.edges_net ?? s?.edges ?? 0) : (s?.edges ?? 0)
  const nWeak = netView ? (s?.weak_edges_net ?? s?.weak_edges ?? 0) : (s?.weak_edges ?? 0)
  const nNone = netView ? (s?.no_edges_net ?? s?.no_edges ?? 0) : (s?.no_edges ?? 0)
  const nInsuf = netView ? (s?.insufficient_net ?? s?.insufficient ?? 0) : (s?.insufficient ?? 0)

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">🧪 Comparison Harness</div>
          <div className="page-subtitle">
            Test strategies against each other AND against doing nothing — buy & hold and random entries — with
            trading costs applied, so you can see which edges survive real fees and slippage.
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
              <label className="form-label">Trading cost (fees + slippage, per side)</label>
              <select className="form-select" value={costBps} onChange={e => setCostBps(Number(e.target.value))}>
                {COST_LEVELS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
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
              <div className="stat-box" style={{ borderColor: nEdges > 0 ? 'var(--emerald)' : 'var(--border)' }}>
                <div className="value" style={{ color: nEdges > 0 ? 'var(--emerald)' : 'var(--text)' }}>{nEdges}</div>
                <div className="label">Cells with real edge{netView ? ' after costs' : ''} (z≥1)</div>
              </div>
              <div className="stat-box">
                <div className="value" style={{ color: 'var(--amber)' }}>{nWeak}</div>
                <div className="label">Weak edge (0.5≤z&lt;1)</div>
              </div>
              <div className="stat-box">
                <div className="value" style={{ color: 'var(--rose)' }}>{nNone}</div>
                <div className="label">No edge (below noise)</div>
              </div>
              <div className="stat-box">
                <div className="value" style={{ color: 'var(--text-dim)' }}>{nInsuf}</div>
                <div className="label">Too few trades to judge</div>
              </div>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
              {s.cells} cells · {s.strategies} strategies × {s.tickers} instruments · {s.errors > 0 && `${s.errors} errored`}
              {netView && (
                <> · <strong style={{ color: s.profitable_net ? 'var(--emerald)' : 'var(--rose)' }}>
                  {s.profitable_net ?? 0}/{s.cells} cells profitable after {costBps} bps/side</strong></>
              )}
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
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>Gross</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>Net</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>BE bps</th>
                  <th style={{ padding: '0.4rem 0.5rem', textAlign: 'right' }}>vs Buy&Hold</th>
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
                        <td colSpan={8} style={{ padding: '0.3rem 0.5rem', color: 'var(--rose)' }}>{r.error}</td>
                      </tr>
                    )
                  }
                  const netRet = r.total_return_pct_net ?? r.total_return_pct
                  const vsBh = r.edge_vs_buyhold_net_pct ?? r.edge_vs_buyhold_pct
                  const z = r.z_score_net ?? r.z_score
                  const tone = (netView ? r.verdict_tone_net : r.verdict_tone) ?? r.verdict_tone
                  const label = (netView ? r.verdict_label_net : r.verdict_label) ?? r.verdict_label
                  const be = r.breakeven_bps_per_side
                  const netColor = netRet >= 0 ? 'var(--emerald)' : 'var(--rose)'
                  const bhColor = vsBh >= 0 ? 'var(--emerald)' : 'var(--rose)'
                  const beColor = be == null ? 'var(--text-dim)' : (be >= costBps ? 'var(--emerald)' : 'var(--rose)')
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.3rem 0.5rem', fontWeight: 500 }}>{r.strategy}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{r.ticker}</td>
                      <td style={{ padding: '0.3rem 0.5rem', color: REGIME_COLOR[r.regime] || 'var(--text)' }}>{r.regime}</td>
                      {numCell(r.total_trades)}
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: 'var(--text-dim)' }}>{fmtPct(r.total_return_pct)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: netColor, fontWeight: 600 }}>{fmtPct(netRet)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: beColor }}>{be == null ? '—' : be.toFixed(1)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: bhColor }}>{fmtPct(vsBh)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', color: TONE_COLOR[tone] || 'var(--text)', fontWeight: 600 }}>
                        {z ? z.toFixed(2) : '—'}
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>
                        <span className="tag" style={{
                          color: TONE_COLOR[tone] || 'var(--text-dim)',
                          borderColor: TONE_COLOR[tone] || 'var(--border)',
                        }}>
                          {label}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '0.5rem 1rem', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
            <strong>Costs:</strong> fees + slippage are charged on BOTH fills of every trade
            (net per trade = exit·(1−c) / entry·(1+c) − 1, c = bps/side). The random baseline pays the same cost.
            <strong> BE bps</strong> = the per-side cost at which the gross edge is exactly consumed —
            green means it still clears your selected cost, red means costs eat it.
            <br />
            Random baseline: same trade count, held for the strategy's average hold time, shuffled 60× per cell.
            z = (strategy total return − random total return) / random std — both sides are sums, so magnitudes are honest
            (values were ~n_trades× inflated before Sep 2026). z ≥ 1.5 = strong edge, ≥ 1.0 = edge, 0.5–1 = weak, below = noise.
            Trades &lt; 10 = not enough data to judge. Long windows plus costs are the honest test.
          </div>
        </div>
      )}
    </div>
  )
}
