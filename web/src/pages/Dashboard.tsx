import { useEffect, useState } from 'react'
import { fetchDbStats, fetchDbTable, DbStats } from '../api'

export default function Dashboard() {
  const [stats, setStats] = useState<DbStats | null>(null)
  const [signals, setSignals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetchDbStats().catch(() => ({ signals: 0, rsi: 0, stochastic: 0, lines: 0 }) as DbStats),
      fetchDbTable('signals').catch(() => []),
    ])
      .then(([s, sigs]) => {
        setStats(s)
        setSignals(sigs)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading dashboard...</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Dashboard</div>
          <div className="page-subtitle">Webhook data overview</div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {stats && (
        <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
          <div className="stat-box cyan">
            <div className="value">{stats.signals}</div>
            <div className="label">Signals</div>
          </div>
          <div className="stat-box emerald">
            <div className="value">{stats.rsi}</div>
            <div className="label">RSI Records</div>
          </div>
          <div className="stat-box amber">
            <div className="value">{stats.stochastic}</div>
            <div className="label">Stochastic Records</div>
          </div>
          <div className="stat-box rose">
            <div className="value">{stats.lines}</div>
            <div className="label">Trend Lines</div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">Signals (Price Data from Webhooks)</div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Time', 'Ticker', 'Action', 'Price', 'Open', 'High', 'Low', 'Close', 'Volume'].map(h => (
                  <th key={h} style={{ padding: '0.5rem', textAlign: 'left', color: 'var(--text-dim)', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {signals.slice(-30).reverse().map((s, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.timestamp}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.ticker}</td>
                  <td style={{ padding: '0.4rem 0.5rem', color: s.order_action === 'buy' ? 'var(--emerald)' : 'var(--rose)' }}>{s.order_action}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.order_price}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.open}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.high}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.low}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.close}</td>
                  <td style={{ padding: '0.4rem 0.5rem' }}>{s.volume}</td>
                </tr>
              ))}
              {signals.length === 0 && (
                <tr><td colSpan={9} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)' }}>No signal data yet — webhooks will populate this</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
