import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import LogEvent from './pages/LogEvent'
import Events from './pages/Events'
import Integrations from './pages/Integrations'

const NAV = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'log', label: 'Log Event' },
  { id: 'events', label: 'Events' },
  { id: 'integrations', label: 'Integrations' },
]

export default function App() {
  const [page, setPage] = useState('dashboard')

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <div className="fixed top-0 left-0 h-full w-52 bg-gray-900 border-r border-gray-800 flex flex-col py-6 px-4">
        <div className="mb-8">
          <div className="text-white font-bold text-lg">AI ROI</div>
          <div className="text-gray-500 text-xs">Tracker</div>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(n => (
            <button
              key={n.id}
              onClick={() => setPage(n.id)}
              className={`text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                page === n.id
                  ? 'bg-indigo-600 text-white font-medium'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {n.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto text-xs text-gray-600">v1.0.0</div>
      </div>

      {/* Main */}
      <div className="ml-52">
        {page === 'dashboard' && <Dashboard />}
        {page === 'log' && <LogEvent />}
        {page === 'events' && <Events />}
        {page === 'integrations' && <Integrations />}
      </div>
    </div>
  )
}
