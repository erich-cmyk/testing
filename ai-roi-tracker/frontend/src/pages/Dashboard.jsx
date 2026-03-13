import { useEffect, useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { getSummary, getDaily, getByDepartment, getByTaskType } from '../api'
import StatCard from '../components/StatCard'

const PIE_COLORS = ['#6366f1', '#f97316', '#22d3ee', '#a78bfa', '#34d399', '#fb7185']

function fmt(n) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(2)}`
}

export default function Dashboard() {
  const [days, setDays] = useState(30)
  const [summary, setSummary] = useState(null)
  const [daily, setDaily] = useState([])
  const [depts, setDepts] = useState([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([getSummary(days), getDaily(days), getByDepartment(days), getByTaskType(days)])
      .then(([s, d, de, t]) => {
        setSummary(s)
        setDaily(d)
        setDepts(de)
        setTasks(t)
      })
      .finally(() => setLoading(false))
  }, [days])

  const sourceData = summary
    ? Object.entries(summary.by_source).map(([k, v]) => ({ name: k, roi: v.roi_usd, cost: v.cost_usd, value: v.value_usd }))
    : []

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI ROI Dashboard</h1>
          <p className="text-gray-400 text-sm">Track the business value of your AI investment</p>
        </div>
        <select
          value={days}
          onChange={e => setDays(Number(e.target.value))}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none"
        >
          {[7, 14, 30, 60, 90].map(d => (
            <option key={d} value={d}>Last {d} days</option>
          ))}
        </select>
      </div>

      {loading && <div className="text-gray-400 text-sm">Loading...</div>}

      {/* KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Net ROI"
            value={fmt(summary.net_roi_usd)}
            sub={`${summary.roi_percent}% return on AI spend`}
            color={summary.net_roi_usd >= 0 ? 'text-green-400' : 'text-red-400'}
          />
          <StatCard
            label="Value Generated"
            value={fmt(summary.total_value_usd)}
            sub="Est. human time saved × hourly rate"
            color="text-indigo-400"
          />
          <StatCard
            label="Total AI Cost"
            value={fmt(summary.total_cost_usd)}
            sub={`${summary.total_events.toLocaleString()} usage events`}
            color="text-orange-400"
          />
          <StatCard
            label="Hours Saved"
            value={`${summary.total_time_saved_hours.toLocaleString()}h`}
            sub={`${(summary.total_time_saved_hours / (summary.period_days || 1)).toFixed(1)}h/day avg`}
            color="text-cyan-400"
          />
        </div>
      )}

      {/* ROI Over Time */}
      <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h2 className="text-sm font-semibold text-gray-400 mb-4">Daily ROI vs Cost</h2>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={daily}>
            <defs>
              <linearGradient id="roi" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="cost" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={d => d.slice(5)} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={v => `$${v}`} />
            <Tooltip
              contentStyle={{ background: '#111827', border: '1px solid #374151' }}
              formatter={(v, name) => [`$${v.toFixed(2)}`, name]}
            />
            <Legend />
            <Area type="monotone" dataKey="value_usd" name="Value" stroke="#6366f1" fill="url(#roi)" strokeWidth={2} />
            <Area type="monotone" dataKey="cost_usd" name="Cost" stroke="#f97316" fill="url(#cost)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* By Source + By Department */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h2 className="text-sm font-semibold text-gray-400 mb-4">ROI by AI Source</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sourceData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={v => `$${v}`} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#9ca3af' }} width={70} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151' }}
                formatter={(v, name) => [`$${v.toFixed(2)}`, name]}
              />
              <Bar dataKey="value" name="Value" fill="#6366f1" radius={[0, 4, 4, 0]} />
              <Bar dataKey="cost" name="Cost" fill="#f97316" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h2 className="text-sm font-semibold text-gray-400 mb-4">Value by Department</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={depts} dataKey="value_usd" nameKey="department" cx="50%" cy="50%" outerRadius={80} label={({ department, percent }) => `${department} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {depts.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151' }}
                formatter={(v) => [`$${v.toFixed(2)}`, 'Value']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* By Task Type */}
      <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h2 className="text-sm font-semibold text-gray-400 mb-4">ROI by Task Type</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={tasks}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="task_type" tick={{ fontSize: 11, fill: '#9ca3af' }} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={v => `$${v}`} />
            <Tooltip
              contentStyle={{ background: '#111827', border: '1px solid #374151' }}
              formatter={(v, name) => [`$${v.toFixed(2)}`, name]}
            />
            <Legend />
            <Bar dataKey="value_usd" name="Value" fill="#22d3ee" radius={[4, 4, 0, 0]} />
            <Bar dataKey="cost_usd" name="Cost" fill="#f97316" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
