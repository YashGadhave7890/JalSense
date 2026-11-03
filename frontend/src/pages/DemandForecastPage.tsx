import React from 'react'
import {
  TrendingUp,
  Calendar,
  AlertCircle,
  Activity,
  Layers,
  Thermometer,
  CloudRain
} from 'lucide-react'
import {
  ResponsiveContainer,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ComposedChart
} from 'recharts'
import type { MultiDayForecastResponse, VillageMeta } from '../types'
import { KpiCard } from '../components/KpiCard'
import { formatLitres, formatDate, getRiskBadgeClasses } from '../utils/formatters'

interface DemandForecastPageProps {
  forecastData?: MultiDayForecastResponse
  selectedVillage?: VillageMeta
  isLoading: boolean
}

export const DemandForecastPage: React.FC<DemandForecastPageProps> = ({
  forecastData,
  selectedVillage,
  isLoading
}) => {
  if (isLoading || !forecastData) {
    return (
      <div className="card-base p-12 text-center text-[#64748B]">
        <Activity className="w-8 h-8 animate-spin text-[#0B78B5] mx-auto mb-3" />
        <div className="font-semibold text-[#16324F]">Calculating 7-Day Forward Forecast...</div>
        <div className="text-xs mt-1">Propagating autoregressive dynamic lags and synchronizing Open-Meteo weather.</div>
      </div>
    )
  }

  const forecasts = forecastData.forecasts || []
  const demands = forecasts.map((f) => f.predicted_demand_litres)

  const dTomorrow = demands.length > 0 ? demands[0] : 0
  const dAvg = demands.length > 0 ? Math.round(demands.reduce((a, b) => a + b, 0) / demands.length) : 0
  const dPeak = demands.length > 0 ? Math.round(Math.max(...demands)) : 0

  return (
    <div className="space-y-5 pb-8">
      {/* Page Header Intro */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              Autoregressive Multi-Step Engine
            </span>
            <span className="text-xs text-[#64748B]">• 7-Day Forward Horizon</span>
          </div>
          <h2 className="text-lg sm:text-xl font-extrabold text-[#16324F] mt-1">
            7-Day Hydrological Water Demand Forecast
          </h2>
          <p className="text-xs text-[#64748B] mt-0.5 max-w-3xl leading-relaxed">
            Multi-step forecast recursively advancing dynamic lagged features (Lags 1, 2, 7) and rolling statistics coupled with multi-day Open-Meteo numerical weather predictions.
          </p>
        </div>

        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-2.5 text-xs text-right shrink-0">
          <span className="text-[#64748B] text-[10px] uppercase font-bold block">Habitation</span>
          <span className="font-bold text-[#16324F]">{selectedVillage?.name || forecastData.village_name}</span>
          <span className="text-[11px] text-[#0D9488] block font-mono">
            Cap: {formatLitres(selectedVillage?.avg_daily_supply_litres, true)}/day
          </span>
        </div>
      </div>

      {/* 3 Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard
          label="Tomorrow Demand"
          sublabel={forecasts[0]?.date ? `${forecasts[0].day_name} (${formatDate(forecasts[0].date)})` : 'Next Day'}
          value={formatLitres(dTomorrow, true)}
          contextText="Immediate operational requirement"
          badgeText="Day 1"
          badgeVariant="info"
          valueColorClass="text-[#0B78B5]"
          icon={Calendar}
        />

        <KpiCard
          label="7-Day Projected Average"
          sublabel="Mean Weekly Baseline"
          value={formatLitres(dAvg, true)}
          contextText="Weekly baseline demand volume"
          badgeText="Weekly Mean"
          badgeVariant="neutral"
          valueColorClass="text-[#16324F]"
          icon={TrendingUp}
        />

        <KpiCard
          label="Peak Expected Demand"
          sublabel="Single-Day Maximum Surge"
          value={formatLitres(dPeak, true)}
          contextText="Maximum stress point in forecast window"
          badgeText="Peak Surge"
          badgeVariant="warning"
          valueColorClass="text-amber-700"
          icon={AlertCircle}
        />
      </div>

      {/* 7-Day Composed Bar + Line Chart */}
      <div className="card-base p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#0B78B5]" />
              7-Day Volumetric Demand vs Sustainable Source Yield
            </h3>
            <p className="text-xs text-[#64748B]">
              Predicted water requirements (bars) compared directly against daily borewell & watershed yield (dashed line).
            </p>
          </div>
        </div>

        <div className="h-72 sm:h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={forecasts} margin={{ top: 15, right: 15, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#64748B' }}
                tickFormatter={(val, idx) => {
                  const day = forecasts[idx]?.day_name || ''
                  const parts = val.split('-')
                  return `${day.slice(0, 3)} ${parts[2]}/${parts[1]}`
                }}
                stroke="#CBD5E1"
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748B' }}
                tickFormatter={(val) => `${(val / 1000).toFixed(0)}k L`}
                stroke="#CBD5E1"
                domain={['auto', 'auto']}
              />
              <Tooltip
                formatter={(val: any, name: any) => [
                  `${Number(val).toLocaleString()} L`,
                  name === 'predicted_demand_litres' ? 'Predicted Demand' : 'Available Supply'
                ]}
                labelFormatter={(lbl, payload) => {
                  const item = payload[0]?.payload
                  return `${item?.day_name || ''}, ${lbl} • Temp: ${item?.temp_mean ?? 0}°C • Rain: ${item?.rainfall_mm ?? 0}mm`
                }}
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
                wrapperStyle={{ fontSize: '11px', paddingBottom: '10px' }}
              />
              <Bar
                dataKey="predicted_demand_litres"
                name="Predicted Demand"
                fill="#0B78B5"
                radius={[4, 4, 0, 0]}
                barSize={36}
              />
              <Line
                type="monotone"
                dataKey="estimated_supply_litres"
                name="Available Supply"
                stroke="#0D9488"
                strokeWidth={2.5}
                strokeDasharray="4 4"
                dot={{ r: 4, fill: '#0D9488' }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Forecast Breakdown Table */}
      <div className="card-base p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide">
            📋 Daily Forecast Breakdown & Risk Matrix
          </h3>
          <span className="text-xs text-[#64748B] font-mono">
            {forecasts.length} Forward Days
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="bg-[#F8FAFC] text-[#64748B] uppercase font-bold border-b border-[#E2E8F0]">
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Day</th>
                <th className="py-2.5 px-3 text-right">Weather</th>
                <th className="py-2.5 px-3 text-right">Demand (L)</th>
                <th className="py-2.5 px-3 text-right">Supply (L)</th>
                <th className="py-2.5 px-3 text-right">Balance</th>
                <th className="py-2.5 px-3 text-center">Risk Level</th>
                <th className="py-2.5 px-3 text-center">Tankers</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F1F5F9]">
              {forecasts.map((item, idx) => {
                const isDef = item.deficit_litres > 0
                const badge = getRiskBadgeClasses(item.risk_category)
                return (
                  <tr key={idx} className="hover:bg-[#F9FBFE] transition-colors">
                    <td className="py-3 px-3 font-mono font-medium text-[#16324F]">{item.date}</td>
                    <td className="py-3 px-3 font-semibold text-[#16324F]">{item.day_name}</td>
                    <td className="py-3 px-3 text-right text-[#64748B]">
                      <span className="inline-flex items-center gap-1">
                        <Thermometer className="w-3 h-3 text-amber-500" /> {item.temp_mean.toFixed(1)}°C
                      </span>
                      {item.rainfall_mm > 0 && (
                        <span className="ml-2 inline-flex items-center gap-1 text-cyan-600">
                          <CloudRain className="w-3 h-3" /> {item.rainfall_mm.toFixed(1)}mm
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-[#0B78B5]">
                      {Math.round(item.predicted_demand_litres).toLocaleString()} L
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-[#0D9488]">
                      {Math.round(item.estimated_supply_litres).toLocaleString()} L
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold">
                      <span className={isDef ? 'text-red-600' : 'text-emerald-700'}>
                        {isDef ? `-${Math.round(item.deficit_litres).toLocaleString()} L` : `+${Math.round(item.surplus_litres).toLocaleString()} L`}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${badge.bg} ${badge.text} ${badge.border}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                        {item.risk_category}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-bold">
                      {item.tankers_needed > 0 ? (
                        <span className="text-red-700 font-extrabold">{item.tankers_needed}</span>
                      ) : (
                        <span className="text-[#94A3B8]">0</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
