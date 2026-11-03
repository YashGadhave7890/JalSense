import React, { useEffect, useState, useCallback } from 'react'
import { Sidebar, type PageId } from './components/Sidebar'
import { Header } from './components/Header'
import { OverviewPage } from './pages/OverviewPage'
import { DemandForecastPage } from './pages/DemandForecastPage'
import { ShortageRiskPage } from './pages/ShortageRiskPage'
import { WeatherIntelligencePage } from './pages/WeatherIntelligencePage'
import { ScenarioSimulatorPage } from './pages/ScenarioSimulatorPage'
import { ModelPerformancePage } from './pages/ModelPerformancePage'
import { DataProvenancePage } from './pages/DataProvenancePage'
import { AIAssistantPage } from './pages/AIAssistantPage'

import { api } from './services/api'
import type {
  VillageMeta,
  PredictDemandResponse,
  MultiDayForecastResponse,
  WeatherForecastResponse,
  HistoricalRecord
} from './types'
import { AlertTriangle, Activity } from 'lucide-react'

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false)

  // Data states
  const [villages, setVillages] = useState<VillageMeta[]>([])
  const [selectedVillageId, setSelectedVillageId] = useState<string>('VILL001')
  const [prediction, setPrediction] = useState<PredictDemandResponse | null>(null)
  const [forecastData, setForecastData] = useState<MultiDayForecastResponse | null>(null)
  const [weatherData, setWeatherData] = useState<WeatherForecastResponse | null>(null)
  const [historicalRecords, setHistoricalRecords] = useState<HistoricalRecord[]>([])

  // Telemetry status
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false)
  const [championModel, setChampionModel] = useState<string>('XGBoost Regressor')
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // 1. Initial health & village metadata load
  useEffect(() => {
    async function initSystem() {
      try {
        const health = await api.getHealth()
        setBackendHealthy(health.status === 'healthy')
        if (health.champion_model) {
          setChampionModel(health.champion_model)
        }

        const vRes = await api.getVillages()
        if (vRes.villages && vRes.villages.length > 0) {
          setVillages(vRes.villages)
          setSelectedVillageId(vRes.villages[0].id)
        }
      } catch (err) {
        console.warn('Initial backend connection issue:', err)
        setBackendHealthy(false)
      }
    }
    initSystem()
  }, [])

  // 2. Fetch telemetry for selected village
  const fetchVillageData = useCallback(async (vid: string) => {
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const [predRes, forecastRes, weatherRes, histRes] = await Promise.all([
        api.predictDemand({ village_id: vid, use_live_weather: true }),
        api.getForecast(vid),
        api.getWeather(vid, 7),
        api.getHistorical(vid, 45)
      ])

      setPrediction(predRes)
      setForecastData(forecastRes)
      setWeatherData(weatherRes)
      setHistoricalRecords(histRes.records || [])
      setBackendHealthy(true)
      setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
    } catch (err: any) {
      console.error('Failed to fetch village telemetry:', err)
      setErrorMsg(err.message || 'Error communicating with backend API service.')
      setBackendHealthy(false)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedVillageId) {
      fetchVillageData(selectedVillageId)
    }
  }, [selectedVillageId, fetchVillageData])

  const selectedVillage = villages.find((v) => v.id === selectedVillageId) || villages[0]

  // Page titles and subtitles
  const pageMeta: Record<PageId, { title: string; subtitle: string }> = {
    overview: {
      title: 'Water Security Command Overview',
      subtitle: 'Real-time decision intelligence & volumetric supply-demand analytics'
    },
    forecast: {
      title: '7-Day Water Demand Forecast',
      subtitle: 'Autoregressive multi-step prediction incorporating dynamic lags & weather forecasts'
    },
    shortage: {
      title: 'Shortage Risk & Vulnerability Analysis',
      subtitle: 'Gaussian stochastic margin modeling and tanker logistics estimation'
    },
    weather: {
      title: 'Meteorological Intelligence',
      subtitle: 'Open-Meteo numerical weather forecasts and thermal demand elasticity'
    },
    simulator: {
      title: 'Scenario Simulator & Stress-Testing',
      subtitle: 'Interactive parameter sensitivity testing for climate and demographic surges'
    },
    performance: {
      title: 'Model Performance & Benchmarking',
      subtitle: 'Empirical holdout validation under chronological non-shuffled evaluation'
    },
    provenance: {
      title: 'Data Sources & Research Provenance',
      subtitle: 'Empirical smart-meter dataset disclosure and academic integrity documentation'
    },
    assistant: {
      title: 'AI Hydrological Decision Assistant',
      subtitle: 'Natural-language explanations grounded in actual telemetry and model outputs'
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#F5F8FC] text-[#16324F]">
      {/* Collapsible Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        backendHealthy={backendHealthy}
        championModel={championModel}
      />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Sticky Header */}
        <Header
          pageTitle={pageMeta[currentPage].title}
          pageSubtitle={pageMeta[currentPage].subtitle}
          villages={villages}
          selectedVillageId={selectedVillageId}
          onSelectVillage={setSelectedVillageId}
          lastUpdated={lastUpdated}
          onRefresh={() => fetchVillageData(selectedVillageId)}
          isLoading={isLoading}
          backendHealthy={backendHealthy}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-5">
          {errorMsg && (
            <div className="bg-red-50 border border-red-200 text-red-800 text-xs p-3.5 rounded-lg flex items-center justify-between mb-4 shadow-2xs">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>
                  <strong>API Synchronization Error:</strong> {errorMsg}
                </span>
              </div>
              <button
                onClick={() => fetchVillageData(selectedVillageId)}
                className="font-bold underline text-red-900 hover:text-red-700 text-xs shrink-0"
              >
                Retry
              </button>
            </div>
          )}

          {/* Render Active Page */}
          {currentPage === 'overview' && prediction && (
            <OverviewPage
              prediction={prediction}
              historicalRecords={historicalRecords}
              selectedVillage={selectedVillage}
              isLoading={isLoading}
            />
          )}

          {currentPage === 'forecast' && (
            <DemandForecastPage
              forecastData={forecastData || undefined}
              selectedVillage={selectedVillage}
              isLoading={isLoading}
            />
          )}

          {currentPage === 'shortage' && prediction && (
            <ShortageRiskPage
              waterBalance={prediction.water_balance}
              selectedVillage={selectedVillage}
            />
          )}

          {currentPage === 'weather' && (
            <WeatherIntelligencePage
              weatherData={weatherData || undefined}
              selectedVillage={selectedVillage}
              isLoading={isLoading}
            />
          )}

          {currentPage === 'simulator' && (
            <ScenarioSimulatorPage
              selectedVillage={selectedVillage}
              initialWeather={prediction?.weather}
            />
          )}

          {currentPage === 'performance' && <ModelPerformancePage />}

          {currentPage === 'provenance' && <DataProvenancePage villages={villages} />}

          {currentPage === 'assistant' && (
            <AIAssistantPage
              selectedVillage={selectedVillage}
              prediction={prediction || undefined}
            />
          )}

          {isLoading && !prediction && (
            <div className="h-64 flex flex-col items-center justify-center text-xs text-[#64748B]">
              <Activity className="w-8 h-8 animate-spin text-[#0B78B5] mb-3" />
              <div className="font-semibold text-[#16324F]">Connecting to JalSense Predictive API...</div>
              <div>Loading village parameters and computing next-day hydrological balance.</div>
            </div>
          )}

          {/* Academic Presentation Mode Footer */}
          <footer className="mt-8 pt-4 border-t border-[#E2E8F0] text-center text-xs text-[#64748B] space-y-1">
            <div className="font-semibold text-[#16324F]">
              JalSense — Village Water Intelligence System
            </div>
            <div className="text-[11px]">
              Advanced Data Science Laboratory • B.Tech Project • Department of Computer Science & Engineering
            </div>
            <div className="text-[10px] text-[#94A3B8]">
              Empirical smart-meter time-series modeling (CC BY-SA 4.0) + Live Open-Meteo weather synchronization
            </div>
          </footer>
        </main>
      </div>
    </div>
  )
}

export default App
