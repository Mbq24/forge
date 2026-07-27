import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { fetchDslDetail, DslDetail as DslDetailType } from '../api'
import Chart from '../components/Chart'
import BacktestResults from '../components/BacktestResults'
import PineScriptDisplay from '../components/PineScriptDisplay'

const TICKER_GROUPS: Record<string, string[]> = {
  synthetic: ['SYNTHETIC'],
  crypto: ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD'],
  forex: ['EURUSD=X', 'GBPUSD=X', 'XAUUSD=X'],
  stocks: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'SPY', 'SPX', 'SPCX'],
}

const INTERVALS = ['15m', '30m', '1h', '4h', '1d']
const PERIODS = ['5d', '7d', '1mo', '3mo', '6mo']

export default function DslDetail() {
  const { name } = useParams<{ name: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData] = useState<DslDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [tab, setTab] = useState<'chart' | 'backtest'>('chart')

  const ticker = searchParams.get('ticker') || 'SYNTHETIC'
  const interval = searchParams.get('interval') || '1h'
  const period = searchParams.get('period') || '5d'

  const load = () => {
    setLoading(true)
    setError('')
    const params: any = { ticker, interval, period }
    if (tab === 'backtest') params.backtest = 'true'
    fetchDslDetail(name!, params)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [name, ticker, interval, period, tab])

  const updateParam = (key: string, val: string) => {
    const next = new URLSearchParams(searchParams)
    next.set(key, val)
    setSearchParams(next)
  }

  const copyPine = () => {
    if (!data) return
    navigator.clipboard.writeText(data.pine_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/dsl" style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>← Back to DSLs</Link>
          <div className="page-title" style={{ marginTop: 4 }}>{name}</div>
        </div>
        <div>
          <Link to={`/dsl/new?edit=${encodeURIComponent(name || '')}`} className="btn btn-primary" style={{ textDecoration: 'none' }}>✏️ Edit</Link>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="card-header">Data Source</div>
        <div className="card-body">
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'end', flexWrap: 'wrap' }}>
            <div>
              <label className="form-label">Ticker</label>
              <select className="form-select" value={ticker} onChange={e => updateParam('ticker', e.target.value)} style={{ minWidth: 140 }}>
                {Object.entries(TICKER_GROUPS).map(([group, syms]) => (
                  <optgroup label={group.charAt(0).toUpperCase() + group.slice(1)} key={group}>
                    {syms.map(s => <option value={s} key={s}>{s}</option>)}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">Interval</label>
              <select className="form-select" value={interval} onChange={e => updateParam('interval', e.target.value)}>
                {INTERVALS.map(iv => <option value={iv} key={iv}>{iv}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Period</label>
              <select className="form-select" value={period} onChange={e => updateParam('period', e.target.value)}>
                {PERIODS.map(p => <option value={p} key={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <button className="btn btn-primary" onClick={load}>Compute</button>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Computing indicators...</div>}

      {/* Tab toggle */}
      {data && !loading && (
        <div style={{ display: 'flex', gap: 4, marginBottom: '1rem' }}>
          <button
            className={`btn btn-sm ${tab === 'chart' ? 'btn-primary' : ''}`}
            onClick={() => setTab('chart')}
            style={{ fontSize: '0.75rem' }}
          >
            📊 Chart & Signals
          </button>
          <button
            className={`btn btn-sm ${tab === 'backtest' ? 'btn-primary' : ''}`}
            onClick={() => setTab('backtest')}
            style={{ fontSize: '0.75rem' }}
          >
            📈 Backtest
          </button>
        </div>
      )}

      {data && !loading && tab === 'chart' && (
        <div className="grid grid-2" style={{ gridTemplateColumns: '1.5fr 1fr' }}>
          {/* Left column: Chart + Stats */}
          <div>
            <div className="card">
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Computed Indicators — {ticker} ({interval})</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{data.date_range}</span>
              </div>
              <div className="card-body" style={{ padding: '0.5rem' }}>
                {data.chart_data ? (
                  <Chart data={data.chart_data} />
                ) : (
                  <div className="loading">No chart data available</div>
                )}
              </div>
            </div>

            {/* Signal Stats */}
            <div className="card">
              <div className="card-header">Signal Analysis</div>
              <div className="card-body">
                <div className="grid grid-4">
                  <div className="stat-box emerald">
                    <div className="value">{data.stats.entry_count}</div>
                    <div className="label">Entries</div>
                  </div>
                  <div className="stat-box rose">
                    <div className="value">{data.stats.exit_count}</div>
                    <div className="label">Exits</div>
                  </div>
                  <div className="stat-box amber">
                    <div className="value">{data.stats.total_bars}</div>
                    <div className="label">Total Bars</div>
                  </div>
                  <div className="stat-box cyan">
                    <div className="value">{data.stats.signal_density}%</div>
                    <div className="label">Density</div>
                  </div>
                </div>
                <div style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
                  <strong>Entry:</strong>{' '}
                  <code style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>{data.entry_cond}</code>
                  <br />
                  <strong>Exit:</strong>{' '}
                  <code style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>{data.exit_cond}</code>
                </div>
              </div>
            </div>
          </div>

          {/* Right column: YAML + Pine */}
          <div>
            <div className="card">
              <div className="card-header">DSL Definition (YAML)</div>
              <div style={{ padding: 0 }}>
                <pre className="code-block" style={{ borderRadius: 0, border: 'none' }}>{data.yaml_content}</pre>
              </div>
            </div>

            <div className="card">
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Generated Pine Script v5</span>
                <button className="btn btn-sm" onClick={copyPine}>
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <div style={{ padding: 0 }}>
                <PineScriptDisplay code={data.pine_code} />
              </div>
            </div>
          </div>
        </div>
      )}

      {data && !loading && tab === 'backtest' && data.backtest && (
        <BacktestResults data={data.backtest} />
      )}
    </div>
  )
}
