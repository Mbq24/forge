import { useState, useEffect } from 'react'

export interface CondRow {
  id: string
  left: string
  op: string
  rightType: 'value' | 'ref'
  rightVal: string
  crossRight: string   // second argument for XOVER/XUNDER
  logic: 'AND' | 'OR'
}

interface Props {
  label: string
  labelColor: string
  availableRefs: string[]
  booleanRefs?: string[]    // refs that are already boolean (patterns, sessions)
  value: string          // current condition string
  onChange: (val: string) => void
}

const OPERATORS = ['>', '<', '>=', '<=', '==', '!=']
const CROSS_TYPES = ['XOVER', 'XUNDER']

let rowCounter = 0
const newRow = (): CondRow => ({
  id: `r${++rowCounter}`, left: '', op: '>',
  rightType: 'value', rightVal: '', crossRight: '',
  logic: 'AND'
})

// Parse a condition string like "rsi < 30 AND hammer" or "CROSSOVER(ema_8, ema_5)" into rows
function parseToRows(expr: string, availableRefs: string[], booleanRefs: string[] = []): CondRow[] {
  if (!expr.trim()) return [newRow()]
  const rows: CondRow[] = []
  // Split on AND/OR (case-insensitive, with word boundaries)
  const parts = expr.split(/\b(AND|OR)\b/i)
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim()
    if (!part) continue
    if (part.toUpperCase() === 'AND' || part.toUpperCase() === 'OR') {
      if (rows.length > 0) rows[rows.length - 1].logic = part.toUpperCase() as 'AND' | 'OR'
      continue
    }
    // Try to parse crossover: CROSSOVER(a, b) or crossunder: CROSSUNDER(a, b)
    const crossMatch = part.match(/^(CROSSOVER|CROSSUNDER)\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)$/i)
    if (crossMatch) {
      const [, crossType, left, right] = crossMatch
      rows.push({
        id: `r${++rowCounter}`,
        left: left.trim(),
        op: crossType === 'CROSSOVER' ? 'XOVER' : 'XUNDER',
        rightType: 'ref',
        rightVal: '',
        crossRight: right.trim(),
        logic: 'AND',
      })
      continue
    }
    // Try to parse "left op right"
    const match = part.match(/^(.+?)\s*(>=|<=|!=|==|>|<)\s*(.+)$/)
    if (match) {
      const [, left, op, rightRaw] = match
      const right = rightRaw.trim()
      const isRef = availableRefs.includes(right) || /^[a-zA-Z_]/.test(right)
      rows.push({
        id: `r${++rowCounter}`,
        left: left.trim(),
        op,
        rightType: isRef ? 'ref' : 'value',
        rightVal: right,
        crossRight: '',
        logic: 'AND',
      })
    } else {
      // Just a bare identifier — boolean refs stay bare, others get > 0
      if (booleanRefs.includes(part)) {
        rows.push({ id: `r${++rowCounter}`, left: part, op: '', rightType: 'value', rightVal: '', crossRight: '', logic: 'AND' })
      } else {
        rows.push({ id: `r${++rowCounter}`, left: part, op: '>', rightType: 'value', rightVal: '0', crossRight: '', logic: 'AND' })
      }
    }
  }
  if (rows.length === 0) rows.push(newRow())
  return rows
}

// Serialize rows back to a condition string
function rowsToString(rows: CondRow[], booleanRefs: string[] = []): string {
  const nonEmpty = rows.filter(r => r.left.trim() !== '')
  return nonEmpty
    .map((r, i) => {
      const left = r.left
      // Boolean refs (patterns, sessions) — just the name
      if (booleanRefs.includes(left)) {
        const logic = i > 0 ? ` ${nonEmpty[i - 1].logic} ` : ''
        return `${logic}${left}`
      }
      // Crossover/crossunder rows
      if (r.op === 'XOVER' || r.op === 'XUNDER') {
        const fn = r.op === 'XOVER' ? 'CROSSOVER' : 'CROSSUNDER'
        const clause = `${fn}(${left}, ${r.crossRight || 'close'})`
        const logic = i > 0 ? ` ${nonEmpty[i - 1].logic} ` : ''
        return `${logic}${clause}`
      }
      // Regular comparison rows
      const right = r.rightType === 'ref' ? r.rightVal : r.rightVal
      const clause = right ? `${left} ${r.op} ${right}` : left
      const logic = i > 0 ? ` ${nonEmpty[i - 1].logic} ` : ''
      return `${logic}${clause}`
    })
    .join('')
    .replace(/^AND |^OR /, '')
}

export default function ConditionBuilder({ label, labelColor, availableRefs, booleanRefs = [], value, onChange }: Props) {
  const [rows, setRows] = useState<CondRow[]>(() => parseToRows(value, availableRefs, booleanRefs))

  // Re-sync only when availableRefs changes (indicator added/removed)
  useEffect(() => {
    setRows(parseToRows(value, availableRefs, booleanRefs))
  }, [availableRefs, booleanRefs])

  const updateRow = (id: string, patch: Partial<CondRow>) => {
    const next = rows.map(r => r.id === id ? { ...r, ...patch } : r)
    setRows(next)
    onChange(rowsToString(next, booleanRefs))
  }

  const removeRow = (id: string) => {
    const next = rows.filter(r => r.id !== id)
    if (next.length === 0) next.push(newRow())
    setRows(next)
    onChange(rowsToString(next, booleanRefs))
  }

  const addRow = () => {
    const next = [...rows, newRow()]
    setRows(next)
  }

  return (
    <div className="card" style={{ marginBottom: '0.75rem' }}>
      <div className="card-header" style={{ color: labelColor }}>{label}</div>
      <div className="card-body" style={{ padding: '0.5rem' }}>
        {rows.map((row, i) => (
          <div key={row.id}>
            {i > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '4px 0' }}>
                <select
                  className="form-select"
                  value={row.logic}
                  onChange={e => updateRow(row.id, { logic: e.target.value as 'AND' | 'OR' })}
                  style={{ width: 80, fontSize: '0.75rem', padding: '2px 4px' }}
                >
                  <option value="AND">AND</option>
                  <option value="OR">OR</option>
                </select>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>join</span>
              </div>
            )}
            <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexWrap: 'wrap' }}>
              {/* Left: indicator/pattern/ref */}
              <select
                className="form-select"
                value={row.left}
                onChange={e => updateRow(row.id, { left: e.target.value })}
                style={{ minWidth: 120, fontSize: '0.75rem', padding: '2px 4px' }}
              >
                <option value="">— select —</option>
                {availableRefs.map(ref => (
                  <option key={ref} value={ref}>{ref}</option>
                ))}
              </select>

              {/* Boolean refs (patterns, sessions) — no comparison needed */}
              {booleanRefs.includes(row.left) ? (
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', padding: '0 4px' }}>
                  = true
                </span>
              ) : (
                <>
              {/* Operator (includes XOVER/XUNDER for cross detection) */}
              <select
                className="form-select"
                value={row.op}
                onChange={e => updateRow(row.id, { op: e.target.value })}
                style={{ width: 76, fontSize: '0.75rem', padding: '2px 4px' }}
              >
                <optgroup label="Compare">
                  {OPERATORS.map(op => (
                    <option key={op} value={op}>{op}</option>
                  ))}
                </optgroup>
                <optgroup label="Cross">
                  <option value="XOVER">XOVER</option>
                  <option value="XUNDER">XUNDER</option>
                </optgroup>
              </select>

              {/* Right side: depends on operator */}
              {row.op === 'XOVER' || row.op === 'XUNDER' ? (
                <select
                  className="form-select"
                  value={row.crossRight}
                  onChange={e => updateRow(row.id, { crossRight: e.target.value })}
                  style={{ minWidth: 100, fontSize: '0.75rem', padding: '2px 4px' }}
                >
                  <option value="">— cross with —</option>
                  {availableRefs.filter(r => r !== row.left).map(ref => (
                    <option key={ref} value={ref}>{ref}</option>
                  ))}
                </select>
              ) : (
                <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                  <select
                    className="form-select"
                    value={row.rightType}
                    onChange={e => updateRow(row.id, { rightType: e.target.value as 'value' | 'ref' })}
                    style={{ width: 56, fontSize: '0.7rem', padding: '2px 4px' }}
                  >
                    <option value="value">val</option>
                    <option value="ref">ref</option>
                  </select>

                  {row.rightType === 'value' ? (
                    <input
                      className="form-input"
                      type="text"
                      value={row.rightVal}
                      onChange={e => updateRow(row.id, { rightVal: e.target.value })}
                      placeholder="e.g. 30, 70"
                      style={{ width: 80, fontSize: '0.75rem', padding: '2px 4px' }}
                    />
                  ) : (
                    <select
                      className="form-select"
                      value={row.rightVal}
                      onChange={e => updateRow(row.id, { rightVal: e.target.value })}
                      style={{ minWidth: 100, fontSize: '0.75rem', padding: '2px 4px' }}
                    >
                      <option value="">— select —</option>
                      {availableRefs.map(ref => (
                        <option key={ref} value={ref}>{ref}</option>
                      ))}
                    </select>
                  )}
                </div>
              )}
              </>
              )}

              {/* Remove row */}
              <button
                className="btn btn-sm"
                onClick={() => removeRow(row.id)}
                style={{ color: 'var(--rose)', fontSize: '0.75rem', padding: '2px 6px' }}
                title="Remove condition"
              >×</button>
            </div>
          </div>
        ))}
        <button className="btn btn-sm" onClick={addRow} style={{ marginTop: 6, fontSize: '0.75rem' }}>
          + Add Condition
        </button>
      </div>
    </div>
  )
}
