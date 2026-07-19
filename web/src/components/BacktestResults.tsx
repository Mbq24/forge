import { useMemo } from 'react'
import Plot from 'react-plotly.js'

interface BacktestProps {
  data: {
    total_trades: number
    winning_trades: number
    losing_trades: number
    win_rate: number
    total_return_pct: number
    avg_return_pct: number
    max_drawdown_pct: number
    profit_factor: number
    sharpe_ratio: number
    avg_bars_held: number
    trades: Array<{
      entry_date: string
      exit_date: string
      entry_price: number
      exit_price: number
      return_pct: number
      bars_held: number
    }>
    equity_curve: Array<{ date: string; equity: number }>
    error: string | null
  }
}

export default function BacktestResults({ data }: BacktestProps) {
  if (data.error) {
    return (
      <div className="card">
        <div className="card-header">Backtest Results</div>
        <div className="card-body">
          <div className="error" style={{ margin: 0 }}>{data.error}</div>
        </div>
      </div>
    )
  }

  if (data.total_trades === 0) {
    return (
      <div className="card">
        <div className="card-header">Backtest Results</div>
        <div className="card-body">
          <div className="loading" style={{ padding: '1rem' }}>No trades were generated. Try different signal conditions or more data.</div>
        </div>
      </div>
    )
  }

  const isProfitable = data.total_return_pct > 0

  // Equity curve chart
  const equityTrace = {
    x: data.equity_curve.map(p => p.date),
    y: data.equity_curve.map(p => p.equity),
    type: 'scatter' as const,
    mode: 'lines' as const,
    name: 'Equity',
    line: { color: isProfitable ? '#34d399' : '#fb7185', width: 1.5 },
    fill: 'tozeroy' as const,
    fillcolor: isProfitable ? 'rgba(52,211,153,0.05)' : 'rgba(251,113,133,0.05)',
  }

  return (
    <div>
      {/* Summary metrics */}
      <div className="card">
        <div className="card-header">Performance Summary</div>
        <div className="card-body">
          <div className="grid grid-4">
            <div className="stat-box" style={{ borderColor: isProfitable ? 'var(--emerald)' : 'var(--rose)' }}>
              <div className="value" style={{ color: isProfitable ? 'var(--emerald)' : 'var(--rose)' }}>
                {data.total_return_pct > 0 ? '+' : ''}{data.total_return_pct}%
              </div>
              <div className="label">Total Return</div>
            </div>
            <div className="stat-box emerald">
              <div className="value">{data.win_rate}%</div>
              <div className="label">Win Rate</div>
            </div>
            <div className="stat-box amber">
              <div className="value">{data.total_trades}</div>
              <div className="label">Total Trades</div>
            </div>
            <div className="stat-box rose">
              <div className="value">{data.max_drawdown_pct}%</div>
              <div className="label">Max Drawdown</div>
            </div>
          </div>
          <div className="grid grid-4" style={{ marginTop: '0.5rem' }}>
            <div className="stat-box cyan">
              <div className="value">{data.sharpe_ratio}</div>
              <div className="label">Sharpe</div>
            </div>
            <div className="stat-box"
              style={{ borderColor: data.profit_factor >= 1.5 ? 'var(--emerald)' : data.profit_factor >= 1 ? 'var(--amber)' : 'var(--rose)' }}>
              <div className="value" style={{
                color: data.profit_factor >= 1.5 ? 'var(--emerald)' : data.profit_factor >= 1 ? 'var(--amber)' : 'var(--rose)'
              }}>{data.profit_factor}</div>
              <div className="label">Profit Factor</div>
            </div>
            <div className="stat-box">
              <div className="value" style={{ color: 'var(--text)' }}>{data.avg_return_pct}%</div>
              <div className="label">Avg Return / Trade</div>
            </div>
            <div className="stat-box">
              <div className="value" style={{ color: 'var(--text)' }}>{data.winning_trades}/{data.losing_trades}</div>
              <div className="label">W / L</div>
            </div>
          </div>
        </div>
      </div>

      {/* Equity curve */}
      <div className="card">
        <div className="card-header">Equity Curve</div>
        <div className="card-body" style={{ padding: '0.5rem' }}>
          {/* @ts-ignore */}
          <Plot
            data={[equityTrace] as any}
            layout={{
              paper_bgcolor: '#0f172a',
              plot_bgcolor: '#0f172a',
              font: { color: '#94a3b8', size: 10, family: 'Segoe UI, system-ui, sans-serif' },
              margin: { t: 10, r: 10, b: 30, l: 50 },
              xaxis: { gridcolor: '#1e293b', showgrid: true },
              yaxis: { gridcolor: '#1e293b', showgrid: true },
              hovermode: 'x unified',
              showlegend: false,
            } as any}
            config={{ responsive: true, displayModeBar: false } as any}
            style={{ width: '100%', height: '300px' }}
            useResizeHandler={true}
          />
        </div>
      </div>

      {/* Trade list */}
      {data.trades.length > 0 && (
        <div className="card">
          <div className="card-header">Trade Log ({data.trades.length} trades)</div>
          <div style={{ overflowX: 'auto', maxHeight: '300px', overflowY: 'auto' }}>
            <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, background: 'var(--bg-card)' }}>
                  {['#', 'Entry', 'Exit', 'Entry Price', 'Exit Price', 'Return', 'Bars'].map(h => (
                    <th key={h} style={{ padding: '0.4rem 0.5rem', textAlign: 'left', color: 'var(--text-dim)', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.trades.map((t, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.3rem 0.5rem', color: 'var(--text-dim)' }}>{i + 1}</td>
                    <td style={{ padding: '0.3rem 0.5rem' }}>{t.entry_date.slice(5, 19)}</td>
                    <td style={{ padding: '0.3rem 0.5rem' }}>{t.exit_date.slice(5, 19)}</td>
                    <td style={{ padding: '0.3rem 0.5rem' }}>${t.entry_price}</td>
                    <td style={{ padding: '0.3rem 0.5rem' }}>${t.exit_price}</td>
                    <td style={{
                      padding: '0.3rem 0.5rem',
                      color: t.return_pct > 0 ? 'var(--emerald)' : 'var(--rose)',
                      fontWeight: 500,
                    }}>
                      {t.return_pct > 0 ? '+' : ''}{t.return_pct}%
                    </td>
                    <td style={{ padding: '0.3rem 0.5rem', color: 'var(--text-dim)' }}>{t.bars_held}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
