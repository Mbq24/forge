import Plot from 'react-plotly.js'

interface ChartProps {
  data: {
    traces: Array<{
      x: string[]
      y: number[]
      name: string
      type: string
      mode?: string
      marker?: any
      line?: any
    }>
    layout: any
  }
}

export default function Chart({ data }: ChartProps) {
  return (
    <Plot
      data={data.traces.map(t => ({
        x: t.x,
        y: t.y,
        type: t.type === 'scatter' ? 'scatter' as const : 'scatter' as const,
        mode: (t.mode || 'lines') as 'lines' | 'markers' | 'lines+markers',
        name: t.name,
        marker: t.marker,
        line: t.line,
      }))}
      layout={{
        ...data.layout,
        dragmode: 'zoom',           // drag = box zoom (backend default is 'pan')
        hovermode: data.layout?.hovermode || 'x unified',
        paper_bgcolor: '#0f172a',
        plot_bgcolor: '#0f172a',
        font: { color: '#94a3b8', size: 10, family: 'Segoe UI, system-ui, sans-serif' },
        margin: { t: 10, r: 10, b: 30, l: 40 },
        xaxis: { ...data.layout?.xaxis, gridcolor: '#1e293b' },
        yaxis: { ...data.layout?.yaxis, gridcolor: '#1e293b' },
      }}
      config={{
        responsive: true,
        scrollZoom: true,           // scroll wheel zooms
        displayModeBar: true,       // show zoom/pan/reset buttons
        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
        doubleClick: 'reset',       // double-click resets zoom
      }}
      style={{ width: '100%', height: '420px' }}
      useResizeHandler={true}
    />
  )
}
