export interface VillageMeta {
  id: string
  name: string
  state: string
  latitude: number
  longitude: number
  base_population: number
  avg_daily_supply_litres: number
  storage_capacity_litres: number
  water_source: string
}

export interface HealthResponse {
  status: string
  model_loaded: boolean
  champion_model?: string
  configured_villages_count: number
  villages: string[]
  timestamp: string
}

export interface DailyWeatherRecord {
  date: string
  temp_max?: number
  temp_min?: number
  temp_mean: number
  rainfall_mm: number
  humidity_pct: number
  heat_index_celsius?: number
}

export interface WeatherForecastResponse {
  village_id: string
  village_name: string
  source: string
  cache_hit: boolean
  forecast: DailyWeatherRecord[]
}

export interface WaterBalance {
  predicted_demand_litres: number
  estimated_supply_litres: number
  deficit_litres: number
  surplus_litres: number
  supply_coverage_ratio: number
  coverage_percentage: number
  shortage_probability: number
  shortage_probability_pct: number
  risk_category: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
  risk_color: string
  risk_description: string
  tankers_needed: number
  tanker_capacity_litres: number
  primary_recommendation: string
  disclaimer: string
  operational_directives?: string[]
  predicted_lpcd: number
  supply_lpcd: number
  jjm_benchmark_lpcd: number
  shortage_risk: string
}

export interface PredictDemandResponse {
  village_id: string
  village_name: string
  state: string
  forecast_date: string
  predicted_demand_litres: number
  predicted_lpcd: number
  estimated_supply_litres: number
  deficit_litres: number
  surplus_litres: number
  shortage_risk: string
  weather: {
    temp_mean_celsius: number
    rainfall_mm: number
    humidity_pct: number
    heat_index_celsius: number
    season: string
    [key: string]: any
  }
  features_used: Record<string, any>
  water_balance: WaterBalance
}

export interface ForecastDayItem {
  day_offset: number
  date: string
  day_name: string
  temp_mean: number
  rainfall_mm: number
  humidity_pct: number
  predicted_demand_litres: number
  estimated_supply_litres: number
  deficit_litres: number
  surplus_litres: number
  shortage_probability_pct: number
  risk_category: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
  risk_color: string
  tankers_needed: number
}

export interface MultiDayForecastResponse {
  village_id: string
  village_name: string
  state: string
  weather_source: string
  forecast_days_count: number
  forecasts: ForecastDayItem[]
}

export interface ScenarioSimulationRequest {
  village_id: string
  population: number
  rainfall_mm: number
  temp_celsius: number
  water_supply_litres: number
  storage_capacity_litres: number
  current_storage_litres: number
  humidity_pct: number
}

export interface ScenarioSimulationResponse {
  scenario_inputs: Record<string, any>
  recalculated_demand_litres: number
  shortage_assessment: WaterBalance
}

export interface AssistantQueryRequest {
  question: string
  village_id: string
  mode?: 'auto' | 'hf' | 'fallback'
}

export interface AssistantQueryResponse {
  question: string
  village_id: string
  answer: string
  source_mode: string
  source_label: string
  is_fallback: boolean
}

export interface HistoricalRecord {
  date: string
  water_demand_litres: number
  daily_supply_litres: number
  temp_mean: number
  rainfall_mm: number
  humidity_pct: number
}

export interface HistoricalResponse {
  village_id: string
  records_count: number
  records: HistoricalRecord[]
  stats: {
    avg_demand_litres: number
    min_demand_litres: number
    max_demand_litres: number
  }
}

export interface ModelComparisonItem {
  model: string
  val_mae: number
  val_rmse: number
  val_r2: number
  test_mae: number
  test_rmse: number
  test_r2: number
}

export interface ModelMetricsResponse {
  selected_model: string
  train_samples: number
  val_samples: number
  test_samples: number
  features_count?: number
  best_model_metrics: {
    mae_litres: number
    rmse_litres: number
    r2_score: number
    wape_pct: number
  }
  comparison_table?: Record<string, any>
}
