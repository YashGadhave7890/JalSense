import React from 'react'
import {
  CloudSun,
  Thermometer,
  CloudRain,
  Droplets,
  Flame,
  Calendar,
  Clock
} from 'lucide-react'
import type { WeatherForecastResponse, VillageMeta } from '../types'
import { WeatherStrip } from '../components/WeatherStrip'
import { formatTemperature, formatDate } from '../utils/formatters'

interface WeatherIntelligencePageProps {
  weatherData?: WeatherForecastResponse
  selectedVillage?: VillageMeta
  isLoading: boolean
}

export const WeatherIntelligencePage: React.FC<WeatherIntelligencePageProps> = ({
  weatherData,
  selectedVillage,
  isLoading
}) => {
  if (isLoading || !weatherData) {
    return (
      <div className="card-base p-12 text-center text-[#64748B]">
        <CloudSun className="w-8 h-8 animate-pulse text-[#0B78B5] mx-auto mb-3" />
        <div className="font-semibold text-[#16324F]">Synchronizing Open-Meteo Meteorological Observations...</div>
        <div className="text-xs mt-1">Retrieving numerical reanalysis and deterministic multi-day weather grids.</div>
      </div>
    )
  }

  const forecast = weatherData.forecast || []
  const todayWeather = forecast.length > 0 ? forecast[0] : null

  return (
    <div className="space-y-5 pb-8">
      {/* Top Header Card */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                Meteorological Ingestion
              </span>
              <span className="text-xs text-[#64748B]">• Open-Meteo Weather API</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#16324F] mt-1">
              Weather Intelligence & Thermal Elasticity
            </h2>
            <p className="text-xs text-[#64748B] mt-0.5 max-w-3xl leading-relaxed">
              Synchronized micro-climate observations driving hydrological demand forecasting. Local deterministic disk caching with 1-hour TTL ensures rate-limit compliance.
            </p>
          </div>

          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-2.5 text-xs text-right shrink-0">
            <span className="text-[#64748B] text-[10px] uppercase font-bold block">Source Attribution</span>
            <span className="font-bold text-[#16324F] flex items-center justify-end gap-1">
              <CloudSun className="w-3.5 h-3.5 text-[#0B78B5]" /> {weatherData.source}
            </span>
            <span className="text-[11px] text-[#0D9488] block font-mono">
              Cache: {weatherData.cache_hit ? 'Disk Hit (Cached)' : 'Live API Query'}
            </span>
          </div>
        </div>
      </div>

      {/* Current Conditions Strip */}
      {todayWeather && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#64748B] flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#0B78B5]" />
              Today's Meteorological Telemetry ({formatDate(todayWeather.date)})
            </span>
            <span className="text-xs text-[#64748B]">
              Coordinates: {selectedVillage?.latitude ?? 18.91}°N, {selectedVillage?.longitude ?? 74.40}°E
            </span>
          </div>
          <WeatherStrip
            weather={{
              temp_mean_celsius: todayWeather.temp_mean,
              rainfall_mm: todayWeather.rainfall_mm,
              humidity_pct: todayWeather.humidity_pct,
              heat_index_celsius: todayWeather.heat_index_celsius ?? todayWeather.temp_mean,
              season: 'Open-Meteo'
            }}
          />
        </div>
      )}

      {/* Weather Impact on Water Demand Rationale */}
      <div className="card-base p-5">
        <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide flex items-center gap-2 mb-2">
          <Thermometer className="w-4 h-4 text-[#0B78B5]" />
          Weather Influence on Rural Water Demand
        </h3>
        <p className="text-xs text-[#64748B] mb-4">
          Quantified physiological and operational demand elasticity across rural agro-climatic zones:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs leading-relaxed">
          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3.5">
            <div className="flex items-center gap-2 font-bold text-[#16324F] mb-1.5">
              <Flame className="w-4 h-4 text-amber-500" />
              Thermal Elasticity (+1.6%/°C)
            </div>
            <p className="text-[#64748B]">
              Human and livestock hydration demands expand by approximately <strong>+1.6% per °C</strong> above baseline (25°C). High temperatures accelerate community borewell abstraction and cattle trough refills.
            </p>
          </div>

          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3.5">
            <div className="flex items-center gap-2 font-bold text-[#16324F] mb-1.5">
              <CloudRain className="w-4 h-4 text-cyan-600" />
              Rainfall Damping Effect
            </div>
            <p className="text-[#64748B]">
              Precipitation events directly substitute kitchen-garden irrigation and dampen secondary domestic pumping, depressing aggregate piped tap withdrawals during high rainfall days.
            </p>
          </div>

          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3.5">
            <div className="flex items-center gap-2 font-bold text-[#16324F] mb-1.5">
              <Droplets className="w-4 h-4 text-indigo-500" />
              Relative Humidity & Heat Index
            </div>
            <p className="text-[#64748B]">
              The Steadman Heat Index couples dry-bulb temperature and humidity. Low humidity accelerates evaporative drying, requiring frequent village washing and livestock cooling.
            </p>
          </div>
        </div>
      </div>

      {/* 7-Day Meteorological Forecast Cards */}
      <div className="card-base p-5">
        <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide mb-3 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-[#0B78B5]" />
          7-Day Weather Grid (Open-Meteo Multi-Day Horizon)
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
          {forecast.map((d, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg border text-xs text-center flex flex-col justify-between ${
                i === 0 ? 'bg-blue-50/60 border-blue-200' : 'bg-[#F8FAFC] border-[#E2E8F0]'
              }`}
            >
              <div>
                <span className="text-[10px] uppercase font-bold text-[#64748B] block">
                  {i === 0 ? 'Today' : `Day +${i}`}
                </span>
                <span className="font-mono font-bold text-[#16324F] block my-0.5">{d.date.slice(5)}</span>
              </div>

              <div className="my-2">
                <Thermometer className="w-5 h-5 text-amber-500 mx-auto mb-1" />
                <span className="font-mono font-extrabold text-sm text-[#16324F] block">
                  {formatTemperature(d.temp_mean)}
                </span>
                {d.temp_max && d.temp_min && (
                  <span className="text-[10px] text-[#64748B] block">
                    {d.temp_min.toFixed(0)}° / {d.temp_max.toFixed(0)}°
                  </span>
                )}
              </div>

              <div className="pt-2 border-t border-slate-200/60 text-[11px] text-[#64748B] space-y-0.5">
                <div className="flex items-center justify-between">
                  <span>Rain:</span>
                  <span className="font-mono font-bold text-cyan-700">{d.rainfall_mm.toFixed(1)}mm</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Hum:</span>
                  <span className="font-mono">{Math.round(d.humidity_pct)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
