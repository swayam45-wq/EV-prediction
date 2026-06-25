import axios from 'axios'
import type {
  ChargingRequest, ChargingRecommendation,
  BatteryHealthResponse, AnalyticsResponse,
  WeatherResponse, PricesResponse, VehicleStatus,
} from './types'

const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

export const getRecommendation = (payload: ChargingRequest): Promise<ChargingRecommendation> =>
  api.post<ChargingRecommendation>('/api/recommend', payload).then(r => r.data)

export const getBatteryHealth = (): Promise<BatteryHealthResponse> =>
  api.get<BatteryHealthResponse>('/api/battery-health').then(r => r.data)

export const getAnalytics = (limit = 30): Promise<AnalyticsResponse> =>
  api.get<AnalyticsResponse>(`/api/analytics?limit=${limit}`).then(r => r.data)

/** Fetch live weather. Pass city or leave blank for adjustment-only mode. */
export const getWeather = (params?: {
  city?: string; lat?: number; lon?: number
  temp?: number; condition?: string
}): Promise<WeatherResponse> =>
  api.get<WeatherResponse>('/api/weather', { params }).then(r => r.data)

/** Fetch 24h electricity price schedule for a given region. */
export const getPrices = (region = 'US_CA', source = 'auto'): Promise<PricesResponse> =>
  api.get<PricesResponse>('/api/prices', { params: { region, source } }).then(r => r.data)

export const getVehicleStatus = (provider?: string): Promise<VehicleStatus> =>
  api.get<VehicleStatus>('/api/vehicle/status', { params: { provider } }).then(r => r.data)

export const connectVehicle = (): Promise<{
  status: string;
  authorization_url?: string;
  message?: string;
  docs_url?: string;
  demo_url?: string;
}> => api.get('/api/vehicle/connect').then(r => r.data)

export const disconnectVehicle = (): Promise<{
  status: string;
  message: string;
}> => api.delete('/api/vehicle/disconnect').then(r => r.data)

export const getHealth = () =>
  api.get('/health').then(r => r.data)

export default api
