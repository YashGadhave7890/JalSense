import React from 'react'
import { MapPin, Users, Database, Clock, RefreshCw } from 'lucide-react'
import type { VillageMeta } from '../types'
import { formatLitres } from '../utils/formatters'

interface HeaderProps {
  pageTitle: string
  pageSubtitle: string
  villages: VillageMeta[]
  selectedVillageId: string
  onSelectVillage: (id: string) => void
  lastUpdated: string
  onRefresh: () => void
  isLoading: boolean
  backendHealthy: boolean
}

export const Header: React.FC<HeaderProps> = ({
  pageTitle,
  pageSubtitle,
  villages,
  selectedVillageId,
  onSelectVillage,
  lastUpdated,
  onRefresh,
  isLoading,
  backendHealthy
}) => {
  const selectedVillage = villages.find((v) => v.id === selectedVillageId) || villages[0]

  return (
    <header className="bg-white border-b border-[#E2E8F0] px-6 py-3.5 sticky top-0 z-10 shadow-xs">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        {/* Title & Subtitle */}
        <div>
          <h1 className="text-xl font-extrabold text-[#16324F] tracking-tight">{pageTitle}</h1>
          <p className="text-xs text-[#64748B] font-medium">{pageSubtitle}</p>
        </div>

        {/* Study Area Dropdown & Status Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Study Area Selector */}
          <div className="flex items-center gap-2 bg-[#F5F8FC] border border-[#CBD5E1] rounded-lg px-3 py-1.5 shadow-2xs">
            <MapPin className="w-4 h-4 text-[#0B78B5] shrink-0" />
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-bold text-[#64748B] leading-none">
                Study Habitation
              </span>
              <select
                value={selectedVillageId}
                onChange={(e) => onSelectVillage(e.target.value)}
                className="bg-transparent text-xs font-bold text-[#16324F] focus:outline-none cursor-pointer pr-1 py-0.5"
                disabled={isLoading}
              >
                {villages.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} ({v.state})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Quick Study Area Stats Pill */}
          {selectedVillage && (
            <div className="hidden xl:flex items-center gap-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-3 py-1.5 text-xs text-[#64748B]">
              <div className="flex items-center gap-1.5" title="Design Population">
                <Users className="w-3.5 h-3.5 text-[#0B78B5]" />
                <span>
                  Pop: <strong className="text-[#16324F] font-mono">{selectedVillage.base_population.toLocaleString()}</strong>
                </span>
              </div>
              <div className="w-px h-4 bg-slate-200" />
              <div className="flex items-center gap-1.5" title="Reservoir Capacity">
                <Database className="w-3.5 h-3.5 text-[#0D9488]" />
                <span>
                  Storage: <strong className="text-[#16324F] font-mono">{formatLitres(selectedVillage.storage_capacity_litres, true)}</strong>
                </span>
              </div>
            </div>
          )}

          {/* Refresh & Timestamp */}
          <div className="flex items-center gap-2 ml-auto lg:ml-0">
            <div className="hidden sm:flex items-center gap-1 text-[11px] text-[#64748B] font-mono">
              <Clock className="w-3.5 h-3.5 text-[#94A3B8]" />
              <span>{lastUpdated || 'Synchronized'}</span>
            </div>

            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh telemetry and forecasts"
              className="p-1.5 text-[#0B78B5] hover:bg-[#F0F7FF] active:bg-[#E0EFFE] rounded-md border border-blue-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-[#0B78B5]' : ''}`} />
            </button>

            {/* Live Operational Indicator */}
            <div
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                backendHealthy
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-amber-50 text-amber-800 border border-amber-200'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${backendHealthy ? 'bg-emerald-600' : 'bg-amber-500 animate-pulse'}`} />
              <span className="text-[11px] font-semibold">{backendHealthy ? 'Live Operational' : 'Connecting'}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
