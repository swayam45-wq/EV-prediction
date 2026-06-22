import axios from 'axios'
import type { ChargingRequest, ChargingRecommendation, BatteryHealthResponse, AnalyticsResponse } from './types'

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

export const getHealth = () =>
  api.get('/health').then(r => r.data)

export default api
