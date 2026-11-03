import React from 'react'
import {
  LayoutDashboard,
  TrendingUp,
  ShieldAlert,
  CloudSun,
  SlidersHorizontal,
  Award,
  Database,
  BotMessageSquare,
  Droplet,
  ChevronLeft,
  ChevronRight,
  Server,
  Cpu,
  Layers
} from 'lucide-react'

export type PageId =
  | 'overview'
  | 'forecast'
  | 'shortage'
  | 'weather'
  | 'simulator'
  | 'performance'
  | 'provenance'
  | 'assistant'

interface SidebarProps {
  currentPage: PageId
  onSelectPage: (page: PageId) => void
  isCollapsed: boolean
  onToggleCollapse: () => void
  backendHealthy: boolean
  championModel?: string
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  isCollapsed,
  onToggleCollapse,
  backendHealthy,
  championModel = 'XGBoost Regressor'
}) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', number: '01', icon: LayoutDashboard },
    { id: 'forecast' as PageId, label: 'Demand Forecast', number: '02', icon: TrendingUp },
    { id: 'shortage' as PageId, label: 'Shortage Risk', number: '03', icon: ShieldAlert },
    { id: 'weather' as PageId, label: 'Weather Intelligence', number: '04', icon: CloudSun },
    { id: 'simulator' as PageId, label: 'Scenario Simulator', number: '05', icon: SlidersHorizontal },
    { id: 'performance' as PageId, label: 'Model Performance', number: '06', icon: Award },
    { id: 'provenance' as PageId, label: 'Data & Provenance', number: '07', icon: Database },
    { id: 'assistant' as PageId, label: 'AI Assistant', number: '08', icon: BotMessageSquare }
  ]

  return (
    <aside
      className={`bg-white border-r border-[#E2E8F0] flex flex-col transition-all duration-200 shrink-0 select-none z-20 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#E2E8F0]">
        {!isCollapsed ? (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-[#0B78B5] text-white flex items-center justify-center font-bold text-lg shadow-sm shrink-0">
              <Droplet className="w-5 h-5 fill-white" />
            </div>
            <div className="leading-tight">
              <div className="font-extrabold text-[#16324F] text-base tracking-tight flex items-center gap-1.5">
                JalSense
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-50 text-[#0B78B5] border border-blue-200">
                  v2.0
                </span>
              </div>
              <div className="text-[11px] text-[#64748B] font-medium truncate">Water Intelligence</div>
            </div>
          </div>
        ) : (
          <div className="mx-auto w-8 h-8 rounded-lg bg-[#0B78B5] text-white flex items-center justify-center font-bold shadow-sm">
            <Droplet className="w-5 h-5 fill-white" />
          </div>
        )}

        <button
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="text-[#64748B] hover:text-[#16324F] hover:bg-[#F1F5F9] p-1.5 rounded-md transition-colors"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {!isCollapsed && (
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-[#94A3B8]">
            Decision Modules
          </div>
        )}

        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              title={isCollapsed ? `${item.number} ${item.label}` : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 text-left ${
                isActive
                  ? 'bg-[#0B78B5] text-white shadow-sm'
                  : 'text-[#16324F] hover:bg-[#F5F8FC] hover:text-[#0B78B5]'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#64748B]'}`} />
              {!isCollapsed && (
                <div className="flex items-center justify-between flex-1 truncate">
                  <span className="truncate">{item.label}</span>
                  <span
                    className={`text-[10px] font-mono font-medium ml-2 px-1.5 py-0.5 rounded ${
                      isActive ? 'bg-white/20 text-white' : 'text-[#94A3B8] bg-slate-100'
                    }`}
                  >
                    {item.number}
                  </span>
                </div>
              )}
            </button>
          )
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-3 border-t border-[#E2E8F0] bg-[#FAFCFF] text-xs">
        {!isCollapsed ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#64748B] flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5" /> Backend
              </span>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[10px] ${
                  backendHealthy
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${backendHealthy ? 'bg-emerald-600' : 'bg-amber-600 animate-pulse'}`}
                />
                {backendHealthy ? 'Operational' : 'Connecting'}
              </span>
            </div>

            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#64748B] flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Model
              </span>
              <span className="font-mono text-[#16324F] font-semibold truncate max-w-[120px]" title={championModel}>
                {championModel.split(' ')[0]}
              </span>
            </div>

            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#64748B] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" /> JJM Standard
              </span>
              <span className="font-mono text-[#16324F] font-semibold">55.0 LPCD</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title={backendHealthy ? 'Backend Operational' : 'Backend Connecting'}>
            <span
              className={`w-2.5 h-2.5 rounded-full ${backendHealthy ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}
            />
          </div>
        )}
      </div>
    </aside>
  )
}
