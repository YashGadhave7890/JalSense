import React from 'react'
import { Info } from 'lucide-react'
import type { VillageMeta } from '../types'

interface StudyAreaDisclaimerProps {
  selectedVillage?: VillageMeta
}

export const StudyAreaDisclaimer: React.FC<StudyAreaDisclaimerProps> = ({ selectedVillage }) => {
  const villageName = selectedVillage ? selectedVillage.name : 'Configured Study Area'

  return (
    <div className="bg-blue-50/60 border border-blue-200/80 rounded-lg px-3.5 py-2 text-xs text-[#16324F] flex items-center justify-between gap-3 mb-4">
      <div className="flex items-center gap-2">
        <Info className="w-4 h-4 text-[#0B78B5] shrink-0" />
        <span className="font-semibold text-[#0B78B5]">
          Study Area: {villageName} — Demonstration Configuration
        </span>
        <span className="text-[#64748B] hidden md:inline">
          • Historical consumption model trained on public smart-meter data (LukaLike CC BY-SA 4.0); live weather synchronized for the configured study area.
        </span>
      </div>
      <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-white px-2 py-0.5 rounded border border-blue-200 shrink-0">
        Academic Integrity
      </span>
    </div>
  )
}
