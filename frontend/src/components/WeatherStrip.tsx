import React from 'react'
import { Thermometer, CloudRain, Droplets, Flame } from 'lucide-react'
import { formatTemperature } from '../utils/formatters'

interface WeatherStripProps {
  weather?: {
    temp_mean_celsius?: number
    temp_max?: number
    temp_min?: number
    rainfall_mm?: number
    humidity_pct?: number
    heat_index_celsius?: number
    season?: string
    [key: string]: any
  }
  compact?: boolean
}

export const WeatherStrip: React.FC<WeatherStripProps> = ({ weather, compact = false }) => {
  if (!weather) return null

  const temp = weather.temp_mean_celsius ?? 28.0
  const rain = weather.rainfall_mm ?? 0.0
  const humidity = weather.humidity_pct ?? 50.0
  const heatIndex = weather.heat_index_celsius ?? temp

  return (
    <div className={`grid grid-cols-2 ${compact ? 'sm:grid-cols-4' : 'sm:grid-cols-4'} gap-3`}>
      <div className="card-base p-3 flex items-center gap-3">
        <div className="p-2 rounded-md bg-blue-50 text-[#0B78B5]">
          <Thermometer className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-[#64748B] block">Temperature</span>
          <span className="text-base font-extrabold font-mono text-[#16324F]">{formatTemperature(temp)}</span>
          <span className="text-[10px] text-[#64748B] block">Ambient Mean</span>
        </div>
      </div>

      <div className="card-base p-3 flex items-center gap-3">
        <div className="p-2 rounded-md bg-cyan-50 text-[#0D9488]">
          <CloudRain className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-[#64748B] block">Precipitation</span>
          <span className="text-base font-extrabold font-mono text-[#16324F]">{rain.toFixed(1)} mm</span>
          <span className="text-[10px] text-[#64748B] block">Daily Total</span>
        </div>
      </div>

      <div className="card-base p-3 flex items-center gap-3">
        <div className="p-2 rounded-md bg-indigo-50 text-indigo-600">
          <Droplets className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-[#64748B] block">Relative Humidity</span>
          <span className="text-base font-extrabold font-mono text-[#16324F]">{Math.round(humidity)}%</span>
          <span className="text-[10px] text-[#64748B] block">Atmospheric</span>
        </div>
      </div>

      <div className="card-base p-3 flex items-center gap-3">
        <div className="p-2 rounded-md bg-amber-50 text-[#D97706]">
          <Flame className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-[#64748B] block">Heat Index</span>
          <span className="text-base font-extrabold font-mono text-[#16324F]">{formatTemperature(heatIndex)}</span>
          <span className="text-[10px] text-[#64748B] block">{weather.season || 'Steadman'}</span>
        </div>
      </div>
    </div>
  )
}
