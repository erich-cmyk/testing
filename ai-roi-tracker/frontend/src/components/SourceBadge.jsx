const COLORS = {
  openai: 'bg-green-900 text-green-300',
  anthropic: 'bg-orange-900 text-orange-300',
  copilot: 'bg-blue-900 text-blue-300',
  custom: 'bg-purple-900 text-purple-300',
}

export default function SourceBadge({ source }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${COLORS[source] ?? 'bg-gray-800 text-gray-300'}`}>
      {source}
    </span>
  )
}
