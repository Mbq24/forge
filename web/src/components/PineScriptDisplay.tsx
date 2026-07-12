interface Props {
  code: string
}

export default function PineScriptDisplay({ code }: Props) {
  // Simple syntax highlighting for Pine Script
  const highlighted = code
    .replace(/(\/\/.*)/g, '<span style="color:#475569;font-style:italic">$1</span>')
    .replace(/\b(and|or|not|var|if|else|for|while|true|false)\b/g,
      '<span style="color:#fb7185;font-weight:500">$1</span>')
    .replace(/(ta\.\w+)/g, '<span style="color:#fbbf24">$1</span>')
    .replace(/([0-9]+\.[0-9]+)/g, '<span style="color:#34d399">$1</span>')
    .replace(/(\b[0-9]+\b)/g, '<span style="color:#34d399">$1</span>')
    .replace(/(".*?")/g, '<span style="color:#a78bfa">$1</span>')
    .replace(/(color\.\w+)/g, '<span style="color:#22d3ee">$1</span>')

  return (
    <pre
      className="code-block"
      style={{ borderRadius: 0, border: 'none' }}
      dangerouslySetInnerHTML={{ __html: highlighted }}
    />
  )
}
