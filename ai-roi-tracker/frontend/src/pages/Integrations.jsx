import { useState } from 'react'
import { syncOpenAI, syncAnthropic, syncCopilot } from '../api'

function IntegrationCard({ title, description, fields, onSync, color }) {
  const [values, setValues] = useState({})
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)

  async function handleSync() {
    setStatus('syncing')
    try {
      const res = await onSync(values)
      setResult(res)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div className={`bg-gray-900 rounded-2xl p-5 border border-gray-800`}>
      <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${color}`}>{title}</div>
      <p className="text-gray-400 text-sm mb-4">{description}</p>
      <div className="space-y-3">
        {fields.map(f => (
          <div key={f.key} className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">{f.label}</label>
            <input
              type="password"
              placeholder={f.placeholder}
              value={values[f.key] || ''}
              onChange={e => setValues(v => ({ ...v, [f.key]: e.target.value }))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        ))}
      </div>
      <button
        onClick={handleSync}
        disabled={status === 'syncing'}
        className="mt-4 w-full bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg py-2 text-sm font-semibold transition-colors"
      >
        {status === 'syncing' ? 'Syncing...' : 'Sync Now'}
      </button>
      {status === 'done' && (
        <p className="text-green-400 text-sm mt-2">
          Synced {result?.synced ?? 0} events.
        </p>
      )}
      {status === 'error' && (
        <p className="text-red-400 text-sm mt-2">Sync failed. Check your credentials.</p>
      )}
    </div>
  )
}

export default function Integrations() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Integrations</h1>
      <p className="text-gray-400 text-sm mb-6">
        Connect your AI providers to automatically pull usage and cost data.
      </p>

      <div className="grid md:grid-cols-2 gap-4">
        <IntegrationCard
          title="OpenAI"
          color="text-green-400"
          description="Fetch token usage and costs from your OpenAI organization."
          fields={[{ key: 'key', label: 'API Key', placeholder: 'sk-...' }]}
          onSync={v => syncOpenAI(v.key)}
        />
        <IntegrationCard
          title="Anthropic"
          color="text-orange-400"
          description="Fetch token usage and costs from your Anthropic account."
          fields={[{ key: 'key', label: 'API Key', placeholder: 'sk-ant-...' }]}
          onSync={v => syncAnthropic(v.key)}
        />
        <IntegrationCard
          title="GitHub Copilot"
          color="text-blue-400"
          description="Fetch seat usage and suggestion acceptance rates from your GitHub org."
          fields={[
            { key: 'token', label: 'GitHub Token', placeholder: 'ghp_...' },
            { key: 'org', label: 'GitHub Org', placeholder: 'my-company' },
          ]}
          onSync={v => syncCopilot(v.token, v.org)}
        />
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <div className="text-xs font-bold uppercase tracking-wider mb-1 text-purple-400">Custom / Internal</div>
          <p className="text-gray-400 text-sm mb-4">
            Push data from any internal AI system via webhook.
          </p>
          <div className="bg-gray-800 rounded-lg p-3 text-xs font-mono text-gray-300 break-all">
            POST /api/integrations/custom/webhook
          </div>
          <p className="text-gray-500 text-xs mt-3">
            Send JSON with: tool_name, cost_usd, time_saved_minutes, input_tokens, output_tokens, department, task_type
          </p>
        </div>
      </div>
    </div>
  )
}
