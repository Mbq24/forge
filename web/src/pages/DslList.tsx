import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchDslList, DslListItem } from '../api'

export default function DslList() {
  const [dsls, setDsls] = useState<DslListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDslList()
      .then(setDsls)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading DSL definitions...</div>
  if (error) return <div className="error">{error}</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Indicator DSL</div>
          <div className="page-subtitle">{dsls.length} definitions available</div>
        </div>
        <a href="/dsl/new" className="btn btn-primary" style={{ textDecoration: 'none' }} onClick={e => { e.preventDefault(); window.location.href = '/dsl/new' }}>+ New Indicator</a>
      </div>

      <div className="grid grid-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))' }}>
        {dsls.map(dsl => (
          <div className="card" key={dsl.name}>
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{dsl.name}</span>
              <span>
                <span className="tag tag-cyan">{dsl.indicators.length} indicators</span>
                <span className="tag tag-emerald">{dsl.compounds.length} compounds</span>
              </span>
            </div>
            <div className="card-body">
              <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>
                {dsl.description.slice(0, 150)}
              </p>
              <div style={{ marginBottom: '0.5rem' }}>
                {dsl.patterns.map(p => (
                  <span className="tag tag-violet" key={p}>{p}</span>
                ))}
                <span className="tag tag-amber">{dsl.timeframe}</span>
              </div>
              {dsl.signals.entry && (
                <div style={{ fontSize: '0.75rem' }}>
                  <span className="signal-entry">▲ entry:</span>{' '}
                  <code style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                    {dsl.signals.entry.condition}
                  </code>
                  <br />
                </div>
              )}
              {dsl.signals.exit && (
                <div style={{ fontSize: '0.75rem' }}>
                  <span className="signal-exit">▼ exit:</span>{' '}
                  <code style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                    {dsl.signals.exit.condition}
                  </code>
                </div>
              )}
            </div>
            <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--border)' }}>
              <Link to={`/dsl/${dsl.name}`} className="btn btn-primary" style={{ textDecoration: 'none', display: 'block', textAlign: 'center' }}>
                Open & Test
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
