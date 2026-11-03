import React from 'react'
import { CheckCircle2, AlertTriangle, AlertCircle, ShieldX } from 'lucide-react'
import type { WaterBalance } from '../types'
import { formatLitres, formatPercentage } from '../utils/formatters'

interface DecisionBannerProps {
  waterBalance: WaterBalance
}

export const DecisionBanner: React.FC<DecisionBannerProps> = ({ waterBalance }) => {
  const isDeficit = waterBalance.deficit_litres > 0
  const risk = (waterBalance.risk_category || 'LOW').toUpperCase()

  let bannerConfig = {
    title: 'WATER SUPPLY SUFFICIENT',
    icon: CheckCircle2,
    bg: 'bg-emerald-50/80',
    border: 'border-emerald-300',
    borderLeft: 'border-l-emerald-600',
    textColor: 'text-emerald-900',
    headlineColor: 'text-emerald-800',
    desc: `Available yield exceeds next-day predicted consumption with a surplus buffer of +${formatLitres(waterBalance.surplus_litres)}. Normal water distribution operations.`
  }

  if (risk === 'CRITICAL') {
    bannerConfig = {
      title: 'CRITICAL WATER SHORTAGE RISK',
      icon: ShieldX,
      bg: 'bg-red-50/90',
      border: 'border-red-300',
      borderLeft: 'border-l-red-600',
      textColor: 'text-red-950',
      headlineColor: 'text-red-800',
      desc: `Critical water deficit of ${formatLitres(waterBalance.deficit_litres)} detected. Available supply meets only ${waterBalance.coverage_percentage}%. Immediate municipal tanker requisitions required.`
    }
  } else if (risk === 'HIGH') {
    bannerConfig = {
      title: 'SHORTAGE RISK HIGH',
      icon: AlertCircle,
      bg: 'bg-orange-50/90',
      border: 'border-orange-300',
      borderLeft: 'border-l-orange-600',
      textColor: 'text-orange-950',
      headlineColor: 'text-orange-800',
      desc: `High shortage vulnerability (${waterBalance.shortage_probability_pct}% probability). Water deficit of ${formatLitres(waterBalance.deficit_litres)}. Review secondary pumping and rotational supply.`
    }
  } else if (risk === 'MODERATE') {
    bannerConfig = {
      title: 'MONITOR WATER BALANCE (MODERATE WARNING)',
      icon: AlertTriangle,
      bg: 'bg-amber-50/90',
      border: 'border-amber-300',
      borderLeft: 'border-l-amber-500',
      textColor: 'text-amber-950',
      headlineColor: 'text-amber-800',
      desc: `Supply coverage is marginal (${waterBalance.coverage_percentage}%). Monitor overhead storage levels closely and prepare reserve pumps for potential demand surges.`
    }
  }

  const Icon = bannerConfig.icon

  return (
    <div
      className={`border ${bannerConfig.border} ${bannerConfig.bg} border-l-6 ${bannerConfig.borderLeft} rounded-xl p-4 sm:p-5 mb-5 shadow-xs`}
    >
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Headline & Explanation */}
        <div className="flex items-start gap-3.5 max-w-2xl">
          <div className="p-2 rounded-lg bg-white shadow-2xs shrink-0 mt-0.5">
            <Icon className={`w-6 h-6 ${bannerConfig.headlineColor}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
                Water Security Status
              </span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full bg-white border ${bannerConfig.border}`}>
                {risk} Risk
              </span>
            </div>
            <h2 className={`text-lg sm:text-xl font-extrabold tracking-tight ${bannerConfig.headlineColor} mt-0.5`}>
              {bannerConfig.title}
            </h2>
            <p className="text-xs sm:text-sm text-[#16324F] font-medium mt-1 leading-relaxed">
              {bannerConfig.desc}
            </p>
          </div>
        </div>

        {/* Right: Inline Key Volumetrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-white/90 rounded-lg p-3 border border-[#E2E8F0] shadow-2xs shrink-0">
          <div className="text-left px-2">
            <span className="text-[10px] font-bold uppercase text-[#64748B] block">Demand</span>
            <span className="text-sm sm:text-base font-extrabold font-mono text-[#16324F]">
              {formatLitres(waterBalance.predicted_demand_litres, true)}
            </span>
            <span className="text-[10px] text-[#64748B] block">{waterBalance.predicted_lpcd} LPCD</span>
          </div>

          <div className="text-left px-2 border-l border-slate-100">
            <span className="text-[10px] font-bold uppercase text-[#64748B] block">Supply</span>
            <span className="text-sm sm:text-base font-extrabold font-mono text-[#0D9488]">
              {formatLitres(waterBalance.estimated_supply_litres, true)}
            </span>
            <span className="text-[10px] text-[#64748B] block">{waterBalance.supply_lpcd} LPCD</span>
          </div>

          <div className="text-left px-2 border-l border-slate-100">
            <span className="text-[10px] font-bold uppercase text-[#64748B] block">Balance</span>
            <span
              className={`text-sm sm:text-base font-extrabold font-mono ${
                isDeficit ? 'text-red-600' : 'text-emerald-700'
              }`}
            >
              {isDeficit ? `-${formatLitres(waterBalance.deficit_litres, true)}` : `+${formatLitres(waterBalance.surplus_litres, true)}`}
            </span>
            <span className="text-[10px] text-[#64748B] block">{isDeficit ? 'Deficit' : 'Surplus'}</span>
          </div>

          <div className="text-left px-2 border-l border-slate-100">
            <span className="text-[10px] font-bold uppercase text-[#64748B] block">Shortage Prob</span>
            <span
              className={`text-sm sm:text-base font-extrabold font-mono ${
                waterBalance.shortage_probability_pct > 25 ? 'text-red-600' : 'text-[#16324F]'
              }`}
            >
              {formatPercentage(waterBalance.shortage_probability_pct)}
            </span>
            <span className="text-[10px] text-[#64748B] block">{waterBalance.coverage_percentage}% Cover</span>
          </div>
        </div>
      </div>
    </div>
  )
}
