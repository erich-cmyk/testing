import { useState } from 'react'
import { logEvent } from '../api'

const SOURCES = ['openai', 'anthropic', 'copilot', 'custom']
const TASK_TYPES = ['code', 'writing', 'analysis', 'summarization', 'classification', 'research', 'other']
const DEPARTMENTS = ['Engineering', 'Marketing', 'Legal', 'Finance', 'Sales', 'HR', 'Other']

const DEFAULT = {
  source: 'openai',
  tool_name: '',
  user_id: '',
  department: 'Engineering',
  task_type: 'code',
  input_tokens: 0,
  output_tokens: 0,
  cost_usd: 0,
  time_saved_minutes: 10,
  hourly_rate_usd: 50,
  quality_score: '',
  notes: '',
}

export default function LogEvent() {
  const [form, setForm] = useState(DEFAULT)
  const [status, setStatus] = useState(null)

  function set(k, v) {
    setForm(f => ({ ...f, [k]: v }))
  }

  async function submit(e) {
    e.preventDefault()
    setStatus('saving')
    try {
      await logEvent({
        ...form,
        input_tokens: Number(form.input_tokens),
        output_tokens: Number(form.output_tokens),
        cost_usd: Number(form.cost_usd),
        time_saved_minutes: Number(form.time_saved_minutes),
        hourly_rate_usd: Number(form.hourly_rate_usd),
        quality_score: form.quality_score ? Number(form.quality_score) : null,
      })
      setStatus('saved')
      setForm(DEFAULT)
    } catch {
      setStatus('error')
    }
  }

  const field = (label, key, type = 'text', props = {}) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-gray-400">{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={e => set(key, e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
        {...props}
      />
    </div>
  )

  const select = (label, key, options) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-gray-400">{label}</label>
      <select
        value={form[key]}
        onChange={e => set(key, e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Log Usage Event</h1>
      <p className="text-gray-400 text-sm mb-6">Manually record an AI usage session and its business value.</p>

      <form onSubmit={submit} className="space-y-4 bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <div className="grid grid-cols-2 gap-4">
          {select('Source', 'source', SOURCES)}
          {field('Tool / Model Name', 'tool_name', 'text', { placeholder: 'e.g. gpt-4o, claude-sonnet-4-6', required: true })}
          {select('Department', 'department', DEPARTMENTS)}
          {select('Task Type', 'task_type', TASK_TYPES)}
          {field('User ID (optional)', 'user_id', 'text', { placeholder: 'e.g. john@company.com' })}
          {field('Quality Score (0–10)', 'quality_score', 'number', { min: 0, max: 10, step: 0.1, placeholder: 'optional' })}
        </div>

        <div className="border-t border-gray-800 pt-4">
          <p className="text-xs text-gray-500 mb-3 uppercase tracking-wide">Cost</p>
          <div className="grid grid-cols-3 gap-4">
            {field('Input Tokens', 'input_tokens', 'number', { min: 0 })}
            {field('Output Tokens', 'output_tokens', 'number', { min: 0 })}
            {field('API Cost (USD)', 'cost_usd', 'number', { min: 0, step: 0.000001, placeholder: '0.00' })}
          </div>
        </div>

        <div className="border-t border-gray-800 pt-4">
          <p className="text-xs text-gray-500 mb-3 uppercase tracking-wide">Business Value</p>
          <div className="grid grid-cols-2 gap-4">
            {field('Time Saved (minutes)', 'time_saved_minutes', 'number', { min: 0, step: 0.5 })}
            {field('Hourly Rate (USD)', 'hourly_rate_usd', 'number', { min: 1 })}
          </div>
          <div className="mt-2 p-3 bg-gray-800 rounded-lg text-sm text-indigo-300">
            Estimated value: ${((Number(form.time_saved_minutes) / 60) * Number(form.hourly_rate_usd)).toFixed(2)}
            {' '}| Net ROI: ${(((Number(form.time_saved_minutes) / 60) * Number(form.hourly_rate_usd)) - Number(form.cost_usd)).toFixed(2)}
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">Notes (optional)</label>
          <textarea
            value={form.notes}
            onChange={e => set('notes', e.target.value)}
            rows={2}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 resize-none"
          />
        </div>

        <button
          type="submit"
          disabled={status === 'saving'}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg py-2.5 text-sm font-semibold transition-colors"
        >
          {status === 'saving' ? 'Saving...' : 'Log Event'}
        </button>

        {status === 'saved' && <p className="text-green-400 text-sm text-center">Event logged successfully.</p>}
        {status === 'error' && <p className="text-red-400 text-sm text-center">Failed to save. Is the backend running?</p>}
      </form>
    </div>
  )
}
