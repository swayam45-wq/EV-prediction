import { useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { Zap, Clock, TrendingDown, Shield, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { getRecommendation } from '../api'
import type { ChargingRequest, ChargingRecommendation, ElectricityPrice } from '../types'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler)

/* ── Default electricity prices (time-of-use rate) ────────── */
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

/* ── Small input field component ───────────────────────────── */
function Field({ label, tip, children }: { label: string; tip?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="input-label tooltip" data-tip={tip}>{label}</label>
      {children}
    </div>
  )
}

/* ── Wear score ring ────────────────────────────────────────── */
function WearRing({ score, rating }: { score: number; rating: string }) {
  const color = rating === 'Low' ? '#06d6a0' : rating === 'Medium' ? '#f59e0b' : '#ef4444'
  const r = 50, circumference = 2 * Math.PI * r
  const dash = ((100 - score) / 100) * circumference
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <svg width="130" height="130" viewBox="0 0 130 130" style={{ filter: `drop-shadow(0 0 12px ${color}50)` }}>
        <circle cx={65} cy={65} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
        <circle cx={65} cy={65} r={r} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={`${circumference - dash} ${circumference}`}
          strokeLinecap="round" transform="rotate(-90 65 65)"
          style={{ transition: 'stroke-dasharray 1s ease' }} />
        <text x={65} y={60} textAnchor="middle" fill="#f0f4ff"
          fontSize="22" fontWeight="700" fontFamily="Space Grotesk, sans-serif">{score.toFixed(0)}</text>
        <text x={65} y={78} textAnchor="middle" fill="#8b9dc3" fontSize="10">/ 100</text>
      </svg>
      <div className={`badge badge-${rating === 'Low' ? 'green' : rating === 'Medium' ? 'yellow' : 'red'}`}>
        {rating} Wear
      </div>
    </div>
  )
}

export default function Optimizer() {
  const [form, setForm] = useState({
    current_soc: 30,
    target_soc: 80,
    battery_capacity_kwh: 75,
    max_charge_rate_kw: 11,
    battery_health_soh: 95,
    departure_time: '08:00',
    temperature_celsius: 22,
    weather_condition: 'clear',
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
      const data = await getRecommendation(payload)
      setResult(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(`Backend error: ${msg}. Make sure the FastAPI server is running on port 8000.`)
    } finally {
      setLoading(false)
    }
  }

  /* Chart data — mixed bar+line chart */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartData: any = result ? {
    labels: result.schedule.map(s => s.hour),
    datasets: [
      {
        label: 'Energy Charged (kWh)',
        data: result.schedule.map(s => s.energy_kwh),
        backgroundColor: result.schedule.map(s =>
          s.is_charging ? 'rgba(59,130,246,0.8)' : 'rgba(255,255,255,0.05)'
        ),
        borderRadius: 6,
        yAxisID: 'y',
      },
      {
        label: 'Price ($/kWh)',
        data: DEFAULT_PRICES.map(p => p.price),
        type: 'line' as const,
        borderColor: 'rgba(245,158,11,0.7)',
        backgroundColor: 'rgba(245,158,11,0.08)',
        borderWidth: 2,
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
      legend: { labels: { color: '#8b9dc3', font: { size: 12 } } },
      title: { display: false },
    },
    scales: {
      x: { ticks: { color: '#4a5a7a', maxRotation: 45 }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: {
        type: 'linear' as const, position: 'left' as const,
        ticks: { color: '#8b9dc3' }, grid: { color: 'rgba(255,255,255,0.04)' },
        title: { display: true, text: 'kWh', color: '#8b9dc3' },
      },
      y1: {
        type: 'linear' as const, position: 'right' as const,
        ticks: { color: '#f59e0b' }, grid: { drawOnChartArea: false },
        title: { display: true, text: '$/kWh', color: '#f59e0b' },
      },
    },
  }

  return (
    <div className="page">
      <h1 className="page-title fade-in-up">Charging Optimizer</h1>
      <p className="page-subtitle fade-in-up delay-1">Enter your vehicle details and we'll compute the optimal low-cost charging schedule.</p>

      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 24, alignItems: 'start' }}>

        {/* ── INPUT FORM ────────────────────────────────────── */}
        <form className="glass-card fade-in-up delay-1" style={{ padding: 28 }} onSubmit={handleSubmit}>
          <h2 style={{ fontWeight: 700, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Zap size={18} color="#3b82f6" /> Vehicle Details
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <Field label="Current SoC (%)" tip="How much charge is in your battery right now">
              <input className="input-field" type="number" min={1} max={99} value={form.current_soc}
                onChange={e => set('current_soc', +e.target.value)} />
            </Field>

            <Field label="Target SoC (%)" tip="How much charge do you want to reach">
              <input className="input-field" type="number" min={1} max={100} value={form.target_soc}
                onChange={e => set('target_soc', +e.target.value)} />
            </Field>

            {/* Live SoC bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 4 }}>
                <span>Current: {form.current_soc}%</span><span>Target: {form.target_soc}%</span>
              </div>
              <div style={{ height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.06)', position: 'relative', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${form.current_soc}%`, background: 'linear-gradient(90deg,#3b82f6,#06d6a0)', borderRadius: 4, transition: 'width 0.3s' }} />
                <div style={{ position: 'absolute', top: 0, height: '100%', left: `${form.current_soc}%`, width: `${form.target_soc - form.current_soc}%`, background: 'rgba(59,130,246,0.2)', borderRadius: '0 4px 4px 0' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Capacity (kWh)">
                <input className="input-field" type="number" min={10} max={200} value={form.battery_capacity_kwh}
                  onChange={e => set('battery_capacity_kwh', +e.target.value)} />
              </Field>
              <Field label="Max Rate (kW)">
                <input className="input-field" type="number" min={1} max={350} value={form.max_charge_rate_kw}
                  onChange={e => set('max_charge_rate_kw', +e.target.value)} />
              </Field>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Battery Health (%)">
                <input className="input-field" type="number" min={50} max={100} value={form.battery_health_soh}
                  onChange={e => set('battery_health_soh', +e.target.value)} />
              </Field>
              <Field label="Departure Time">
                <input className="input-field" type="time" value={form.departure_time}
                  onChange={e => set('departure_time', e.target.value)} />
              </Field>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="Temperature (°C)">
                <input className="input-field" type="number" min={-20} max={50} value={form.temperature_celsius}
                  onChange={e => set('temperature_celsius', +e.target.value)} />
              </Field>
              <Field label="Weather">
                <select className="input-field" value={form.weather_condition}
                  onChange={e => set('weather_condition', e.target.value)}>
                  {['clear', 'cloudy', 'rain', 'snow', 'hot'].map(w => <option key={w}>{w}</option>)}
                </select>
              </Field>
            </div>

            {/* Collapsible price editor */}
            <button type="button"
              style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: 'var(--clr-primary)', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600, padding: 0 }}
              onClick={() => setShowPrices(v => !v)}>
              {showPrices ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              {showPrices ? 'Hide' : 'Show'} Electricity Prices
            </button>

            {showPrices && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, maxHeight: 200, overflowY: 'auto' }}>
                {DEFAULT_PRICES.map((p, i) => (
                  <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--clr-text-muted)', width: 40 }}>{p.hour}</span>
                    <span style={{ color: '#f59e0b' }}>${p.price.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="divider" />

            {error && (
              <div style={{ padding: '10px 14px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#ef4444', fontSize: '0.82rem' }}>
                {error}
              </div>
            )}

            <button className="btn-primary" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
              {loading ? <><Loader2 size={18} style={{ animation: 'spin-slow 0.8s linear infinite' }} /> Computing...</> : <><Zap size={18} /> Optimize Schedule</>}
            </button>
          </div>
        </form>

        {/* ── RESULTS ──────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {!result && !loading && (
            <div className="glass-card fade-in-up" style={{
              padding: 64, textAlign: 'center',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16,
            }}>
              <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(59,130,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Zap size={36} color="#3b82f6" />
              </div>
              <p style={{ color: 'var(--clr-text-muted)', fontSize: '1rem' }}>
                Fill in your vehicle details and click <strong style={{ color: 'var(--clr-text)' }}>Optimize Schedule</strong> to see results.
              </p>
            </div>
          )}

          {loading && (
            <div className="glass-card" style={{ padding: 64, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
              <div className="spinner" />
              <p style={{ color: 'var(--clr-text-muted)' }}>Running LP optimizer + ML model...</p>
            </div>
          )}

          {result && (
            <>
              {/* Summary row */}
              <div className="grid-4 fade-in-up">
                <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                  <p style={{ fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Start</p>
                  <p style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.6rem', fontWeight: 700, color: '#06d6a0' }}>{result.start_charging ?? '—'}</p>
                </div>
                <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                  <p style={{ fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Stop</p>
                  <p style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.6rem', fontWeight: 700, color: '#3b82f6' }}>{result.stop_charging ?? '—'}</p>
                </div>
                <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                  <p style={{ fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Energy</p>
                  <p style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.6rem', fontWeight: 700 }}>{result.total_energy_kwh?.toFixed(1)} <span style={{ fontSize: '0.9rem', color: 'var(--clr-text-muted)' }}>kWh</span></p>
                </div>
                <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                  <p style={{ fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Savings</p>
                  <p style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.6rem', fontWeight: 700, color: '#06d6a0' }}>
                    {result.cost_analysis?.savings_percent.toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Chart */}
              {chartData && (
                <div className="glass-card fade-in-up delay-1" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Clock size={18} color="#3b82f6" /> Charging Schedule
                  </h3>
                  <Bar data={chartData} options={chartOptions} />
                </div>
              )}

              {/* Cost + Wear row */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* Cost */}
                <div className="glass-card fade-in-up delay-2" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <TrendingDown size={18} color="#06d6a0" /> Cost Analysis
                  </h3>
                  {result.cost_analysis && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {[
                        { label: 'Normal Cost', val: `$${result.cost_analysis.normal_cost.toFixed(3)}`, color: 'var(--clr-text-muted)' },
                        { label: 'Optimized Cost', val: `$${result.cost_analysis.optimized_cost.toFixed(3)}`, color: '#06d6a0' },
                        { label: 'You Save', val: `$${result.cost_analysis.savings_dollar.toFixed(3)}  (${result.cost_analysis.savings_percent.toFixed(1)}%)`, color: '#3b82f6' },
                      ].map(row => (
                        <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
                          <span style={{ color: 'var(--clr-text-muted)', fontSize: '0.88rem' }}>{row.label}</span>
                          <span style={{ fontWeight: 700, color: row.color }}>{row.val}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Wear */}
                <div className="glass-card fade-in-up delay-3" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Shield size={18} color="#a78bfa" /> Battery Wear (ML)
                  </h3>
                  {result.wear_estimate && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                      <WearRing score={result.wear_estimate.total_score} rating={result.wear_estimate.rating} />
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {[
                          { label: 'Temp Impact', val: result.wear_estimate.temperature_impact },
                          { label: 'SoC Stress', val: result.wear_estimate.high_soc_stress },
                          { label: 'Fast Charge', val: result.wear_estimate.fast_charging_penalty },
                        ].map(row => (
                          <div key={row.label}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 3 }}>
                              <span>{row.label}</span><span>{row.val.toFixed(1)}</span>
                            </div>
                            <div style={{ height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.06)' }}>
                              <div style={{ height: '100%', width: `${Math.min(row.val, 100)}%`, background: '#a78bfa', borderRadius: 3, transition: 'width 0.6s' }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Explanations */}
              <div className="glass-card fade-in-up delay-4" style={{ padding: 24 }}>
                <h3 style={{ fontWeight: 700, marginBottom: 16 }}>AI Explanations</h3>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.explanations.map((e, i) => (
                    <li key={i} style={{ display: 'flex', gap: 10, color: 'var(--clr-text-muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                      <span style={{ color: '#3b82f6', flexShrink: 0, fontWeight: 700 }}>→</span> {e}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Health advice */}
              {result.battery_health_advice.length > 0 && (
                <div className="glass-card fade-in-up delay-4" style={{ padding: 24, borderColor: 'rgba(6,214,160,0.2)' }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 16, color: '#06d6a0' }}>Battery Health Advice</h3>
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {result.battery_health_advice.map((a, i) => (
                      <li key={i} style={{ display: 'flex', gap: 10, color: 'var(--clr-text-muted)', fontSize: '0.88rem' }}>
                        <span style={{ color: '#06d6a0' }}>✓</span> {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
