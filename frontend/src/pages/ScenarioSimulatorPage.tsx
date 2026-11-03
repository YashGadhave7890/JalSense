import React, { useState } from 'react'
import {
  Play,
  RotateCcw,
  Users,
  Thermometer,
  Activity,
  ShieldCheck,
  AlertTriangle,
  Lightbulb,
  Truck
} from 'lucide-react'
import type { VillageMeta, ScenarioSimulationResponse } from '../types'
import { api } from '../services/api'
import { KpiCard } from '../components/KpiCard'
import { formatLitres, formatPercentage, formatTemperature } from '../utils/formatters'

interface ScenarioSimulatorPageProps {
  selectedVillage?: VillageMeta
  initialWeather?: {
    temp_mean_celsius?: number
    rainfall_mm?: number
    humidity_pct?: number
  }
}

export const ScenarioSimulatorPage: React.FC<ScenarioSimulatorPageProps> = ({
  selectedVillage,
  initialWeather
}) => {
  // Baseline initial state
  const basePop = selectedVillage?.base_population ?? 2450
  const baseSupply = selectedVillage?.avg_daily_supply_litres ?? 150000
  const baseStorage = selectedVillage?.storage_capacity_litres ?? 170000
  const baseTemp = initialWeather?.temp_mean_celsius ?? 28.0
  const baseRain = initialWeather?.rainfall_mm ?? 0.0
  const baseHum = initialWeather?.humidity_pct ?? 50.0

  // Interactive Form State
  const [pop, setPop] = useState<number>(basePop)
  const [supply, setSupply] = useState<number>(baseSupply)
  const [storage, setStorage] = useState<number>(Math.round(baseStorage * 0.5))
  const [temp, setTemp] = useState<number>(baseTemp)
  const [rain, setRain] = useState<number>(baseRain)
  const [hum, setHum] = useState<number>(baseHum)

  const [isSimulating, setIsSimulating] = useState<boolean>(false)
  const [simResult, setSimResult] = useState<ScenarioSimulationResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleReset = () => {
    setPop(basePop)
    setSupply(baseSupply)
    setStorage(Math.round(baseStorage * 0.5))
    setTemp(baseTemp)
    setRain(baseRain)
    setHum(baseHum)
    setSimResult(null)
    setErrorMsg(null)
  }

  const handleRunSimulation = async () => {
    setIsSimulating(true)
    setErrorMsg(null)
    try {
      const res = await api.simulateScenario({
        village_id: selectedVillage?.id ?? 'VILL001',
        population: pop,
        rainfall_mm: rain,
        temp_celsius: temp,
        water_supply_litres: supply,
        storage_capacity_litres: baseStorage,
        current_storage_litres: storage,
        humidity_pct: hum
      })
      setSimResult(res)
    } catch (err: any) {
      setErrorMsg(err.message || 'Simulation execution failed.')
    } finally {
      setIsSimulating(false)
    }
  }

  const wb = simResult?.shortage_assessment
  const isDeficit = wb ? wb.deficit_litres > 0 : false

  return (
    <div className="space-y-5 pb-8">
      {/* Top Banner */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                Stress-Testing Workbench
              </span>
              <span className="text-xs text-[#64748B]">• What-If Hydrological Scenarios</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#16324F] mt-1">
              Interactive Scenario Simulator
            </h2>
            <p className="text-xs text-[#64748B] mt-0.5 max-w-3xl leading-relaxed">
              Test how demographic surges, severe heatwaves (+3°C to +8°C), prolonged droughts, or pump infrastructure dropouts impact future village water security.
            </p>
          </div>

          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-[#64748B] hover:text-[#16324F] hover:bg-slate-50 transition-colors shrink-0"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset to Baseline
          </button>
        </div>
      </div>

      {/* 2-Column Input Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left Column: Demographics & Water Infrastructure */}
        <div className="card-base p-5 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-[#F1F5F9]">
            <Users className="w-4 h-4 text-[#0B78B5]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#16324F]">
              Demographics & Infrastructure Controls
            </h3>
          </div>

          {/* Population Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-[#16324F]">Village Population</span>
              <span className="font-mono font-bold text-[#0B78B5]">{pop.toLocaleString()} capita</span>
            </div>
            <input
              type="range"
              min={1000}
              max={8000}
              step={100}
              value={pop}
              onChange={(e) => setPop(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0B78B5]"
            />
            <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5 font-mono">
              <span>1,000</span>
              <span>Baseline: {basePop.toLocaleString()}</span>
              <span>8,000</span>
            </div>
          </div>

          {/* Daily Water Supply Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-[#16324F]">Available Daily Supply</span>
              <span className="font-mono font-bold text-[#0D9488]">{formatLitres(supply)}</span>
            </div>
            <input
              type="range"
              min={30000}
              max={400000}
              step={5000}
              value={supply}
              onChange={(e) => setSupply(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0D9488]"
            />
            <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5 font-mono">
              <span>30k L</span>
              <span>Baseline: {formatLitres(baseSupply, true)}</span>
              <span>400k L</span>
            </div>
          </div>

          {/* Overhead Storage Level Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-[#16324F]">Current Overhead Tank Buffer</span>
              <span className="font-mono font-bold text-indigo-700">{formatLitres(storage)}</span>
            </div>
            <input
              type="range"
              min={0}
              max={baseStorage}
              step={5000}
              value={storage}
              onChange={(e) => setStorage(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5 font-mono">
              <span>0 L (Dry)</span>
              <span>Capacity: {formatLitres(baseStorage, true)}</span>
              <span>Full Tank</span>
            </div>
          </div>
        </div>

        {/* Right Column: Climate Stress-Testing */}
        <div className="card-base p-5 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-[#F1F5F9]">
            <Thermometer className="w-4 h-4 text-amber-500" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#16324F]">
              Climate Stress Parameters
            </h3>
          </div>

          {/* Temperature Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-[#16324F]">Ambient Temperature</span>
              <span className="font-mono font-bold text-amber-700">{formatTemperature(temp)}</span>
            </div>
            <input
              type="range"
              min={18.0}
              max={48.0}
              step={0.5}
              value={temp}
              onChange={(e) => setTemp(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5 font-mono">
              <span>18 °C</span>
              <span>Baseline: {formatTemperature(baseTemp)}</span>
              <span>48 °C (Heatwave)</span>
            </div>
          </div>

          {/* Rainfall Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-[#16324F]">Rainfall / Precipitation</span>
              <span className="font-mono font-bold text-cyan-700">{rain.toFixed(1)} mm</span>
            </div>
            <input
              type="range"
              min={0.0}
              max={100.0}
              step={1.0}
              value={rain}
              onChange={(e) => setRain(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-cyan-600"
            />
            <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5 font-mono">
              <span>0 mm (Dry)</span>
              <span>Baseline: {baseRain.toFixed(1)} mm</span>
              <span>100 mm (Monsoon)</span>
            </div>
          </div>

          {/* Relative Humidity Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-[#16324F]">Relative Humidity</span>
              <span className="font-mono font-bold text-indigo-700">{hum.toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min={10.0}
              max={100.0}
              step={1.0}
              value={hum}
              onChange={(e) => setHum(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-[10px] text-[#94A3B8] mt-0.5 font-mono">
              <span>10% (Arid)</span>
              <span>Baseline: {baseHum.toFixed(0)}%</span>
              <span>100% (Saturated)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Large RUN SIMULATION Button */}
      <div className="flex justify-center">
        <button
          onClick={handleRunSimulation}
          disabled={isSimulating}
          className="flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-[#0B78B5] hover:bg-[#09669B] active:bg-[#075683] text-white font-extrabold text-sm shadow-md transition-all disabled:opacity-50 cursor-pointer min-w-[240px]"
        >
          {isSimulating ? (
            <>
              <Activity className="w-5 h-5 animate-spin" />
              <span>Simulating Hydrological Response...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5 fill-white" />
              <span>RUN SIMULATION</span>
            </>
          )}
        </button>
      </div>

      {errorMsg && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Simulation Results Display */}
      {wb && (
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#0B78B5]" />
              Recalculated Simulation Outcomes
            </h3>
            <span className="text-xs text-[#64748B] font-mono">Live Simulation Result</span>
          </div>

          {/* 4 Outcome Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Predicted Demand"
              sublabel="Simulated Volumetric Need"
              value={formatLitres(wb.predicted_demand_litres, true)}
              contextText={`${wb.predicted_lpcd} LPCD per Capita`}
              badgeText="Recalculated"
              badgeVariant="info"
              valueColorClass="text-[#0B78B5]"
            />

            <KpiCard
              label="Expected Supply"
              sublabel="Simulated Source Inflow"
              value={formatLitres(wb.estimated_supply_litres, true)}
              contextText={`${wb.supply_lpcd} LPCD Capacity`}
              badgeText="Supply"
              badgeVariant="safe"
              valueColorClass="text-[#0D9488]"
            />

            <KpiCard
              label="Water Balance"
              sublabel={isDeficit ? 'Simulated Deficit' : 'Simulated Surplus'}
              value={isDeficit ? `-${formatLitres(wb.deficit_litres, true)}` : `+${formatLitres(wb.surplus_litres, true)}`}
              contextText={`${formatPercentage(wb.coverage_percentage)} Coverage Ratio`}
              badgeText={isDeficit ? 'Deficit' : 'Surplus'}
              badgeVariant={isDeficit ? 'danger' : 'safe'}
              valueColorClass={isDeficit ? 'text-red-600' : 'text-emerald-700'}
            />

            <KpiCard
              label="Shortage Risk"
              sublabel="Simulated Failure Probability"
              value={formatPercentage(wb.shortage_probability_pct)}
              contextText={`${wb.risk_category} Risk Category`}
              badgeText={`${wb.risk_category} Risk`}
              badgeVariant={isDeficit || wb.risk_category === 'CRITICAL' ? 'danger' : wb.risk_category === 'MODERATE' ? 'warning' : 'safe'}
              valueColorClass={wb.shortage_probability_pct > 25 ? 'text-red-600' : 'text-[#16324F]'}
            />
          </div>

          {/* Advisory & Response Directive */}
          <div className="card-base p-5 border-l-4 border-l-[#0B78B5]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#64748B] flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-[#0B78B5]" />
                Recommended Response Strategy
              </span>
              {isDeficit && (
                <span className="text-xs font-bold text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded flex items-center gap-1">
                  <Truck className="w-3 h-3 text-red-600" />
                  Tankers Required: {wb.tankers_needed} units
                </span>
              )}
            </div>

            <p className="text-sm font-bold text-[#16324F] leading-relaxed">
              {wb.primary_recommendation}
            </p>

            <div className="pt-3 border-t border-[#F1F5F9] mt-3 text-[11px] text-[#64748B] flex items-start gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" />
              <span>{wb.disclaimer}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
