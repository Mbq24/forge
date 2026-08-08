import { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import { fetchPortfolioState, PortfolioState } from '../api'

const fmt = (v: number, digits = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? '—' : v.toFixed(digits)

function ageStr(iso: string): string {
  const then = new Date(iso).getTime()
  const mins = Math.round((Date.now() - then) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Portfolio() {
  const [state, setState] = useState<PortfolioState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<number>(Date.now())

  const load = () => {
    setLoading(true)
    fetchPortfolioState()
      .then(s => { setState(s); setError('') })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    const iv = setInterval(() => setLastUpdated(Date.now()), 30000)
    return () => clearInterval(iv)
  }, [])

  if (loading && !state) return <div className="loading">Loading portfolio state...</div>

  const p = state?.portfolio
  const cfg = state?.config
  const stale = state ? (Date.now() - new Date(state.updated_at).getTime()) > 3 * 3600_000 : false

  // Equity curve
  const eq = state?.equity_curve ?? []
  const equityTrace = eq.length > 1 ? {
    x: eq.map(r => r.time),
    y: eq.map(r => parseFloat(r.equity)),
    type: 'scatter' as const,
    mode: 'lines' as const,
    name: 'Equity',
    line: { color: (p && p.equity >= p.cash) ? '#34d399' : '#fb7185', width: 1.5 },
    fill: 'tozeroy' as const,
    fillcolor: 'rgba(52,211,153,0.05)',
  } : null

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">🎛 Portfolio Control Room</div>
          <div className="page-subtitle">
            What portfolio-manager is actually running, and every trade it has made.
            {state && (
              <span style={{ marginLeft: '0.5rem', color: stale ? 'var(--rose)' : 'var(--text-dim)' }}>
                · last push {ageStr(state.updated_at)}{stale && ' ⚠️ STALE — is the cron running?'}
              </span>
            )}
          </div>
        </div>
        <button className="btn btn-sm" onClick={load} disabled={loading}>
          {loading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      {error && !state && <div className="error">{error}</div>}
      {error && state && <div className="error" style={{ marginBottom: '0.75rem' }}>{error} (showing last known)</div>}

      {state && p && cfg && (
        <>
          {/* Active configuration — WHAT is being executed */}
          <div className="card">
            <div className="card-header">Active Strategy</div>
            <div className="card-body">
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="tag tag-violet" style={{ fontSize: '0.85rem', padding: '0.3rem 0.7rem' }}>
                  {state.strategy_name || cfg.strategy}
                </span>
                <span className="tag tag-cyan">{cfg.ticker}</span>
                <span className="tag tag-amber">{cfg.interval} · {cfg.period}</span>
                <span className="tag" style={{
                  color: cfg.mode === 'paper' ? 'var(--amber)' : 'var(--emerald)',
                  borderColor: cfg.mode === 'paper' ? 'var(--amber)' : 'var(--emerald)',
                }}>
                  {cfg.mode.toUpperCase()}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{state.source || '—'}</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', lineHeight: 1.6 }}>
                <div>To change what runs, edit <code style={{ color: 'var(--text)' }}>~/DBot/portfolio-manager/config.json</code> on the machine running portfolio-manager:</div>
                <pre style={{
                  background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6,
                  padding: '0.6rem 0.8rem', fontSize: '0.72rem', marginTop: '0.4rem', overflowX: 'auto',
                }}>
{`{
  "strategy": "${cfg.strategy}",      ← Forge strategy YAML (examples/ filename or path)
  "ticker": "${cfg.ticker}",          ← instrument — must match the traded asset
  "interval": "${cfg.interval}",      ← timeframe
  "period": "${cfg.period}",          ← lookback
  "asset": "${cfg.asset}",            ← symbol traded via broker
  "mode": "${cfg.mode}"               ← "paper" (internal executor) or "live" (broker)
}`}
                </pre>
              </div>
            </div>
          </div>

          {/* Account summary */}
          <div className="grid grid-4">
            <div className="stat-box" style={{ borderColor: p.equity >= 10000 ? 'var(--emerald)' : 'var(--rose)' }}>
              <div className="value" style={{ color: p.equity >= 10000 ? 'var(--emerald)' : 'var(--rose)' }}>${fmt(p.equity)}</div>
              <div className="label">Total Equity</div>
            </div>
            <div className="stat-box">
              <div className="value" style={{ color: 'var(--text)' }}>${fmt(p.cash)}</div>
              <div className="label">Cash</div>
            </div>
            <div className="stat-box">
              <div className="value" style={{ color: 'var(--amber)' }}>{p.total_trades}</div>
              <div className="label">Total Trades</div>
            </div>
            <div className="stat-box">
              <div className="value" style={{ color: p.win_rate >= 0.5 ? 'var(--emerald)' : 'var(--rose)' }}>{(p.win_rate * 100).toFixed(1)}%</div>
              <div className="label">Win Rate ({p.wins}W/{p.losses}L)</div>
            </div>
          </div>

          {/* Open positions */}
          {p.positions.length > 0 && (
            <div className="card">
              <div className="card-header">Open Positions</div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-dim)' }}>
                      {['Asset', 'Side', 'Size', 'Entry', 'Current', 'Unrealized P&L'].map(h =>
                        <th key={h} style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {p.positions.map((pos, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '0.3rem 0.6rem', fontWeight: 500 }}>{pos.asset}</td>
                        <td style={{ padding: '0.3rem 0.6rem', color: pos.side === 'long' ? 'var(--emerald)' : 'var(--rose)' }}>{pos.side}</td>
                        <td style={{ padding: '0.3rem 0.6rem' }}>{fmt(pos.size, 4)}</td>
                        <td style={{ padding: '0.3rem 0.6rem' }}>${fmt(pos.entry_price)}</td>
                        <td style={{ padding: '0.3rem 0.6rem' }}>${fmt(pos.current_price)}</td>
                        <td style={{ padding: '0.3rem 0.6rem', color: pos.unrealized_pnl >= 0 ? 'var(--emerald)' : 'var(--rose)' }}>
                          {pos.unrealized_pnl >= 0 ? '+' : ''}${fmt(pos.unrealized_pnl)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Equity curve */}
          {equityTrace && (
            <div className="card">
              <div className="card-header">Equity Curve ({eq.length} points)</div>
              <div className="card-body" style={{ padding: '0.5rem' }}>
                {/* @ts-ignore */}
                <Plot
                  data={[equityTrace] as any}
                  layout={{
                    paper_bgcolor: '#0f172a', plot_bgcolor: '#0f172a',
                    font: { color: '#94a3b8', size: 10 },
                    margin: { t: 10, r: 10, b: 30, l: 50 },
                    xaxis: { gridcolor: '#1e293b' }, yaxis: { gridcolor: '#1e293b' },
                    hovermode: 'x unified', showlegend: false,
                  } as any}
                  config={{ responsive: true, displayModeBar: false } as any}
                  style={{ width: '100%', height: '240px' }}
                  useResizeHandler={true}
                />
              </div>
            </div>
          )}

          {/* Trade journal */}
          <div className="card">
            <div className="card-header">Trade Journal ({state.trades.length} most recent, append-only)</div>
            <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-dim)', position: 'sticky', top: 0, background: 'var(--bg-card)' }}>
                    {['Time', 'Type', 'Asset', 'Side', 'Size', 'Price', 'P&L', 'Strategy', 'Ticker', 'Interval', 'Mode'].map(h =>
                      <th key={h} style={{ padding: '0.4rem 0.5rem', textAlign: 'left' }}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {state.trades.map((t, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.3rem 0.5rem', color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
                        {t.time?.slice(5, 19).replace('T', ' ')}
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>
                        <span className="tag" style={{
                          color: t.type === 'enter' ? 'var(--emerald)' : 'var(--rose)',
                          borderColor: t.type === 'enter' ? 'var(--emerald)' : 'var(--rose)',
                        }}>{t.type === 'enter' ? '▲ ENTER' : '▼ EXIT'}</span>
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem', fontWeight: 500 }}>{t.asset}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{t.side}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right' }}>{fmt(parseFloat(t.size), 4)}</td>
                      <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right' }}>${fmt(parseFloat(t.price || t.exit_price || '0'))}</td>
                      <td style={{
                        padding: '0.3rem 0.5rem', textAlign: 'right', fontWeight: 600,
                        color: parseFloat(t.pnl || '0') >= 0 ? 'var(--emerald)' : 'var(--rose)',
                      }}>
                        {t.pnl ? `${parseFloat(t.pnl) >= 0 ? '+' : ''}$${fmt(parseFloat(t.pnl))}` : '—'}
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{t.strategy || '—'}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{t.ticker || '—'}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{t.interval || '—'}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{t.mode || '—'}</td>
                    </tr>
                  ))}
                  {state.trades.length === 0 && (
                    <tr><td colSpan={11} style={{ padding: '1rem', color: 'var(--text-dim)', textAlign: 'center' }}>
                      No trades yet — strategy is running, waiting for a signal.
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
