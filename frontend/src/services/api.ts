import type {
  HealthResponse,
  VillageMeta,
  WeatherForecastResponse,
  PredictDemandResponse,
  WaterBalance,
  ScenarioSimulationRequest,
  ScenarioSimulationResponse,
  MultiDayForecastResponse,
  AssistantQueryRequest,
  AssistantQueryResponse,
  HistoricalResponse,
  ModelMetricsResponse,
  ModelComparisonItem
} from '../types'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== ''
    ? import.meta.env.VITE_API_BASE_URL
    : '/api'
).replace(/\/$/, '')

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP error ${res.status}: ${res.statusText}`
    try {
      const errorJson = await res.json()
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail)
  }
  return res.json()
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(5000) })
    return handleResponse<HealthResponse>(res)
  },

  async getVillages(): Promise<{ count: number; villages: VillageMeta[] }> {
    const res = await fetch(`${API_BASE_URL}/villages`, { signal: AbortSignal.timeout(5000) })
    return handleResponse<{ count: number; villages: VillageMeta[] }>(res)
  },

  async getWeather(villageId: string, days = 7): Promise<WeatherForecastResponse> {
    const res = await fetch(`${API_BASE_URL}/weather?village_id=${encodeURIComponent(villageId)}&days=${days}`, {
      signal: AbortSignal.timeout(8000)
    })
    return handleResponse<WeatherForecastResponse>(res)
  },

  async predictDemand(params: {
    village_id: string
    use_live_weather?: boolean
    custom_temp?: number
    custom_rainfall?: number
    custom_humidity?: number
    custom_population?: number
    custom_supply?: number
  }): Promise<PredictDemandResponse> {
    const res = await fetch(`${API_BASE_URL}/predict-demand`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        use_live_weather: true,
        ...params
      }),
      signal: AbortSignal.timeout(10000)
    })
    return handleResponse<PredictDemandResponse>(res)
  },

  async assessShortageRisk(params: {
    predicted_demand_litres?: number
    estimated_supply_litres?: number
    village_id?: string
    population?: number
    storage_capacity_litres?: number
    current_storage_litres?: number
  }): Promise<WaterBalance> {
    const res = await fetch(`${API_BASE_URL}/shortage-risk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(8000)
    })
    return handleResponse<WaterBalance>(res)
  },

  async simulateScenario(req: ScenarioSimulationRequest): Promise<ScenarioSimulationResponse> {
    const res = await fetch(`${API_BASE_URL}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal: AbortSignal.timeout(10000)
    })
    return handleResponse<ScenarioSimulationResponse>(res)
  },

  async getForecast(villageId: string): Promise<MultiDayForecastResponse> {
    const res = await fetch(`${API_BASE_URL}/forecast?village_id=${encodeURIComponent(villageId)}`, {
      signal: AbortSignal.timeout(12000)
    })
    return handleResponse<MultiDayForecastResponse>(res)
  },

  async getHistorical(villageId: string, days = 45): Promise<HistoricalResponse> {
    const res = await fetch(`${API_BASE_URL}/historical?village_id=${encodeURIComponent(villageId)}&days=${days}`, {
      signal: AbortSignal.timeout(8000)
    })
    return handleResponse<HistoricalResponse>(res)
  },

  async getModelMetrics(): Promise<ModelMetricsResponse> {
    const res = await fetch(`${API_BASE_URL}/models/metrics`, { signal: AbortSignal.timeout(5000) })
    return handleResponse<ModelMetricsResponse>(res)
  },

  async getModelComparison(): Promise<{ count: number; comparison: ModelComparisonItem[] }> {
    const res = await fetch(`${API_BASE_URL}/models/comparison`, { signal: AbortSignal.timeout(5000) })
    return handleResponse<{ count: number; comparison: ModelComparisonItem[] }>(res)
  },

  async queryAssistant(req: AssistantQueryRequest): Promise<AssistantQueryResponse> {
    const res = await fetch(`${API_BASE_URL}/assistant/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal: AbortSignal.timeout(20000)
    })
    return handleResponse<AssistantQueryResponse>(res)
  }
}
