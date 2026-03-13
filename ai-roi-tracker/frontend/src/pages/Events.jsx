import { useEffect, useState } from 'react'
import { getEvents } from '../api'
import SourceBadge from '../components/SourceBadge'

export default function Events() {
  const [events, setEvents] = useState([])
  const [source, setSource] = useState('')
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getEvents({ days, ...(source ? { source } : {}) })
      .then(setEvents)
      .finally(() => setLoading(false))
  }, [source, days])

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Usage Events</h1>
          <p className="text-gray-400 text-sm">{events.length} events</p>
        </div>
        <div className="flex gap-3">
          <select
            value={source}
            onChange={e => setSource(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none"
          >
            <option value="">All sources</option>
            {['openai', 'anthropic', 'copilot', 'custom'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none"
          >
            {[7, 14, 30, 60, 90].map(d => (
              <option key={d} value={d}>Last {d}d</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="text-gray-400 text-sm">Loading...</div>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase tracking-wide border-b border-gray-800">
              <th className="text-left py-3 pr-4">Source</th>
              <th className="text-left py-3 pr-4">Tool</th>
              <th className="text-left py-3 pr-4">Dept</th>
              <th className="text-left py-3 pr-4">Task</th>
              <th className="text-right py-3 pr-4">Tokens</th>
              <th className="text-right py-3 pr-4">Cost</th>
              <th className="text-right py-3 pr-4">Value</th>
              <th className="text-right py-3 pr-4">ROI</th>
              <th className="text-right py-3">Time Saved</th>
            </tr>
          </thead>
          <tbody>
            {events.map(e => {
              const value = (e.time_saved_minutes / 60) * e.hourly_rate_usd
              const roi = value - e.cost_usd
              return (
                <tr key={e.id} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                  <td className="py-2.5 pr-4"><SourceBadge source={e.source} /></td>
                  <td className="py-2.5 pr-4 font-mono text-xs text-gray-300">{e.tool_name}</td>
                  <td className="py-2.5 pr-4 text-gray-400">{e.department || '—'}</td>
                  <td className="py-2.5 pr-4 text-gray-400">{e.task_type || '—'}</td>
                  <td className="py-2.5 pr-4 text-right text-gray-400">{(e.input_tokens + e.output_tokens).toLocaleString()}</td>
                  <td className="py-2.5 pr-4 text-right text-orange-300">${e.cost_usd.toFixed(4)}</td>
                  <td className="py-2.5 pr-4 text-right text-indigo-300">${value.toFixed(2)}</td>
                  <td className={`py-2.5 pr-4 text-right font-semibold ${roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    ${roi.toFixed(2)}
                  </td>
                  <td className="py-2.5 text-right text-gray-400">{e.time_saved_minutes}m</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {!loading && events.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No events yet. Log one manually or sync an integration.
          </div>
        )}
      </div>
    </div>
  )
}
