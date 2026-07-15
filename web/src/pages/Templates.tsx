import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchDslList, DslListItem } from '../api'

// Template metadata with regime tags and descriptions
const TEMPLATE_INFO: Record<string, { regime: string; concepts: string[]; difficulty: string }> = {
  "VT-Breakout": {
    regime: "Trending",
    concepts: ["EMA Family", "Candle Patterns"],
    difficulty: "Beginner",
  },
  "RSI-EMA-Simple1": {
    regime: "Ranging",
    concepts: ["RSI", "EMA Trend Filter"],
    difficulty: "Beginner",
  },
  "Volatility Squeeze": {
    regime: "Volatile",
    concepts: ["Bollinger Bands", "EMA Spread"],
    difficulty: "Intermediate",
  },
  "Trend Pullback": {
    regime: "Trending",
    concepts: ["Pull Count", "Candle Proximity"],
    difficulty: "Intermediate",
  },
  "MACD Trend Rider": {
    regime: "Trending",
    concepts: ["MACD", "EMA Trend Filter"],
    difficulty: "Intermediate",
  },
  "Session Breakout": {
    regime: "Any",
    concepts: ["Session Encoding", "Volume"],
    difficulty: "Advanced",
  },
  "Gold Hours": {
    regime: "Any",
    concepts: ["Session Encoding", "EMA Alignment"],
    difficulty: "Advanced",
  },
  "BB Squeeze Combo": {
    regime: "Ranging",
    concepts: ["Bollinger Bands", "RSI", "Mean Reversion"],
    difficulty: "Intermediate",
  },
}

const REGIME_COLORS: Record<string, string> = {
  Trending: 'var(--emerald)',
  Ranging: 'var(--amber)',
  Volatile: 'var(--rose)',
  Any: 'var(--violet)',
}

export default function Templates() {
  const [dsls, setDsls] = useState<DslListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchDslList()
      .then(setDsls)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Determine available regime filters
  const regimes = [...new Set(Object.values(TEMPLATE_INFO).map(t => t.regime))].sort()

  const filtered = filter
    ? dsls.filter(d => TEMPLATE_INFO[d.name]?.regime === filter)
    : dsls

  const handleLoad = (name: string) => {
    navigate(`/dsl/${encodeURIComponent(name)}?ticker=SYNTHETIC&interval=1h&period=5d`)
  }

  if (loading) return <div className="loading">Loading templates...</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Strategy Templates</div>
          <div className="page-subtitle">{dsls.length} pre-built strategies — load and test instantly</div>
        </div>
      </div>

      {/* Regime filter tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button
          className={`btn btn-sm ${!filter ? 'btn-primary' : ''}`}
          onClick={() => setFilter(null)}
          style={{ fontSize: '0.75rem' }}
        >
          All
        </button>
        {regimes.map(r => (
          <button
            key={r}
            className={`btn btn-sm ${filter === r ? 'btn-primary' : ''}`}
            onClick={() => setFilter(r)}
            style={{ fontSize: '0.75rem', borderColor: REGIME_COLORS[r], color: filter === r ? '#000' : REGIME_COLORS[r] }}
          >
            {r}
          </button>
        ))}
      </div>

      {/* Template grid */}
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '1rem' }}>
        {filtered.map(dsl => {
          const meta = TEMPLATE_INFO[dsl.name] || { regime: 'N/A', concepts: [], difficulty: 'N/A' }
          const regimeColor = REGIME_COLORS[meta.regime] || 'var(--text-dim)'

          return (
            <div className="card" key={dsl.name} style={{ display: 'flex', flexDirection: 'column' }}>
              {/* Header with regime badge */}
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600 }}>{dsl.name}</span>
                <span className="tag" style={{
                  background: `${regimeColor}15`,
                  color: regimeColor,
                  border: `1px solid ${regimeColor}40`,
                }}>
                  {meta.regime}
                </span>
              </div>

              <div className="card-body" style={{ flex: 1 }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
                  {dsl.description || 'No description'}
                </p>

                {/* Concepts */}
                {meta.concepts.length > 0 && (
                  <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>Concepts</div>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {meta.concepts.map(c => (
                        <span key={c} className="tag tag-cyan">{c}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Indicators used */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Indicators ({dsl.indicators.length})
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {dsl.indicators.map((i: any) => (
                      <span key={i.id} className="tag tag-amber">{i.id}</span>
                    ))}
                    {dsl.compounds.map((c: any) => (
                      <span key={c.id} className="tag tag-emerald">{c.id}</span>
                    ))}
                  </div>
                </div>

                {/* Entry / Exit */}
                {dsl.signals && (
                  <div style={{ fontSize: '0.75rem' }}>
                    {dsl.signals.entry && (
                      <div style={{ marginBottom: 2 }}>
                        <span className="signal-entry">▲ entry:</span>{' '}
                        <code style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                          {dsl.signals.entry.condition}
                        </code>
                      </div>
                    )}
                    {dsl.signals.exit && (
                      <div>
                        <span className="signal-exit">▼ exit:</span>{' '}
                        <code style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                          {dsl.signals.exit.condition}
                        </code>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--border)', display: 'flex', gap: 6 }}>
                <button className="btn btn-primary btn-sm" onClick={() => handleLoad(dsl.name)} style={{ flex: 1 }}>
                  🧪 Load & Test
                </button>
                <button className="btn btn-sm" onClick={() => navigate(`/dsl/new?edit=${encodeURIComponent(dsl.name)}`)}>
                  ✏️ Edit
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {filtered.length === 0 && (
        <div className="loading">No templates for this filter</div>
      )}
    </div>
  )
}
