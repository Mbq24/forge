const BASE = '/api'

export interface DslListItem {
  name: string
  description: string
  timeframe: string
  indicators: any[]
  compounds: any[]
  patterns: string[]
  signals: Record<string, { condition: string }>
}

export interface DslDetail {
  dsl_name: string
  indicators: any[]
  compounds: any[]
  timeframe: string
  tickers: Record<string, string[]>
  ticker: string
  interval: string
  period: string
  yaml_content: string
  pine_code: string
  chart_html: string | null
  chart_data: any | null
  backtest: any | null
  error: string | null
  stats: { entry_count: number; exit_count: number; total_bars: number; signal_density: number }
  entry_cond: string
  exit_cond: string
  date_range: string
}

export interface DbStats {
  signals: number
  rsi: number
  stochastic: number
  lines: number
}

export async function fetchDslList(): Promise<DslListItem[]> {
  const res = await fetch(`${BASE}/dsl`)
  if (!res.ok) throw new Error(`Failed to fetch DSL list: ${res.status}`)
  return res.json()
}

export async function fetchDslDetail(
  name: string,
  params: { ticker?: string; interval?: string; period?: string; backtest?: string } = {}
): Promise<DslDetail> {
  const qs = new URLSearchParams({
    ticker: params.ticker || 'SYNTHETIC',
    interval: params.interval || '1h',
    period: params.period || '5d',
  })
  if (params.backtest) qs.set('backtest', params.backtest)
  const res = await fetch(`${BASE}/dsl/${encodeURIComponent(name)}?${qs}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text.slice(0, 200))
  }
  return res.json()
}

export async function fetchDbStats(): Promise<DbStats> {
  const res = await fetch(`${BASE}/dashboard/stats`)
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`)
  return res.json()
}

export async function fetchDbTable(table: string): Promise<any[]> {
  const res = await fetch(`${BASE}/dashboard/table/${table}`)
  if (!res.ok) throw new Error(`Failed to fetch ${table}`)
  return res.json()
}

export interface IndicatorType {
  type: string
  category: string
  description: string
  params: Record<string, any>
  vt_concept: boolean
}

export async function fetchIndicatorTypes(): Promise<{ indicators: IndicatorType[]; patterns: string[]; categories: string[] }> {
  const res = await fetch(`${BASE}/indicators`)
  if (!res.ok) throw new Error(`Failed to fetch indicators: ${res.status}`)
  return res.json()
}

export async function createDsl(dslData: any): Promise<{ status: string; name: string; filename: string }> {
  const res = await fetch(`${BASE}/dsl`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dslData),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || `Failed to create DSL: ${res.status}`)
  }
  return res.json()
}

export async function deleteDsl(name: string): Promise<void> {
  const res = await fetch(`${BASE}/dsl/${encodeURIComponent(name)}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete DSL: ${res.status}`)
}

export interface AdvisorSuggestion {
  ticker: string
  interval: string
  period: string
  preferences: {
    trade_style: string
    risk_level: string
    instrument_type: string
    direction_bias: string
  }
  multi_tf: {
    higher_interval: string
    higher_trend: string
    higher_rsi: number
    higher_atr_pct: number
    trend_aligned: boolean
  }
  analysis: {
    trend_strength: number
    is_trending: boolean
    is_volatile: boolean
    atr_pct: number
    rsi_estimate: number
    above_ma: boolean
    volume_ratio: number
    bar_count: number
    date_range: string
  }
  explanation: string[]
  suggested_dsl: any
}

export interface AdvisorPrefs {
  trade_style: 'scalp' | 'intraday' | 'swing'
  risk_level: 'conservative' | 'moderate' | 'aggressive'
  instrument_type: 'crypto' | 'forex' | 'stocks' | 'indices'
  direction_bias: 'both' | 'long' | 'short'
}

export async function fetchAdvisorSuggestion(
  ticker: string,
  interval: string,
  period: string,
  preferences: AdvisorPrefs
): Promise<AdvisorSuggestion> {
  const res = await fetch(`${BASE}/advisor/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, interval, period, preferences }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || `Advisor failed: ${res.status}`)
  }
  return res.json()
}

export interface DslEditData {
  name: string
  description: string
  timeframe: string
  indicators: Array<{ id: string; type: string; params: Record<string, any> }>
  compounds: Array<{ id: string; type: string; params: Record<string, any> }>
  patterns: string[]
  signals: Record<string, string>
  yaml_content: string
}

export async function fetchDslEdit(name: string): Promise<DslEditData> {
  const res = await fetch(`${BASE}/dsl/${encodeURIComponent(name)}?mode=edit`)
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || `Failed to fetch DSL: ${res.status}`)
  }
  return res.json()
}

export async function updateDsl(name: string, dslData: any): Promise<{ status: string; name: string; filename: string }> {
  const res = await fetch(`${BASE}/dsl/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dslData),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || `Failed to update DSL: ${res.status}`)
  }
  return res.json()
}
