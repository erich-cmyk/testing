export default function StatCard({ label, value, sub, color = 'text-white', icon }) {
  return (
    <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800 flex flex-col gap-1">
      <div className="flex items-center gap-2 text-gray-400 text-sm">
        {icon && <span>{icon}</span>}
        {label}
      </div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-gray-500 text-xs">{sub}</div>}
    </div>
  )
}
