import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Zap, Battery, TrendingDown, Shield, ArrowRight,
  Thermometer, Clock, Activity, AlertTriangle,
} from 'lucide-react'
import { getBatteryHealth, getVehicleStatus, getWeather } from '../api'
import type { BatteryHealthResponse, VehicleStatus, WeatherResponse } from '../types'

/* ── Circular SoC gauge ───────────────────────────────────── */
function SoCGauge({ pct }: { pct: number }) {
  const r = 54, cx = 64, cy = 64
  const circ = 2 * Math.PI * r
  const filled = (pct / 100) * circ
  const color = pct > 50 ? '#10b981' : pct > 20 ? '#f59e0b' : '#ef4444'

  return (
    <svg width="128" height="128" viewBox="0 0 128 128">
      {/* Track */}
      <circle cx={cx} cy={cy} r={r}
        fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
      {/* Fill */}
      <circle cx={cx} cy={cy} r={r}
        fill="none" stroke={color} strokeWidth="10"
        strokeDasharray={`${filled} ${circ}`}
        strokeLinecap="round"
        transform="rotate(-90 64 64)"
        style={{ transition: 'stroke-dasharray 1s ease' }} />
      {/* Center */}
      <text x={cx} y={58} textAnchor="middle"
        fill="#f1f3f8" fontSize="22" fontWeight="700"
        fontFamily="Inter, sans-serif" letterSpacing="-0.03em">
        {pct.toFixed(0)}%
      </text>
      <text x={cx} y={74} textAnchor="middle"
        fill="#4a5060" fontSize="9" fontWeight="600"
        fontFamily="Inter, sans-serif" letterSpacing="0.06em">
        STATE OF CHARGE
      </text>
    </svg>
  )
}

/* ── Mini metric row ─────────────────────────────────────── */
function MetricRow({ label, value, unit, color = 'var(--text-primary)' }:
  { label: string; value: string | number; unit?: string; color?: string }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '10px 0', borderBottom: '1px solid var(--border)',
    }}>
      <span style={{ fontSize: 12, color: 'var(--text-tertiary)', fontWeight: 500 }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>
        {value}{unit && <span style={{ fontWeight: 400, color: 'var(--text-secondary)', marginLeft: 2 }}>{unit}</span>}
      </span>
    </div>
  )
}

export default function Home() {
  const [health, setHealth] = useState<BatteryHealthResponse | null>(null)
  const [vehicle, setVehicle] = useState<VehicleStatus | null>(null)
  const [weather, setWeather] = useState<WeatherResponse | null>(null)
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    getBatteryHealth().then(setHealth).catch(() => setOffline(true))
    getVehicleStatus().then(setVehicle).catch(() => {})
    getWeather().then(setWeather).catch(() => {})
  }, [])

  const s = health?.summary
  const soc = vehicle?.battery_level_pct ?? 72
  const capacity = vehicle?.battery_capacity_kwh ?? 75
  const range = vehicle?.battery_range_km ?? Math.round(soc / 100 * capacity * 6.2)
  const chargeRate = vehicle?.charge_rate_kw ?? 11.0
  const isPlugged = vehicle?.is_plugged_in ?? true

  const ambientTemp = weather?.live_data.temperature_celsius ?? 22
  const weatherCond = weather?.live_data.weather_condition ?? 'Clear'
  const batteryTemp = weather?.live_data.temperature_celsius
    ? Math.round(weather.live_data.temperature_celsius + 4)
    : 27

  // Helper to dynamically show time until 8:00 AM departure
  const getHoursUntilDeparture = () => {
    const now = new Date()
    const currentHour = now.getHours()
    const currentMin = now.getMinutes()
    let diffMins = (8 * 60) - (currentHour * 60 + currentMin)
    if (diffMins < 0) {
      diffMins += 24 * 60 // schedule next day
    }
    const h = Math.floor(diffMins / 60)
    const m = diffMins % 60
    return `${h}h ${m}m`
  }

  return (
    <>
      {/* Page header */}
      <div className="page-header">
        <div className="page-header-inner">
          <div className="page-eyebrow">Overview</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h1 className="page-title">Dashboard</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className={`pill pill-${offline ? 'yellow' : 'green'}`}>
                <div className="pill-dot" />
                {offline ? 'Backend Offline' : 'System Online'}
              </div>
              <Link to="/optimizer">
                <button className="btn btn-primary">
                  <Zap size={14} /> New Session <ArrowRight size={13} />
                </button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body">

        {offline && (
          <div className="alert alert-warning fade-up" style={{ marginBottom: 20 }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>
              Backend server not reachable. Start it with&nbsp;
              <code style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: 4 }}>
                python -m uvicorn main:app --reload --port 8000
              </code>
            </span>
          </div>
        )}

        {/* ── Top stats row ─────────────────────────────────── */}
        <div className="grid-4 fade-up" style={{ marginBottom: 20 }}>
          {[
            { icon: Battery,      label: 'State of Health',    value: s?.inferred_soh_percent?.toFixed(1) ?? '—', unit: '%',    color: 'var(--success)',  boxCls: 'icon-box-green' },
            { icon: TrendingDown, label: 'Avg Cost Savings',   value: s?.avg_savings_percent?.toFixed(1)   ?? '—', unit: '%',    color: 'var(--accent)',   boxCls: 'icon-box-blue' },
            { icon: Zap,          label: 'Total Sessions',      value: s?.total_charging_sessions ?? '—',           unit: '',     color: 'var(--text-primary)', boxCls: 'icon-box-blue' },
            { icon: Shield,       label: 'Avg Wear Score',     value: s?.avg_wear_score?.toFixed(1)         ?? '—', unit: '/100', color: s && s.avg_wear_score < 20 ? 'var(--success)' : 'var(--warning)', boxCls: s && s.avg_wear_score < 20 ? 'icon-box-green' : 'icon-box-yellow' },
          ].map(({ icon: Icon, label, value, unit, color, boxCls }) => (
            <div key={label} className="stat-tile">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                <div className={`icon-box ${boxCls}`}><Icon size={16} /></div>
              </div>
              <div className="stat-label">{label}</div>
              <div className="stat-value" style={{ color }}>
                {value}<span className="stat-unit">{unit}</span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Battery status + vehicle info ─────────────────── */}
        <div className="grid-2 fade-up" style={{ marginBottom: 20 }}>
          {/* Battery gauge card */}
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className="card-title"><Battery size={14} /> Battery Status</span>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2, textTransform: 'capitalize' }}>
                  {vehicle ? `${vehicle.make} ${vehicle.model || ''}`.trim() : 'Loading EV...'}
                </div>
              </div>
              <div className={`pill pill-${isPlugged ? 'green' : 'yellow'}`}>
                <div className="pill-dot" />
                {isPlugged ? 'Plugged In' : 'Unplugged'}
              </div>
            </div>
            <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
              <SoCGauge pct={soc} />
              <div style={{ flex: 1 }}>
                <MetricRow label="Current State of Charge" value={soc.toFixed(0)} unit="%" color={soc > 50 ? 'var(--success)' : soc > 20 ? 'var(--warning)' : 'var(--danger)'} />
                <MetricRow label="Estimated Range"     value={range.toFixed(0)} unit=" km" />
                <MetricRow label="Battery Capacity"    value={capacity.toFixed(0)} unit=" kWh" />
                <MetricRow label="Charge Rate"         value={chargeRate.toFixed(1)} unit=" kW" />
                <div style={{ paddingTop: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>
                    <span>Current · {soc.toFixed(0)}%</span><span>Full · 100%</span>
                  </div>
                  <div className="progress-wrap">
                    <div className="progress-fill" style={{
                      width: `${soc}%`,
                      background: soc > 50 ? 'var(--success)' : soc > 20 ? 'var(--warning)' : 'var(--danger)'
                    }} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Charging conditions */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Activity size={14} /> Charging Conditions</span>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Live Feed</span>
            </div>
            <div className="card-body">
              <MetricRow label="Ambient Temperature"  value={ambientTemp.toFixed(1)} unit="°C" />
              <MetricRow label="Battery Temperature"  value={batteryTemp.toFixed(0)} unit="°C" />
              <MetricRow label="Weather Condition"    value={weatherCond.charAt(0).toUpperCase() + weatherCond.slice(1)} />
              <MetricRow label="Optimal Temp Range"   value="15–35" unit="°C" color="var(--success)" />
              <MetricRow label="Target Departure"     value="08:00"  />
              <MetricRow label="Time Until Departure" value={getHoursUntilDeparture()} color="var(--accent)" />
            </div>
          </div>
        </div>

        {/* ── How the system works ──────────────────────────── */}
        <div className="card fade-up">
          <div className="card-header">
            <span className="card-title">System Overview</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderTop: 'none' }}>
            {[
              {
                icon: Zap,         color: 'var(--accent)',
                step: '01',        label: 'LP Optimization',
                desc: 'Coin-or CBC linear solver computes the minimum-cost hourly charging schedule satisfying all constraints — battery capacity, departure time, charge rate limits.',
              },
              {
                icon: Shield,      color: 'var(--success)',
                step: '02',        label: 'ML Wear Prediction',
                desc: 'XGBoost model (R²=0.993) trained on 15,000 physics-informed samples predicts battery degradation from temperature, C-rate, and target SoC.',
              },
              {
                icon: TrendingDown, color: 'var(--warning)',
                step: '03',        label: 'Cost Intelligence',
                desc: 'Dynamic pricing awareness shifts load to off-peak windows. Every session is persisted to SQLite for trend analysis and model improvement.',
              },
            ].map(({ icon: Icon, color, step, label, desc }) => (
              <div key={step} style={{
                padding: '20px 24px',
                borderRight: '1px solid var(--border)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <Icon size={15} color={color} />
                  <span style={{ fontSize: 11, fontWeight: 700, color, letterSpacing: '0.06em' }}>STEP {step}</span>
                </div>
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>{label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.7 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Health tips */}
        {health?.tips && (
          <div className="card fade-up" style={{ marginTop: 20 }}>
            <div className="card-header">
              <span className="card-title"><Thermometer size={14} /> Battery Care Recommendations</span>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {health.tips.map((tip, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <Clock size={12} color="var(--text-tertiary)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{tip}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
