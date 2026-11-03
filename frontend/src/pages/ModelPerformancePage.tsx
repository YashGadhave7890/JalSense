import React, { useEffect, useState } from 'react'
import {
  Award,
  BarChart2,
  CheckCircle2,
  Cpu,
  Layers,
  Activity,
  FileText
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts'
import type { ModelMetricsResponse, ModelComparisonItem } from '../types'
import { api } from '../services/api'
import { KpiCard } from '../components/KpiCard'
import { formatLitres, formatPercentage } from '../utils/formatters'

export const ModelPerformancePage: React.FC = () => {
  const [metrics, setMetrics] = useState<ModelMetricsResponse | null>(null)
  const [comparison, setComparison] = useState<ModelComparisonItem[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      setIsLoading(true)
      try {
        const [mRes, cRes] = await Promise.all([
          api.getModelMetrics(),
          api.getModelComparison()
        ])
        setMetrics(mRes)
        setComparison(cRes.comparison || [])
      } catch (err: any) {
        setErrorMsg(err.message || 'Failed to load model evaluation artifacts.')
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  if (isLoading) {
    return (
      <div className="card-base p-12 text-center text-[#64748B]">
        <Activity className="w-8 h-8 animate-spin text-[#0B78B5] mx-auto mb-3" />
        <div className="font-semibold text-[#16324F]">Loading Model Evaluation Artifacts...</div>
        <div className="text-xs mt-1">Reading saved model metrics and holdout benchmarking tables.</div>
      </div>
    )
  }

  const bestMetrics = metrics?.best_model_metrics || {
    mae_litres: 6589.57,
    rmse_litres: 9309.34,
    r2_score: 0.9884,
    wape_pct: 3.46
  }

  return (
    <div className="space-y-5 pb-8">
      {/* Champion Hero Card */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Holdout Champion
                </span>
                <span className="text-xs text-[#64748B]">• Strict Chronological Split (No Leakage)</span>
              </div>
              <h2 className="text-xl font-extrabold text-[#16324F] mt-1">
                {metrics?.selected_model || 'XGBoost Regressor'}
              </h2>
              <p className="text-xs text-[#64748B] mt-0.5 max-w-2xl leading-relaxed">
                Selected based on lowest Test Mean Absolute Error (MAE) and highest R² among all benchmarked architectures on un-shuffled chronological holdout observations.
              </p>
            </div>
          </div>

          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3 text-xs text-right shrink-0">
            <div className="text-[#64748B] text-[10px] uppercase font-bold">Split Distribution</div>
            <div className="font-mono text-[#16324F] font-bold mt-0.5">
              Train: {metrics?.train_samples ?? 2565} | Val: {metrics?.val_samples ?? 545} | Test: {metrics?.test_samples ?? 545}
            </div>
            <span className="text-[10px] text-emerald-700 font-semibold block mt-0.5">
              Zero Random Shuffling (Time-Series Safe)
            </span>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-3 rounded-lg">
          {errorMsg}
        </div>
      )}

      {/* 4 Holdout Test Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Test MAE"
          sublabel="Mean Absolute Error"
          value={formatLitres(bestMetrics.mae_litres)}
          contextText="Average daily error in litres"
          badgeText="Holdout"
          badgeVariant="safe"
          valueColorClass="text-[#0B78B5]"
          icon={Activity}
        />

        <KpiCard
          label="Test RMSE"
          sublabel="Root Mean Squared Error"
          value={formatLitres(bestMetrics.rmse_litres)}
          contextText="Penalizes large outlier errors"
          badgeText="Precision"
          badgeVariant="info"
          valueColorClass="text-[#0D9488]"
          icon={BarChart2}
        />

        <KpiCard
          label="Coefficient R²"
          sublabel="Variance Explained"
          value={bestMetrics.r2_score.toFixed(4)}
          contextText="Proportion of variance captured"
          badgeText="Goodness of Fit"
          badgeVariant="safe"
          valueColorClass="text-emerald-700"
          icon={CheckCircle2}
        />

        <KpiCard
          label="Test WAPE"
          sublabel="Weighted Absolute % Error"
          value={formatPercentage(bestMetrics.wape_pct)}
          contextText="Scale-independent percentage error"
          badgeText="Accuracy"
          badgeVariant="neutral"
          valueColorClass="text-[#16324F]"
          icon={Cpu}
        />
      </div>

      {/* 4-Model Comparison Table */}
      <div className="card-base p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#0B78B5]" />
            4-Model Empirical Benchmark Comparison
          </h3>
          <span className="text-xs text-[#64748B] font-mono">
            {comparison.length} Architectures
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="bg-[#F8FAFC] text-[#64748B] uppercase font-bold border-b border-[#E2E8F0]">
                <th className="py-2.5 px-3">Model Architecture</th>
                <th className="py-2.5 px-3 text-right">Val MAE (L)</th>
                <th className="py-2.5 px-3 text-right">Val RMSE (L)</th>
                <th className="py-2.5 px-3 text-right">Val R²</th>
                <th className="py-2.5 px-3 text-right">Test MAE (L)</th>
                <th className="py-2.5 px-3 text-right">Test RMSE (L)</th>
                <th className="py-2.5 px-3 text-right">Test R²</th>
                <th className="py-2.5 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F1F5F9]">
              {comparison.map((item, idx) => {
                const isChampion = item.model.toLowerCase().includes('xgboost')
                return (
                  <tr
                    key={idx}
                    className={`transition-colors ${
                      isChampion ? 'bg-emerald-50/40 font-semibold' : 'hover:bg-[#F9FBFE]'
                    }`}
                  >
                    <td className="py-3 px-3 text-[#16324F] flex items-center gap-2">
                      {isChampion && <Award className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
                      <span className={isChampion ? 'font-bold text-emerald-950' : 'font-medium'}>
                        {item.model}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-[#64748B]">{item.val_mae.toFixed(2)}</td>
                    <td className="py-3 px-3 text-right font-mono text-[#64748B]">{item.val_rmse.toFixed(2)}</td>
                    <td className="py-3 px-3 text-right font-mono text-[#64748B]">{item.val_r2.toFixed(4)}</td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-[#0B78B5]">
                      {item.test_mae.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-[#0D9488]">
                      {item.test_rmse.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-emerald-700">
                      {item.test_r2.toFixed(4)}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          isChampion
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : 'bg-slate-100 text-[#64748B]'
                        }`}
                      >
                        {isChampion ? 'Champion' : 'Benchmark'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* MAE & RMSE Error Distribution Chart */}
      {comparison.length > 0 && (
        <div className="card-base p-5">
          <h3 className="text-sm font-bold text-[#16324F] uppercase tracking-wide mb-3 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-[#0B78B5]" />
            Test Error Metrics (MAE & RMSE) Across Architectures
          </h3>
          <p className="text-xs text-[#64748B] mb-4">
            Lower error metrics signify higher volumetric precision. XGBoost achieved minimum MAE (6,589.57 L).
          </p>

          <div className="h-64 sm:h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparison} margin={{ top: 15, right: 15, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis
                  dataKey="model"
                  tick={{ fontSize: 11, fill: '#16324F' }}
                  tickFormatter={(val) => val.split(' ')[0]}
                  stroke="#CBD5E1"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748B' }}
                  tickFormatter={(val) => `${(val / 1000).toFixed(1)}k L`}
                  stroke="#CBD5E1"
                />
                <Tooltip
                  formatter={(val: any) => [`${Number(val).toFixed(2)} Litres`, '']}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E2E8F0',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                />
                <Legend verticalAlign="top" align="right" wrapperStyle={{ fontSize: '11px', paddingBottom: '10px' }} />
                <Bar dataKey="test_mae" name="Test MAE (Litres)" fill="#0B78B5" radius={[4, 4, 0, 0]} barSize={28} />
                <Bar dataKey="test_rmse" name="Test RMSE (Litres)" fill="#D97706" radius={[4, 4, 0, 0]} barSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Technical Notes & Rationale */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-base p-4">
          <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-[#16324F] mb-2">
            <FileText className="w-4 h-4 text-[#0B78B5]" />
            Why This Model? (Selection Rationale)
          </div>
          <p className="text-xs text-[#64748B] leading-relaxed">
            The <strong>XGBoost Regressor</strong> demonstrated superior capacity to model non-linear interactions between bio-meteorological stresses (ambient temperature and heat index) and rolling autoregressive consumption patterns. It outperformed the baseline Linear Regression by over 1,265 litres in average precision.
          </p>
        </div>

        <div className="card-base p-4">
          <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-[#16324F] mb-2">
            <Layers className="w-4 h-4 text-[#0D9488]" />
            Temporal Leakage Prevention
          </div>
          <p className="text-xs text-[#64748B] leading-relaxed">
            Time-series data is evaluated using strict <strong>chronological forward splitting</strong> (70% Train, 15% Validation, 15% Holdout Test). Zero random shuffling or k-fold cross-validation is permitted to prevent temporal lookahead leakage.
          </p>
        </div>
      </div>
    </div>
  )
}
