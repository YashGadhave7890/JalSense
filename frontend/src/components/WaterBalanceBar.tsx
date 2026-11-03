import React from 'react'
import type { WaterBalance } from '../types'
import { formatLitres, formatPercentage } from '../utils/formatters'

interface WaterBalanceBarProps {
  waterBalance: WaterBalance
}

export const WaterBalanceBar: React.FC<WaterBalanceBarProps> = ({ waterBalance }) => {
  const isDeficit = waterBalance.deficit_litres > 0
  const maxVal = Math.max(waterBalance.predicted_demand_litres, waterBalance.estimated_supply_litres) * 1.08 || 1

  const supplyPct = Math.min(100, Math.round((waterBalance.estimated_supply_litres / maxVal) * 100))
  const demandPct = Math.min(100, Math.round((waterBalance.predicted_demand_litres / maxVal) * 100))

  return (
    <div className="card-base p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide">
            ⚖️ Water Balance: Available Supply vs Predicted Demand
          </h3>
          <p className="text-xs text-[#64748B]">
            Direct horizontal volumetric contrast with functional Jal Jeevan Mission benchmarks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-md border ${
              waterBalance.coverage_percentage >= 100
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            Supply Coverage: {formatPercentage(waterBalance.coverage_percentage)}
          </span>
        </div>
      </div>

      {/* Bars Container */}
      <div className="space-y-3.5 my-3">
        {/* Available Supply Bar */}
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-semibold text-[#16324F] flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0D9488]" />
              Available Source Yield
            </span>
            <span className="font-mono font-bold text-[#0D9488]">
              {formatLitres(waterBalance.estimated_supply_litres)} ({waterBalance.supply_lpcd} LPCD)
            </span>
          </div>
          <div className="w-full bg-[#F1F5F9] h-5 rounded-md overflow-hidden relative border border-slate-200/60">
            <div
              className="bg-[#0D9488] h-full rounded-md transition-all duration-500 flex items-center justify-end pr-2"
              style={{ width: `${supplyPct}%` }}
            >
              <span className="text-[10px] font-bold text-white tracking-wide">
                {formatLitres(waterBalance.estimated_supply_litres, true)}
              </span>
            </div>
          </div>
        </div>

        {/* Predicted Demand Bar */}
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-semibold text-[#16324F] flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0B78B5]" />
              Predicted Next-Day Demand
            </span>
            <span className="font-mono font-bold text-[#0B78B5]">
              {formatLitres(waterBalance.predicted_demand_litres)} ({waterBalance.predicted_lpcd} LPCD)
            </span>
          </div>
          <div className="w-full bg-[#F1F5F9] h-5 rounded-md overflow-hidden relative border border-slate-200/60">
            <div
              className="bg-[#0B78B5] h-full rounded-md transition-all duration-500 flex items-center justify-end pr-2"
              style={{ width: `${demandPct}%` }}
            >
              <span className="text-[10px] font-bold text-white tracking-wide">
                {formatLitres(waterBalance.predicted_demand_litres, true)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Metrics Strip */}
      <div className="pt-3 border-t border-[#F1F5F9] mt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-[#64748B]">Net Water Balance:</span>
          <span className={`font-mono font-bold ${isDeficit ? 'text-red-600' : 'text-emerald-700'}`}>
            {isDeficit ? `Deficit: -${formatLitres(waterBalance.deficit_litres)}` : `Surplus: +${formatLitres(waterBalance.surplus_litres)}`}
          </span>
        </div>

        <div className="flex items-center gap-2 text-[#64748B]">
          <span>JJM National Norm: <strong>55.0 LPCD</strong></span>
          <span className="text-slate-300">•</span>
          <span>
            Actual vs Norm:{' '}
            <strong className="text-[#16324F]">
              {(waterBalance.predicted_lpcd / 55.0).toFixed(2)}x
            </strong>
          </span>
        </div>
      </div>
    </div>
  )
}
