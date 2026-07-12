import { useEffect, useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  fetchIndicatorTypes, fetchDslEdit, createDsl, updateDsl,
  IndicatorType
} from '../api'
import Chart from '../components/Chart'

interface IndicatorEntry {
  id: string
  type: string
  params: Record<string, any>
}

interface CompoundEntry {
  id: string
  type: string
  params: Record<string, any>
}

export default function DslNew() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editName = searchParams.get('edit')
  const isEditing = !!editName

  // Load available types
  const [allIndicators, setAllIndicators] = useState<IndicatorType[]>([])
  const [allPatterns, setAllPatterns] = useState<string[]>([])
  const [loadingTypes, setLoadingTypes] = useState(true)

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [timeframe, setTimeframe] = useState('1h')
  const [indicators, setIndicators] = useState<IndicatorEntry[]>([])
  const [compounds, setCompounds] = useState<CompoundEntry[]>([])
  const [patterns, setPatterns] = useState<string[]>([])
  const [entryCond, setEntryCond] = useState('')
  const [exitCond, setExitCond] = useState('')

  // Adding indicators
  const [addType, setAddType] = useState('ema')
  const [addId, setAddId] = useState('')
  const [addParams, setAddParams] = useState<Record<string, any>>({})
  const [addCompoundType, setAddCompoundType] = useState('ema_alignment')
  const [addCompoundId, setAddCompoundId] = useState('')

  // Preview
  const [testResult, setTestResult] = useState<any>(null)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    fetchIndicatorTypes()
      .then(d => { setAllIndicators(d.indicators); setAllPatterns(d.patterns) })
      .catch(e => setError(e.message))
      .finally(() => setLoadingTypes(false))
  }, [])
  
  // Load existing DSL for editing
  useEffect(() => {
    if (editName) {
      setLoadingTypes(true)
      fetchDslEdit(editName)
        .then(data => {
          setName(data.name)
          setDescription(data.description)
          setTimeframe(data.timeframe)
          setIndicators(data.indicators.map(i => ({ id: i.id, type: i.type, params: i.params || {} })))
          setCompounds(data.compounds.map(c => ({ id: c.id, type: c.type, params: c.params || {} })))
          setPatterns(data.patterns)
          if (data.signals) {
            setEntryCond(data.signals.entry || '')
            setExitCond(data.signals.exit || '')
          }
        })
        .catch(e => setError(e.message))
        .finally(() => setLoadingTypes(false))
    }
  }, [editName])

  // Build YAML preview
  const yamlPreview = useMemo(() => {
    const lines: string[] = []
    lines.push(`name: "${name || 'my-indicator'}"`)
    if (description) lines.push(`description: "${description}"`)
    lines.push(`timeframe: "${timeframe}"`)
    if (indicators.length > 0) {
      lines.push('indicators:')
      for (const ind of indicators) {
        const paramsStr = Object.keys(ind.params).length > 0
          ? `  params: { ${Object.entries(ind.params).map(([k, v]) => `${k}: ${v}`).join(', ')} }`
          : ''
        lines.push(`  - id: ${ind.id}    type: ${ind.type}    ${paramsStr}`)
      }
    }
    if (compounds.length > 0) {
      lines.push('compounds:')
      for (const c of compounds) {
        const paramsStr = Object.keys(c.params).length > 0
          ? `  params: { ${Object.entries(c.params).map(([k, v]) => `${k}: ${v}`).join(', ')} }`
          : ''
        lines.push(`  - id: ${c.id}    type: ${c.type}    ${paramsStr}`)
      }
    }
    if (patterns.length > 0) lines.push(`patterns: [${patterns.join(', ')}]`)
    if (entryCond || exitCond) {
      lines.push('signals:')
      if (entryCond) lines.push(`  entry: "${entryCond}"`)
      if (exitCond) lines.push(`  exit: "${exitCond}"`)
    }
    return lines.join('\n')
  }, [name, description, timeframe, indicators, compounds, patterns, entryCond, exitCond])

  // Selected indicator info
  const selectedType = allIndicators.find(i => i.type === addType)
  const selectedCompound = allIndicators.find(i => i.type === addCompoundType)

  const addIndicator = () => {
    if (!addId.trim()) return
    setIndicators(prev => [...prev, { id: addId.trim(), type: addType, params: { ...addParams } }])
    setAddId('')
    setAddParams({})
  }

  const removeIndicator = (id: string) => {
    setIndicators(prev => prev.filter(i => i.id !== id))
  }

  const addCompound = () => {
    if (!addCompoundId.trim()) return
    const params: Record<string, any> = {}
    if (addCompoundType === 'ema_alignment' || addCompoundType === 'ema_spread') {
      // Need emas list — use available EMA ids
      const emaIds = indicators.filter(i => i.type === 'ema').map(i => i.id)
      params.emas = emaIds.length > 0 ? emaIds : ['ema_5', 'ema_8', 'ema_13']
    }
    if (addCompoundType === 'pull_count' || addCompoundType === 'candle_proximity') {
      const firstEma = indicators.find(i => i.type === 'ema')
      params.ema = firstEma?.id || 'ema_5'
    }
    setCompounds(prev => [...prev, { id: addCompoundId.trim(), type: addCompoundType, params }])
    setAddCompoundId('')
  }

  const removeCompound = (id: string) => {
    setCompounds(prev => prev.filter(c => c.id !== id))
  }

  const togglePattern = (p: string) => {
    setPatterns(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p])
  }

  const handleTest = async () => {
    if (!name.trim()) { setError('Name is required'); return }
    setTesting(true)
    setError('')
    setTestResult(null)
    try {
      const dslData = {
        name: name.trim(),
        description,
        timeframe,
        ticker: 'SYNTHETIC',
        interval: '1h',
        period: '5d',
        indicators: indicators.map(i => ({ id: i.id, type: i.type, params: i.params })),
        compounds: compounds.map(c => ({ id: c.id, type: c.type, params: c.params })),
        patterns,
        signals: {} as Record<string, string>,
      }
      if (entryCond) dslData.signals['entry'] = entryCond
      if (exitCond) dslData.signals['exit'] = exitCond

      const res = await fetch('/api/dsl/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dslData),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || `Test failed: ${res.status}`)
      }
      const result = await res.json()
      setTestResult(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async () => {
    if (!name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const dslData = {
        name: name.trim(),
        description,
        timeframe,
        indicators: indicators.map(i => ({ id: i.id, type: i.type, params: i.params })),
        compounds: compounds.map(c => ({ id: c.id, type: c.type, params: c.params })),
        patterns,
        signals: {} as Record<string, string>,
      }
      if (entryCond) dslData.signals['entry'] = entryCond
      if (exitCond) dslData.signals['exit'] = exitCond

      if (isEditing && editName) {
        const result = await updateDsl(editName, dslData)
        setSuccess(`Updated ${result.name}`)
        setTimeout(() => navigate(`/dsl/${encodeURIComponent(result.name)}`), 1200)
      } else {
        const created = await createDsl(dslData)
        setSuccess(`Created ${created.name}`)
        setTimeout(() => navigate(`/dsl/${encodeURIComponent(created.name)}`), 1200)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  if (loadingTypes) return <div className="loading">Loading indicator types...</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <a href="/dsl" style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }} onClick={e => { e.preventDefault(); navigate('/dsl') }}>← Back to DSLs</a>
          <div className="page-title" style={{ marginTop: 4 }}>{isEditing ? `Edit: ${editName}` : 'New Indicator'}</div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div style={{ padding: '1rem', color: 'var(--emerald)', background: 'rgba(52,211,153,0.1)', border: '1px solid var(--emerald)', borderRadius: 6, marginBottom: '1rem', fontSize: '0.85rem' }}>{success}</div>}

      <div className="grid grid-2" style={{ gridTemplateColumns: '1.3fr 1fr' }}>
        {/* Left: Form */}
        <div>
          {/* Basic info */}
          <div className="card">
            <div className="card-header">Basic Info</div>
            <div className="card-body">
              <div style={{ marginBottom: '0.75rem' }}>
                <label className="form-label">Name</label>
                <input className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="my-breakout-strategy" />
              </div>
              <div style={{ marginBottom: '0.75rem' }}>
                <label className="form-label">Description</label>
                <input className="form-input" value={description} onChange={e => setDescription(e.target.value)} placeholder="EMA crossover with RSI filter" />
              </div>
              <div>
                <label className="form-label">Timeframe</label>
                <select className="form-select" value={timeframe} onChange={e => setTimeframe(e.target.value)}>
                  {['15m','30m','1h','4h','1d'].map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Standard indicators */}
          <div className="card">
            <div className="card-header">Standard Indicators <span style={{ fontWeight: 400, color: 'var(--text-dim)', fontSize: '0.75rem' }}>({indicators.length} added)</span></div>
            <div className="card-body">
              {indicators.map(ind => (
                <div key={ind.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', borderBottom: '1px solid var(--border)', fontSize: '0.8rem' }}>
                  <span><span className="tag tag-cyan">{ind.type}</span> {ind.id}</span>
                  <button className="btn btn-sm" onClick={() => removeIndicator(ind.id)} style={{ color: 'var(--rose)' }}>×</button>
                </div>
              ))}
              {indicators.length === 0 && <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', marginBottom: '0.5rem' }}>No indicators added yet</div>}
              <hr />
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'end' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label">Type</label>
                  <select className="form-select" value={addType} onChange={e => setAddType(e.target.value)}>
                    {allIndicators.filter(i => !i.vt_concept).map(i => (
                      <option key={i.type} value={i.type}>{i.type} — {i.category}</option>
                    ))}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label">ID (e.g. ema_fast)</label>
                  <input className="form-input" value={addId} onChange={e => setAddId(e.target.value)} placeholder={`${addType}_1`} />
                </div>
                {selectedType && Object.keys(selectedType.params).length > 0 && Object.entries(selectedType.params).filter(([k]) => k !== 'source').map(([k, v]) => (
                  <div key={k} style={{ width: 80 }}>
                    <label className="form-label">{k}</label>
                    <input className="form-input" type="number"
                      defaultValue={(v as any).default ?? 14}
                      onChange={e => setAddParams(prev => ({ ...prev, [k]: Number(e.target.value) }))} />
                  </div>
                ))}
                <div>
                  <button className="btn btn-primary" onClick={addIndicator} disabled={!addId.trim()}>Add</button>
                </div>
              </div>
            </div>
          </div>

          {/* VT Compounds */}
          <div className="card">
            <div className="card-header">VT Compounds <span style={{ fontWeight: 400, color: 'var(--text-dim)', fontSize: '0.75rem' }}>({compounds.length} added)</span></div>
            <div className="card-body">
              {compounds.map(c => (
                <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', borderBottom: '1px solid var(--border)', fontSize: '0.8rem' }}>
                  <span><span className="tag tag-emerald">{c.type}</span> {c.id}</span>
                  <button className="btn btn-sm" onClick={() => removeCompound(c.id)} style={{ color: 'var(--rose)' }}>×</button>
                </div>
              ))}
              {compounds.length === 0 && <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', marginBottom: '0.5rem' }}>No compounds added yet</div>}
              <hr />
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'end' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label">Type</label>
                  <select className="form-select" value={addCompoundType} onChange={e => setAddCompoundType(e.target.value)}>
                    {allIndicators.filter(i => i.vt_concept).map(i => (
                      <option key={i.type} value={i.type}>{i.type}</option>
                    ))}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label">ID</label>
                  <input className="form-input" value={addCompoundId} onChange={e => setAddCompoundId(e.target.value)} placeholder={`${addCompoundType}_1`} />
                </div>
                <div>
                  <button className="btn btn-primary" onClick={addCompound} disabled={!addCompoundId.trim()}>Add</button>
                </div>
              </div>
            </div>
          </div>

          {/* Patterns */}
          <div className="card">
            <div className="card-header">Candlestick Patterns</div>
            <div className="card-body">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {allPatterns.map(p => (
                  <label key={p} style={{ cursor: 'pointer', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input type="checkbox" checked={patterns.includes(p)} onChange={() => togglePattern(p)} />
                    {p}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Signals */}
          <div className="card">
            <div className="card-header">Signal Conditions</div>
            <div className="card-body">
              <div style={{ marginBottom: '0.75rem' }}>
                <label className="form-label" style={{ color: 'var(--emerald)' }}>Entry Condition</label>
                <input className="form-input" value={entryCond} onChange={e => setEntryCond(e.target.value)}
                  placeholder='rsi < 30 AND hammer' />
              </div>
              <div>
                <label className="form-label" style={{ color: 'var(--rose)' }}>Exit Condition</label>
                <input className="form-input" value={exitCond} onChange={e => setExitCond(e.target.value)}
                  placeholder='rsi > 70 OR pull >= 3' />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="card">
            <div className="card-body" style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-primary" onClick={handleTest} disabled={testing || !name.trim()}>
                {testing ? 'Testing...' : '▶ Test'}
              </button>
              <button className="btn btn-primary" style={{ background: 'var(--emerald)', borderColor: 'var(--emerald)' }}
                onClick={handleSave} disabled={saving || !name.trim()}>
                {saving ? 'Saving...' : isEditing ? '💾 Update' : '💾 Save'}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Preview */}
        <div>
          <div className="card">
            <div className="card-header">DSL Preview (YAML)</div>
            <div style={{ padding: 0 }}>
              <pre className="code-block" style={{ borderRadius: 0, border: 'none' }}>{yamlPreview}</pre>
            </div>
          </div>

          {testResult && testResult.chart_data && (
            <div className="card">
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Test Results — {testResult.ticker} ({testResult.interval})</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{testResult.date_range}</span>
              </div>
              <div className="card-body" style={{ padding: '0.5rem' }}>
                <Chart data={testResult.chart_data} />
              </div>
              <div className="card-body">
                <div className="grid grid-4">
                  <div className="stat-box emerald"><div className="value">{testResult.stats.entry_count}</div><div className="label">Entries</div></div>
                  <div className="stat-box rose"><div className="value">{testResult.stats.exit_count}</div><div className="label">Exits</div></div>
                  <div className="stat-box amber"><div className="value">{testResult.stats.total_bars}</div><div className="label">Bars</div></div>
                  <div className="stat-box cyan"><div className="value">{testResult.stats.signal_density}%</div><div className="label">Density</div></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
