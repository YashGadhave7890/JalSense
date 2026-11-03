import React from 'react'
import {
  ExternalLink,
  ShieldAlert,
  CloudSun,
  MapPin,
  FileSpreadsheet
} from 'lucide-react'
import type { VillageMeta } from '../types'

interface DataProvenancePageProps {
  villages: VillageMeta[]
}

export const DataProvenancePage: React.FC<DataProvenancePageProps> = ({ villages }) => {
  return (
    <div className="space-y-5 pb-8">
      {/* Top Card */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs">
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-[#0B78B5] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
            Academic Research Integrity
          </span>
          <span className="text-xs text-[#64748B]">• Transparent Dataset Specification</span>
        </div>
        <h2 className="text-xl font-extrabold text-[#16324F] mt-1">
          Data Provenance & Empirical Architecture
        </h2>
        <p className="text-xs text-[#64748B] mt-0.5 max-w-3xl leading-relaxed">
          Full disclosure of telemetry data sources, meteorological reanalysis endpoints, and micro-catchment scaling configurations.
        </p>
      </div>

      {/* Critical Integrity Disclaimer */}
      <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 text-xs text-amber-950 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="block text-amber-900 font-bold mb-0.5">
            Academic Research Integrity & Data Disclosure
          </strong>
          Indian national public repositories (such as <code className="bg-white/80 px-1 py-0.5 rounded">data.gov.in</code> and Jal Jeevan Mission public dashboards) provide district-level tap connection figures, but do <strong>not</strong> publicly offer open minute-level smart water meter telemetry logs. To maintain scientific integrity without fabricating artificial numbers, JalSense trains on an open empirical smart-meter time-series dataset, scaled across configured representative rural habitations.
        </div>
      </div>

      {/* 2-Column Data Specification */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Empirical Water Consumption Dataset */}
        <div className="card-base p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#F1F5F9]">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-[#0B78B5]" />
              <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide">
                Primary Empirical Consumption Dataset
              </h3>
            </div>
            <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              CC BY-SA 4.0
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Dataset Name</span>
              <strong className="text-[#16324F]">LukaLike Water Consumption Dataset</strong>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Source File</span>
              <code className="text-[#0B78B5] font-mono text-[11px]">minutely-water-consumption-data.csv</code>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Repository Origin</span>
              <a
                href="https://github.com/LukaLike/water-consumption-data"
                target="_blank"
                rel="noreferrer"
                className="text-[#0B78B5] hover:underline flex items-center gap-1 font-semibold"
              >
                GitHub — LukaLike/water-consumption-data <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Raw Observation Count</span>
              <strong className="text-[#16324F] font-mono">263,811 minutely readings</strong>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Aggregation Pipeline</span>
              <strong className="text-[#16324F]">Aggregated to daily litres (YYYY-MM-DD)</strong>
            </div>

            <div className="flex justify-between py-1">
              <span className="text-[#64748B]">Pre-cleaning Applied</span>
              <span className="text-emerald-700 font-semibold">Zero-fill dropouts & negative flow filter</span>
            </div>
          </div>
        </div>

        {/* Meteorological Reanalysis (Open-Meteo) */}
        <div className="card-base p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#F1F5F9]">
            <div className="flex items-center gap-2">
              <CloudSun className="w-4 h-4 text-[#0D9488]" />
              <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide">
                Meteorological Ingestion (Open-Meteo)
              </h3>
            </div>
            <span className="text-[10px] font-bold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              ODbL Open Database
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">API Provider</span>
              <strong className="text-[#16324F]">Open-Meteo Weather APIs</strong>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Historical Archive</span>
              <code className="text-[#0D9488] font-mono text-[11px]">archive-api.open-meteo.com/v1/archive</code>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Real-Time Forecast</span>
              <code className="text-[#0D9488] font-mono text-[11px]">api.open-meteo.com/v1/forecast</code>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Variables Ingested</span>
              <strong className="text-[#16324F]">Temp (Min/Max/Mean), Rainfall (mm), Humidity (%)</strong>
            </div>

            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-[#64748B]">Bio-Meteorology Metric</span>
              <strong className="text-[#16324F]">Steadman Rothfusz Heat Index (°C)</strong>
            </div>

            <div className="flex justify-between py-1">
              <span className="text-[#64748B]">Caching Architecture</span>
              <span className="text-[#16324F] font-mono font-semibold">Deterministic MD5 (1-hr TTL)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Configured Study Habitations Table */}
      <div className="card-base p-5">
        <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-[#0B78B5]" />
          Configured Representative Study Habitations
        </h3>
        <p className="text-xs text-[#64748B] mb-3">
          Five geographically and hydro-geologically diverse rural habitations calibrated under Jal Jeevan Mission benchmarks (55.0 LPCD):
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="bg-[#F8FAFC] text-[#64748B] uppercase font-bold border-b border-[#E2E8F0]">
                <th className="py-2.5 px-3">Village ID</th>
                <th className="py-2.5 px-3">Habitation & State</th>
                <th className="py-2.5 px-3 text-right">Population</th>
                <th className="py-2.5 px-3 text-right">Coordinates</th>
                <th className="py-2.5 px-3">Primary Water Source</th>
                <th className="py-2.5 px-3 text-right">Storage Capacity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F1F5F9]">
              {villages.map((v) => (
                <tr key={v.id} className="hover:bg-[#F9FBFE]">
                  <td className="py-3 px-3 font-mono font-bold text-[#0B78B5]">{v.id}</td>
                  <td className="py-3 px-3 font-bold text-[#16324F]">{v.name}</td>
                  <td className="py-3 px-3 text-right font-mono font-semibold text-[#16324F]">
                    {v.base_population.toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-[#64748B]">
                    {v.latitude.toFixed(2)}°N, {v.longitude.toFixed(2)}°E
                  </td>
                  <td className="py-3 px-3 text-[#16324F]">{v.water_source}</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-[#0D9488]">
                    {v.storage_capacity_litres.toLocaleString()} L
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
