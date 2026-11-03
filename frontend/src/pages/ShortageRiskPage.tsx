import React from 'react'
import {
  Info,
  Scale
} from 'lucide-react'
import type { WaterBalance, VillageMeta } from '../types'
import { formatLitres, formatPercentage, getRiskBadgeClasses } from '../utils/formatters'

interface ShortageRiskPageProps {
  waterBalance: WaterBalance
  selectedVillage?: VillageMeta
}

export const ShortageRiskPage: React.FC<ShortageRiskPageProps> = ({
  waterBalance,
  selectedVillage
}) => {
  const isDeficit = waterBalance.deficit_litres > 0
  const prob = waterBalance.shortage_probability_pct
  const badge = getRiskBadgeClasses(waterBalance.risk_category)

  return (
    <div className="space-y-5 pb-8">
      {/* Top Hero Card */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                Stochastic Margin Model
              </span>
              <span className="text-xs text-[#64748B]">• Probabilistic Deficit Formulation</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#16324F] mt-1">
              Shortage Risk & Water Vulnerability Assessment
            </h2>
            <p className="text-xs text-[#64748B] mt-0.5 max-w-3xl leading-relaxed">
              Formulated as a Gaussian stochastic margin: <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-[#0B78B5]">M = [S + α·B] - D</code> where S is baseline supply, B is overhead buffer storage, and D is predicted consumption. Deficit probability is given by <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-[#0B78B5]">P(Shortage) = Φ(-μ_M / σ_M)</code>.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] font-bold uppercase text-[#64748B] block">Assessed Habitation</span>
              <span className="font-bold text-[#16324F] text-sm">{selectedVillage?.name || 'Selected Village'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Assessment Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Visual Probability Gauge */}
        <div className="lg:col-span-5">
          <div className="card-base p-6 text-center h-full flex flex-col justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#64748B] block mb-1">
                Shortage Probability
              </span>

              {/* Large Circular / Arc Display */}
              <div className="relative w-48 h-48 mx-auto my-4 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  {/* Track */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="#F1F5F9"
                    strokeWidth="10"
                  />
                  {/* Progress Arc */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke={
                      prob > 50
                        ? '#DC2626'
                        : prob > 25
                        ? '#EA580C'
                        : prob > 10
                        ? '#D97706'
                        : '#15803D'
                    }
                    strokeWidth="10"
                    strokeDasharray={`${2 * Math.PI * 40}`}
                    strokeDashoffset={`${2 * Math.PI * 40 * (1 - prob / 100)}`}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>

                {/* Inner Content */}
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold font-mono text-[#16324F]">
                    {formatPercentage(prob)}
                  </span>
                  <span
                    className={`mt-1 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase border ${badge.bg} ${badge.text} ${badge.border}`}
                  >
                    <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
                    {waterBalance.risk_category} Risk
                  </span>
                </div>
              </div>

              {/* Stochastic Description */}
              <p className="text-xs text-[#16324F] font-medium px-4 mt-2 leading-relaxed">
                {waterBalance.risk_description}
              </p>
            </div>

            {/* Threshold Reference */}
            <div className="pt-4 border-t border-[#F1F5F9] mt-4 grid grid-cols-4 gap-1 text-[10px] text-[#64748B]">
              <div className="p-1 bg-emerald-50 rounded border border-emerald-100 text-emerald-800 font-bold">
                &lt;10% Low
              </div>
              <div className="p-1 bg-amber-50 rounded border border-amber-100 text-amber-800 font-bold">
                10-25% Mod
              </div>
              <div className="p-1 bg-orange-50 rounded border border-orange-100 text-orange-800 font-bold">
                25-50% High
              </div>
              <div className="p-1 bg-red-50 rounded border border-red-100 text-red-800 font-bold">
                &gt;50% Crit
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Detailed Metrics & Explanation */}
        <div className="lg:col-span-7 space-y-4">
          {/* Volumetrics Grid */}
          <div className="card-base p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#64748B] mb-3 flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5 text-[#0B78B5]" />
              Hydrological Balance Variables
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3">
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">Predicted Demand</span>
                <span className="text-base font-extrabold font-mono text-[#0B78B5]">
                  {formatLitres(waterBalance.predicted_demand_litres, true)}
                </span>
                <span className="text-[10px] text-[#64748B] block">{waterBalance.predicted_lpcd} LPCD</span>
              </div>

              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3">
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">Available Supply</span>
                <span className="text-base font-extrabold font-mono text-[#0D9488]">
                  {formatLitres(waterBalance.estimated_supply_litres, true)}
                </span>
                <span className="text-[10px] text-[#64748B] block">{waterBalance.supply_lpcd} LPCD</span>
              </div>

              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3">
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">Net Balance</span>
                <span className={`text-base font-extrabold font-mono ${isDeficit ? 'text-red-600' : 'text-emerald-700'}`}>
                  {isDeficit ? `-${formatLitres(waterBalance.deficit_litres, true)}` : `+${formatLitres(waterBalance.surplus_litres, true)}`}
                </span>
                <span className="text-[10px] text-[#64748B] block">{isDeficit ? 'Deficit' : 'Surplus'}</span>
              </div>

              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3">
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">Coverage Ratio</span>
                <span className="text-base font-extrabold font-mono text-[#16324F]">
                  {formatPercentage(waterBalance.coverage_percentage)}
                </span>
                <span className="text-[10px] text-[#64748B] block">Demand Satisfaction</span>
              </div>

              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3">
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">Municipal Tankers</span>
                <span className={`text-base font-extrabold font-mono ${isDeficit ? 'text-red-700' : 'text-[#64748B]'}`}>
                  {waterBalance.tankers_needed} Units
                </span>
                <span className="text-[10px] text-[#64748B] block">10,000L Standard</span>
              </div>

              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3">
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">JJM Benchmark</span>
                <span className="text-base font-extrabold font-mono text-[#16324F]">55.0 LPCD</span>
                <span className="text-[10px] text-[#64748B] block">Ministry Mandate</span>
              </div>
            </div>

            {/* Plain-Language Automated Explanation */}
            <div className="mt-4 pt-3 border-t border-[#F1F5F9] text-xs leading-relaxed text-[#16324F]">
              <div className="font-bold text-[#0B78B5] mb-1">Hydrological Assessment Rationale:</div>
              {isDeficit ? (
                <p>
                  Projected village consumption ({formatLitres(waterBalance.predicted_demand_litres)}) exceeds available municipal pumping capacity ({formatLitres(waterBalance.estimated_supply_litres)}), creating an immediate deficit of <strong>{formatLitres(waterBalance.deficit_litres)}</strong> ({formatPercentage(waterBalance.coverage_percentage)} coverage). Under Gaussian stochastic variance, the probability of complete reservoir exhaustion reaches <strong>{formatPercentage(prob)}</strong>. Immediate contingency deployment of <strong>{waterBalance.tankers_needed} tanker(s)</strong> is recommended.
                </p>
              ) : (
                <p>
                  Current estimated supply yield ({formatLitres(waterBalance.estimated_supply_litres)}) comfortably satisfies predicted next-day consumption ({formatLitres(waterBalance.predicted_demand_litres)}), maintaining a healthy surplus reserve buffer of <strong>+{formatLitres(waterBalance.surplus_litres)}</strong>. The calculated shortage risk is minimal at <strong>{formatPercentage(prob)}</strong>. Routine scheduled pumping is adequate.
                </p>
              )}
            </div>
          </div>

          {/* Operational Recommendation Card */}
          <div className="card-base p-5 border-l-4 border-l-[#0B78B5]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#64748B]">
                Decision-Support Directive
              </span>
              <span className="text-[10px] font-bold text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                Non-Statutory Decision Support
              </span>
            </div>

            <div className="text-sm font-bold text-[#16324F] leading-snug">
              {waterBalance.primary_recommendation}
            </div>

            <div className="pt-3 border-t border-[#F1F5F9] mt-3 text-[11px] text-[#64748B] leading-tight flex items-start gap-1.5">
              <Info className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" />
              <span>{waterBalance.disclaimer}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
