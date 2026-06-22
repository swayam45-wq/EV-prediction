// ── Shared TypeScript types matching FastAPI schemas ────────

export interface ElectricityPrice {
  hour: string;
  price: number;
}

export interface ChargingRequest {
  current_soc: number;
  target_soc: number;
  battery_capacity_kwh: number;
  max_charge_rate_kw: number;
  battery_health_soh: number;
  departure_time: string;
  electricity_prices: ElectricityPrice[];
  temperature_celsius?: number;
  weather_condition?: string;
  charging_efficiency?: number;
}

export interface HourlyChargingSlot {
  hour: string;
  price: number;
  energy_kwh: number;
  is_charging: boolean;
  cumulative_soc: number;
}

export interface CostComparison {
  normal_cost: number;
  optimized_cost: number;
  savings_dollar: number;
  savings_percent: number;
}

export interface BatteryWearEstimate {
  total_score: number;
  rating: 'Low' | 'Medium' | 'High';
  temperature_impact: number;
  high_soc_stress: number;
  fast_charging_penalty: number;
}

export interface ChargingRecommendation {
  status: string;
  start_charging: string | null;
  stop_charging: string | null;
  schedule: HourlyChargingSlot[];
  total_energy_kwh: number | null;
  target_soc_reached: boolean;
  cost_analysis: CostComparison | null;
  wear_estimate: BatteryWearEstimate | null;
  battery_health_advice: string[];
  explanations: string[];
}

export interface BatteryHealthSummary {
  total_charging_sessions: number;
  avg_wear_score: number;
  avg_savings_percent: number;
  total_energy_charged_kwh: number;
  inferred_soh_percent: number;
}

export interface WearHistoryItem {
  session_id: number;
  wear_score: number;
  wear_rating: string;
  target_soc: number;
  temperature: number;
  created_at: string;
}

export interface BatteryHealthResponse {
  status: string;
  summary: BatteryHealthSummary;
  wear_history: WearHistoryItem[];
  ml_model_info: Record<string, unknown>;
  tips: string[];
}

export interface AnalyticsResponse {
  status: string;
  session_count: number;
  total_saved_usd: number;
  wear_trend: { date: string; wear_score: number; rating: string }[];
  savings_trend: { date: string; savings_percent: number; optimized_cost: number; normal_cost: number }[];
  charging_pattern: { hour: string; count: number }[];
  soc_distribution: { range: string; count: number }[];
}
