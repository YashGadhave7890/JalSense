import React, { useState } from 'react'
import {
  TrendingUp,
  Droplet,
  ShieldCheck,
  Truck,
  Activity,
  Calendar,
  AlertTriangle,
  Lightbulb
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts'
import type { PredictDemandResponse, HistoricalRecord, VillageMeta } from '../types'
import { DecisionBanner } from '../components/DecisionBanner'
import { KpiCard } from '../components/KpiCard'
import { WaterBalanceBar } from '../components/WaterBalanceBar'
import { WeatherStrip } from '../components/WeatherStrip'
import { StudyAreaDisclaimer } from '../components/StudyAreaDisclaimer'
import { formatLitres, formatPercentage } from '../utils/formatters'

interface OverviewPageProps {
  prediction: PredictDemandResponse
  historicalRecords: HistoricalRecord[]
  selectedVillage?: VillageMeta
  isLoading: boolean
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  prediction,
  historicalRecords,
  selectedVillage,
  isLoading
}) => {
  const [historyRange, setHistoryRange] = useState<7 | 14 | 30 | 45>(30)

  const wb = prediction.water_balance
  const isDeficit = wb.deficit_litres > 0

  // Filter historical data by range
  const filteredHistory = historicalRecords.slice(-historyRange)

  // Calculate historical stats
  const historyDemands = filteredHistory.map((h) => h.water_demand_litres)
  const histAvg = historyDemands.length ? Math.round(historyDemands.reduce((a, b) => a + b, 0) / historyDemands.length) : 0
  const histMin = historyDemands.length ? Math.round(Math.min(...historyDemands)) : 0
  const histMax = historyDemands.length ? Math.round(Math.max(...historyDemands)) : 0

  return (
    <div className="space-y-5 pb-8">
      {/* 1. Academic Disclaimer */}
      <StudyAreaDisclaimer selectedVillage={selectedVillage} />

      {/* 2. Primary Decision Banner (Dominates Screen) */}
      <DecisionBanner waterBalance={wb} />

      {/* 3. 4 Compact KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Predicted Demand"
          sublabel="Next Day Volume"
          value={formatLitres(wb.predicted_demand_litres, true)}
          contextText={`${wb.predicted_lpcd} LPCD (JJM Norm: 55 LPCD)`}
          badgeText="Tomorrow"
          badgeVariant="info"
          valueColorClass="text-[#0B78B5]"
          icon={Droplet}
        />

        <KpiCard
          label="Available Supply"
          sublabel="Current Source Capacity"
          value={formatLitres(wb.estimated_supply_litres, true)}
          contextText={`${wb.supply_lpcd} LPCD Sustainable Yield`}
          badgeText="Yield"
          badgeVariant="safe"
          valueColorClass="text-[#0D9488]"
          icon={Activity}
        />

        <KpiCard
          label="Water Balance"
          sublabel={isDeficit ? 'Unfulfilled Deficit' : 'Operational Surplus'}
          value={isDeficit ? `-${formatLitres(wb.deficit_litres, true)}` : `+${formatLitres(wb.surplus_litres, true)}`}
          contextText={`${formatPercentage(wb.coverage_percentage)} Supply Coverage`}
          badgeText={isDeficit ? 'Deficit' : 'Surplus'}
          badgeVariant={isDeficit ? 'danger' : 'safe'}
          valueColorClass={isDeficit ? 'text-red-600' : 'text-emerald-700'}
          icon={TrendingUp}
        />

        <KpiCard
          label="Shortage Probability"
          sublabel="Gaussian Stochastic Risk"
          value={formatPercentage(wb.shortage_probability_pct)}
          contextText={`${wb.risk_category} Risk Category`}
          badgeText={`${wb.risk_category} Risk`}
          badgeVariant={isDeficit || wb.risk_category === 'CRITICAL' ? 'danger' : wb.risk_category === 'MODERATE' ? 'warning' : 'safe'}
          valueColorClass={wb.shortage_probability_pct > 25 ? 'text-red-600' : 'text-[#16324F]'}
          icon={ShieldCheck}
        />
      </div>

      {/* 4. Water Balance & Decision Advisory Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7">
          <WaterBalanceBar waterBalance={wb} />
        </div>

        <div className="lg:col-span-5">
          <div className="card-base p-5 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4 text-[#0B78B5]" />
                <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide">
                  Decision-Support Advisory
                </h3>
              </div>
              <p className="text-xs text-[#64748B] mb-3">
                System-generated operational recommendation for Gram Panchayat water logistics.
              </p>

              {/* Main Action Box */}
              <div className="bg-[#F8FAFC] border-l-4 border-[#0B78B5] p-3.5 rounded-r-lg text-xs leading-relaxed text-[#16324F] font-medium mb-3">
                {wb.primary_recommendation}
              </div>

              {/* Tanker Logistics Box */}
              {isDeficit ? (
                <div className="bg-red-50/70 border border-red-200 rounded-lg p-3 text-xs flex items-center justify-between text-red-900">
                  <div className="flex items-center gap-2">
                    <Truck className="w-4 h-4 text-red-600 shrink-0" />
                    <span>Emergency Tankers Needed:</span>
                  </div>
                  <span className="font-mono font-extrabold text-sm text-red-700">
                    {wb.tankers_needed} unit(s) (10,000L)
                  </span>
                </div>
              ) : (
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-lg p-3 text-xs flex items-center justify-between text-emerald-900">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Reserve Buffer Status:</span>
                  </div>
                  <span className="font-mono font-bold text-emerald-700">
                    +{formatLitres(wb.surplus_litres, true)} Safe Buffer
                  </span>
                </div>
              )}
            </div>

            {/* Advisory Disclaimer */}
            <div className="pt-3 border-t border-[#F1F5F9] mt-3">
              <span className="text-[11px] text-[#64748B] leading-tight flex items-start gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                <span>{wb.disclaimer}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Historical Consumption Timeline & Selector */}
      <div className="card-base p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#0B78B5]" />
              Recent Water Consumption & Available Supply Timeline
            </h3>
            <p className="text-xs text-[#64748B]">
              Continuous telemetry observations showing daily village consumption vs available source capacity.
            </p>
          </div>

          {/* Range Selector & Summary Chips */}
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-[#F1F5F9] rounded-lg p-0.5 border border-slate-200 text-xs">
              {([7, 14, 30, 45] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setHistoryRange(r)}
                  className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
                    historyRange === r ? 'bg-white text-[#0B78B5] shadow-2xs font-bold' : 'text-[#64748B] hover:text-[#16324F]'
                  }`}
                >
                  {r}D
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Range Metric Cards */}
        <div className="grid grid-cols-3 gap-3 mb-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-2.5 text-xs">
          <div>
            <span className="text-[#64748B] text-[10px] uppercase font-bold block">{historyRange}-Day Mean Demand</span>
            <span className="font-mono font-bold text-[#16324F] text-sm">{formatLitres(histAvg, true)}</span>
          </div>
          <div className="border-l border-slate-200 pl-3">
            <span className="text-[#64748B] text-[10px] uppercase font-bold block">Minimum Observation</span>
            <span className="font-mono font-bold text-emerald-700 text-sm">{formatLitres(histMin, true)}</span>
          </div>
          <div className="border-l border-slate-200 pl-3">
            <span className="text-[#64748B] text-[10px] uppercase font-bold block">Peak Observation</span>
            <span className="font-mono font-bold text-amber-700 text-sm">{formatLitres(histMax, true)}</span>
          </div>
        </div>

        {/* Recharts Historical Timeline */}
        <div className="h-64 sm:h-72 w-full">
          {filteredHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filteredHistory} margin={{ top: 10, right: 15, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#64748B' }}
                  tickFormatter={(val) => {
                    const parts = val.split('-')
                    return parts.length >= 3 ? `${parts[2]}/${parts[1]}` : val
                  }}
                  stroke="#CBD5E1"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748B' }}
                  tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                  stroke="#CBD5E1"
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  formatter={(val: any, name: any) => [
                    `${Number(val).toLocaleString()} L`,
                    name === 'water_demand_litres' ? 'Actual Demand' : 'Source Yield'
                  ]}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E2E8F0',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.07)'
                  }}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  wrapperStyle={{ fontSize: '11px', paddingBottom: '8px' }}
                />
                <Line
                  type="monotone"
                  dataKey="water_demand_litres"
                  name="Daily Demand"
                  stroke="#0B78B5"
                  strokeWidth={2.2}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="daily_supply_litres"
                  name="Source Yield"
                  stroke="#0D9488"
                  strokeWidth={1.8}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-[#64748B]">
              {isLoading ? 'Synchronizing historical consumption records...' : 'No historical consumption data available.'}
            </div>
          )}
        </div>
      </div>

      {/* 6. Meteorological Telemetry Strip */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#0B78B5]" />
            Synchronized Weather Telemetry (Open-Meteo)
          </span>
          <span className="text-[11px] text-[#64748B]">Coordinates: {selectedVillage?.latitude ?? 18.91}°N, {selectedVillage?.longitude ?? 74.40}°E</span>
        </div>
        <WeatherStrip weather={prediction.weather} compact />
      </div>
    </div>
  )
}
