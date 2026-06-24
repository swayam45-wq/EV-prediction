import { useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { Zap, Clock, TrendingDown, Shield, ChevronDown, ChevronUp, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { getRecommendation } from '../api'
import type { ChargingRequest, ChargingRecommendation, ElectricityPrice } from '../types'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler)

const DEFAULT_PRICES: ElectricityPrice[] = [
  { hour: '00:00', price: 0.08 }, { hour: '01:00', price: 0.07 },
  { hour: '02:00', price: 0.07 }, { hour: '03:00', price: 0.06 },
  { hour: '04:00', price: 0.06 }, { hour: '05:00', price: 0.07 },
  { hour: '06:00', price: 0.10 }, { hour: '07:00', price: 0.15 },
  { hour: '08:00', price: 0.18 }, { hour: '09:00', price: 0.17 },
  { hour: '10:00', price: 0.15 }, { hour: '11:00', price: 0.14 },
  { hour: '12:00', price: 0.13 }, { hour: '13:00', price: 0.12 },
  { hour: '14:00', price: 0.13 }, { hour: '15:00', price: 0.15 },
  { hour: '16:00', price: 0.18 }, { hour: '17:00', price: 0.22 },
  { hour: '18:00', price: 0.24 }, { hour: '19:00', price: 0.22 },
  { hour: '20:00', price: 0.18 }, { hour: '21:00', price: 0.15 },
  { hour: '22:00', price: 0.12 }, { hour: '23:00', price: 0.10 },
]

function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="form-label">{label}</label>
      {children}
    </div>
  )
}

function WearBar({ label, value }: { label: string; value: number }) {
  const color = value < 15 ? 'var(--success)' : value < 35 ? 'var(--warning)' : 'var(--danger)'
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>
        <span>{label}</span>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-secondary)' }}>{value.toFixed(1)}</span>
      </div>
      <div className="progress-wrap">
        <div className="progress-fill" style={{ width: `${Math.min(value, 100)}%`, background: color }} />
      </div>
    </div>
  )
}

export default function Optimizer() {
  const [form, setForm] = useState({
    current_soc: 30, target_soc: 80,
    battery_capacity_kwh: 75, max_charge_rate_kw: 11,
    battery_health_soh: 95, departure_time: '08:00',
    temperature_celsius: 22, weather_condition: 'clear',
    charging_efficiency: 0.90,
  })
  const [result, setResult] = useState<ChargingRecommendation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showPrices, setShowPrices] = useState(false)

  const set = (k: string, v: number | string) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError(null); setResult(null)
    try {
      const payload: ChargingRequest = { ...form, electricity_prices: DEFAULT_PRICES }
      setResult(await getRecommendation(payload))
    } catch {
      setError('Could not reach backend. Ensure the FastAPI server is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  const delta = form.target_soc - form.current_soc

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartData: any = result ? {
    labels: result.schedule.map(s => s.hour),
    datasets: [
      {
        label: 'Energy Charged (kWh)',
        data: result.schedule.map(s => s.energy_kwh),
        backgroundColor: result.schedule.map(s =>
          s.is_charging ? 'rgba(14,165,233,0.85)' : 'rgba(255,255,255,0.04)'
        ),
        borderRadius: 4,
        yAxisID: 'y',
      },
      {
        label: 'Price ($/kWh)',
        data: DEFAULT_PRICES.map(p => p.price),
        type: 'line' as const,
        borderColor: 'rgba(245,158,11,0.6)',
        backgroundColor: 'rgba(245,158,11,0.05)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: true,
        yAxisID: 'y1',
      },
    ],
  } : null

  const chartOptions = {
    responsive: true,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: { labels: { color: '#8b919e', font: { size: 11 }, boxWidth: 12 } },
      title: { display: false },
    },
    scales: {
      x: {
        ticks: { color: '#4a5060', font: { size: 11 }, maxRotation: 45 },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        type: 'linear' as const, position: 'left' as const,
        ticks: { color: '#8b919e', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
        title: { display: true, text: 'kWh', color: '#8b919e', font: { size: 11 } },
      },
      y1: {
        type: 'linear' as const, position: 'right' as const,
        ticks: { color: '#f59e0b', font: { size: 11 } },
        grid: { drawOnChartArea: false },
        title: { display: true, text: '$/kWh', color: '#f59e0b', font: { size: 11 } },
      },
    },
  }

  const wear = result?.wear_estimate

  return (
    <>
      {/* Page header */}
      <div className="page-header">
        <div className="page-header-inner">
          <div className="page-eyebrow">Charging</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h1 className="page-title">Schedule Optimizer</h1>
            {result && (
              <div className={`pill pill-${result.status === 'optimal' ? 'green' : 'red'}`}>
                {result.status === 'optimal'
                  ? <><CheckCircle size={10} /> Optimal schedule found</>
                  : <><AlertCircle size={10} /> Infeasible — adjust inputs</>
                }
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20, alignItems: 'start' }}>

          {/* ── INPUT PANEL ─────────────────────────────────── */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Battery section */}
            <div className="card">
              <div className="card-header">
                <span className="card-title"><Zap size={14} /> Vehicle Parameters</span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>

                {/* SoC range visual */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <FormRow label="Current SoC (%)">
                      <input className="form-input" type="number" min={1} max={99}
                        value={form.current_soc}
                        onChange={e => set('current_soc', +e.target.value)}
                        style={{ width: 100 }} />
                    </FormRow>
                    <FormRow label="Target SoC (%)">
                      <input className="form-input" type="number" min={1} max={100}
                        value={form.target_soc}
                        onChange={e => set('target_soc', +e.target.value)}
                        style={{ width: 100 }} />
                    </FormRow>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 5 }}>
                    Charge needed: <span style={{ color: 'var(--accent)', fontWeight: 700 }}>+{Math.max(0, delta)}%</span>
                  </div>
                  <div className="progress-wrap">
                    <div className="progress-fill" style={{ width: `${form.current_soc}%`, background: 'var(--text-tertiary)' }} />
                  </div>
                  <div style={{ position: 'relative', marginTop: 2 }}>
                    <div className="progress-wrap">
                      <div className="progress-fill" style={{
                        width: `${form.target_soc}%`,
                        background: 'linear-gradient(90deg, var(--text-tertiary) 0%, var(--accent) 100%)'
                      }} />
                    </div>
                  </div>
                </div>

                <div className="grid-2">
                  <FormRow label="Capacity (kWh)">
                    <input className="form-input" type="number" min={10} max={200}
                      value={form.battery_capacity_kwh}
                      onChange={e => set('battery_capacity_kwh', +e.target.value)} />
                  </FormRow>
                  <FormRow label="Max Rate (kW)">
                    <input className="form-input" type="number" min={1} max={350}
                      value={form.max_charge_rate_kw}
                      onChange={e => set('max_charge_rate_kw', +e.target.value)} />
                  </FormRow>
                </div>

                <div className="grid-2">
                  <FormRow label="SoH (%)">
                    <input className="form-input" type="number" min={50} max={100}
                      value={form.battery_health_soh}
                      onChange={e => set('battery_health_soh', +e.target.value)} />
                  </FormRow>
                  <FormRow label="Departure">
                    <input className="form-input" type="time"
                      value={form.departure_time}
                      onChange={e => set('departure_time', e.target.value)} />
                  </FormRow>
                </div>
              </div>
            </div>

            {/* Environment section */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Environment</span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
                <div className="grid-2">
                  <FormRow label="Temperature (°C)">
                    <input className="form-input" type="number" min={-20} max={50}
                      value={form.temperature_celsius}
                      onChange={e => set('temperature_celsius', +e.target.value)} />
                  </FormRow>
                  <FormRow label="Weather">
                    <select className="form-select"
                      value={form.weather_condition}
                      onChange={e => set('weather_condition', e.target.value)}>
                      {['clear', 'cloudy', 'rain', 'snow', 'hot'].map(w => <option key={w}>{w}</option>)}
                    </select>
                  </FormRow>
                </div>
              </div>
            </div>

            {/* Prices toggle */}
            <div className="card">
              <button type="button" className="card-header"
                style={{ width: '100%', cursor: 'pointer', background: 'none', border: 'none', color: 'inherit' }}
                onClick={() => setShowPrices(v => !v)}>
                <span className="card-title">Electricity Prices</span>
                {showPrices ? <ChevronUp size={14} color="var(--text-tertiary)" /> : <ChevronDown size={14} color="var(--text-tertiary)" />}
              </button>
              {showPrices && (
                <div className="card-body">
                  <table style={{ width: '100%' }}>
                    <tbody>
                      {DEFAULT_PRICES.map((p, i) => (
                        <tr key={i}>
                          <td className="mono" style={{ color: 'var(--text-tertiary)', padding: '2px 0', fontSize: 12 }}>{p.hour}</td>
                          <td style={{ textAlign: 'right', padding: '2px 0' }}>
                            <div className="progress-wrap" style={{ display: 'inline-block', width: 60, height: 3, marginRight: 6, verticalAlign: 'middle' }}>
                              <div className="progress-fill" style={{ width: `${(p.price / 0.25) * 100}%`, background: p.price > 0.18 ? 'var(--danger)' : p.price < 0.09 ? 'var(--success)' : 'var(--warning)' }} />
                            </div>
                            <span className="mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>${p.price.toFixed(2)}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {error && (
              <div className="alert alert-error">
                <AlertCircle size={14} style={{ flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}

            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading
                ? <><Loader2 size={14} style={{ animation: 'spin 0.7s linear infinite' }} /> Computing optimal schedule...</>
                : <><Zap size={14} /> Run Optimizer</>
              }
            </button>
          </form>

          {/* ── RESULTS PANEL ────────────────────────────────── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {!result && !loading && (
              <div className="card" style={{ padding: '60px 24px', textAlign: 'center' }}>
                <div style={{
                  width: 48, height: 48, borderRadius: '50%',
                  background: 'var(--bg-overlay)', border: '1px solid var(--border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 14px',
                }}>
                  <Zap size={22} color="var(--text-tertiary)" />
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                  No schedule computed yet
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                  Configure your vehicle parameters and click Run Optimizer.
                </div>
              </div>
            )}

            {loading && (
              <div className="card" style={{ padding: '60px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
                <div className="spinner-lg" />
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Running LP solver + XGBoost ML model...</span>
              </div>
            )}

            {result && (
              <>
                {/* Summary tiles */}
                <div className="grid-4 fade-up">
                  {[
                    { label: 'Start Time',    value: result.start_charging ?? '—',                       color: 'var(--success)' },
                    { label: 'Stop Time',     value: result.stop_charging  ?? '—',                       color: 'var(--accent)' },
                    { label: 'Energy Added',  value: `${result.total_energy_kwh?.toFixed(1) ?? '—'} kWh`, color: 'var(--text-primary)' },
                    { label: 'Cost Savings',  value: `${result.cost_analysis?.savings_percent.toFixed(1) ?? '—'}%`, color: 'var(--success)' },
                  ].map(t => (
                    <div key={t.label} className="stat-tile">
                      <div className="stat-label">{t.label}</div>
                      <div className="stat-value mono" style={{ fontSize: 22, color: t.color }}>{t.value}</div>
                    </div>
                  ))}
                </div>

                {/* Schedule chart */}
                {chartData && (
                  <div className="card fade-up">
                    <div className="card-header">
                      <span className="card-title"><Clock size={14} /> Charging Schedule</span>
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Blue = charging active · Line = price</span>
                    </div>
                    <div className="card-body">
                      <Bar data={chartData} options={chartOptions} />
                    </div>
                  </div>
                )}

                {/* Cost analysis + Wear */}
                <div className="grid-2 fade-up">
                  {/* Cost */}
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title"><TrendingDown size={14} /> Cost Breakdown</span>
                    </div>
                    {result.cost_analysis && (
                      <div className="card-body">
                        <table className="data-table">
                          <tbody>
                            {[
                              { label: 'Normal (unoptimized)', val: `$${result.cost_analysis.normal_cost.toFixed(4)}`,    color: 'var(--text-secondary)' },
                              { label: 'Optimized cost',       val: `$${result.cost_analysis.optimized_cost.toFixed(4)}`,  color: 'var(--accent)' },
                              { label: 'Savings',              val: `$${result.cost_analysis.savings_dollar.toFixed(4)}`,  color: 'var(--success)' },
                              { label: 'Savings %',            val: `${result.cost_analysis.savings_percent.toFixed(1)}%`, color: 'var(--success)' },
                            ].map(r => (
                              <tr key={r.label}>
                                <td style={{ color: 'var(--text-tertiary)', borderBottom: '1px solid var(--border)', padding: '9px 0' }}>{r.label}</td>
                                <td style={{ textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: r.color, borderBottom: '1px solid var(--border)', padding: '9px 0' }}>{r.val}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Wear */}
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title"><Shield size={14} /> Battery Wear (XGBoost)</span>
                      {wear && (
                        <div className={`pill pill-${wear.rating === 'Low' ? 'green' : wear.rating === 'Medium' ? 'yellow' : 'red'}`}>
                          {wear.rating}
                        </div>
                      )}
                    </div>
                    {wear && (
                      <div className="card-body">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                          <div style={{
                            width: 60, height: 60, borderRadius: '50%',
                            border: `3px solid ${wear.rating === 'Low' ? 'var(--success)' : wear.rating === 'Medium' ? 'var(--warning)' : 'var(--danger)'}`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <span style={{
                              fontSize: 17, fontWeight: 700,
                              color: wear.rating === 'Low' ? 'var(--success)' : wear.rating === 'Medium' ? 'var(--warning)' : 'var(--danger)',
                              fontFamily: 'JetBrains Mono, monospace',
                            }}>{wear.total_score.toFixed(0)}</span>
                          </div>
                          <div>
                            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 2 }}>Wear score out of 100</div>
                            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Lower is better · Powered by ML model</div>
                          </div>
                        </div>
                        <WearBar label="Temperature Impact"    value={wear.temperature_impact} />
                        <WearBar label="High SoC Stress"      value={wear.high_soc_stress} />
                        <WearBar label="Fast Charging Penalty" value={wear.fast_charging_penalty} />
                      </div>
                    )}
                  </div>
                </div>

                {/* Explanations */}
                <div className="card fade-up">
                  <div className="card-header">
                    <span className="card-title">Optimizer Explanations</span>
                  </div>
                  <div className="card-body">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {result.explanations.map((e, i) => (
                        <div key={i} style={{
                          display: 'flex', gap: 10, padding: '8px 12px',
                          background: 'var(--bg-overlay)', borderRadius: 6,
                          fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6,
                        }}>
                          <span style={{ color: 'var(--accent)', fontWeight: 700, flexShrink: 0 }}>{String(i + 1).padStart(2, '0')}</span>
                          {e}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Battery advice */}
                {result.battery_health_advice.length > 0 && (
                  <div className="card fade-up">
                    <div className="card-header">
                      <span className="card-title"><Shield size={14} /> Health Recommendations</span>
                    </div>
                    <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {result.battery_health_advice.map((a, i) => (
                        <div key={i} style={{ display: 'flex', gap: 9, fontSize: 12, color: 'var(--text-secondary)' }}>
                          <span style={{ color: 'var(--success)', flexShrink: 0 }}>✓</span> {a}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
