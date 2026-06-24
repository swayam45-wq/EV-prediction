import { useEffect, useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { Battery, Shield, Cpu, TrendingDown, AlertTriangle, Zap } from 'lucide-react'
import { getBatteryHealth } from '../api'
import type { BatteryHealthResponse } from '../types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

/* ── Arc SoH Gauge ───────────────────────────────────────── */
function SoHGauge({ soh }: { soh: number }) {
  const color = soh > 85 ? 'var(--success)' : soh > 70 ? 'var(--warning)' : 'var(--danger)'
  const label = soh > 85 ? 'Excellent' : soh > 70 ? 'Good' : 'Degraded'
  const pill  = soh > 85 ? 'pill-green' : soh > 70 ? 'pill-yellow' : 'pill-red'

  // 240° arc: starts at 150°, sweeps clockwise
  const r = 54, cx = 64, cy = 70
  const toRad = (d: number) => d * Math.PI / 180
  const startA = toRad(150)
  const sweep  = 240 * (soh / 100)
  const endA   = toRad(150 + sweep)
  const large  = sweep > 180 ? 1 : 0
  const pt     = (a: number) => [cx + r * Math.cos(a), cy + r * Math.sin(a)]
  const [sx, sy] = pt(startA)
  const [ex, ey] = pt(endA)
  const [tx, ty] = pt(toRad(150 + 240))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <svg width="128" height="120" viewBox="0 0 128 120">
        {/* Track */}
        <path
          d={`M ${pt(toRad(150)).join(' ')} A ${r} ${r} 0 1 1 ${tx} ${ty}`}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="9" strokeLinecap="round" />
        {/* Fill */}
        {soh > 0 && (
          <path
            d={`M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`}
            fill="none" stroke={color} strokeWidth="9" strokeLinecap="round"
            style={{ transition: 'all 1.2s ease' }} />
        )}
        {/* Value */}
        <text x={cx} y={cy - 4} textAnchor="middle"
          fill="#f1f3f8" fontSize="22" fontWeight="700"
          fontFamily="Inter, sans-serif" letterSpacing="-0.03em">
          {soh.toFixed(1)}%
        </text>
        <text x={cx} y={cy + 13} textAnchor="middle"
          fill="#4a5060" fontSize="9" fontWeight="600"
          fontFamily="Inter, sans-serif" letterSpacing="0.08em">
          STATE OF HEALTH
        </text>
      </svg>
      <div className={`pill ${pill}`}>
        <div className="pill-dot" /> {label}
      </div>
    </div>
  )
}

export default function BatteryHealth() {
  const [data, setData] = useState<BatteryHealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    getBatteryHealth()
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const history = data?.wear_history ?? []

  const lineData = {
    labels: history.map((_, i) => `#${i + 1}`),
    datasets: [{
      label: 'Wear Score',
      data: history.map(h => h.wear_score),
      borderColor: 'rgba(14,165,233,0.8)',
      backgroundColor: 'rgba(14,165,233,0.06)',
      borderWidth: 1.5, tension: 0.4, fill: true,
      pointBackgroundColor: history.map(h =>
        h.wear_rating === 'Low' ? '#10b981' : h.wear_rating === 'Medium' ? '#f59e0b' : '#ef4444'
      ),
      pointRadius: 4,
    }],
  }

  const lineOptions = {
    responsive: true,
    plugins: {
      legend: { labels: { color: '#8b919e', font: { size: 11 }, boxWidth: 12 } },
    },
    scales: {
      x: { ticks: { color: '#4a5060', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: {
        min: 0, max: 100,
        ticks: { color: '#8b919e', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
        title: { display: true, text: 'Wear Score', color: '#8b919e', font: { size: 11 } },
      },
    },
  }

  const s = data?.summary

  return (
    <>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-inner">
          <div className="page-eyebrow">Health Monitoring</div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h1 className="page-title">Battery Health</h1>
            {data && (
              <div className="pill pill-blue">
                <Cpu size={10} />
                {(data.ml_model_info as { status?: string }).status === 'ml_model_active'
                  ? 'XGBoost Active'
                  : 'Heuristic Mode'}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="page-body">
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
            <div className="spinner-lg" />
          </div>
        )}

        {error && (
          <div className="alert alert-warning fade-up" style={{ marginBottom: 20 }}>
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            Backend not reachable — start the FastAPI server on port 8000.
          </div>
        )}

        {data && (
          <>
            {/* SoH gauge + stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 16, marginBottom: 16 }}>
              {/* Gauge card */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '28px 20px', gap: 20 }}>
                <SoHGauge soh={s?.inferred_soh_percent ?? 0} />
                <div className="divider" style={{ width: '100%' }} />
                <div style={{ width: '100%' }}>
                  {[
                    { label: 'ML Model', value: (data.ml_model_info as { model_type?: string }).model_type ?? 'XGBoost' },
                    { label: 'Sessions',  value: s?.total_charging_sessions ?? 0 },
                  ].map(r => (
                    <div key={r.label} style={{
                      display: 'flex', justifyContent: 'space-between',
                      fontSize: 11, padding: '6px 0',
                      borderBottom: '1px solid var(--border)',
                      color: 'var(--text-tertiary)',
                    }}>
                      <span>{r.label}</span>
                      <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{r.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid-2" style={{ alignContent: 'start' }}>
                {[
                  { icon: Battery,      label: 'Total Sessions',       value: s?.total_charging_sessions ?? 0,               unit: '',    color: 'var(--accent)',   cls: 'icon-box-blue' },
                  { icon: TrendingDown, label: 'Avg Cost Savings',     value: `${(s?.avg_savings_percent ?? 0).toFixed(1)}`,  unit: '%',   color: 'var(--success)',  cls: 'icon-box-green' },
                  { icon: Shield,       label: 'Avg Wear Score',       value: `${(s?.avg_wear_score ?? 0).toFixed(1)}`,       unit: '/100',color: 'var(--warning)',  cls: 'icon-box-yellow' },
                  { icon: Zap,          label: 'Total Energy Charged', value: `${(s?.total_energy_charged_kwh ?? 0).toFixed(1)}`, unit: 'kWh', color: 'var(--text-primary)', cls: 'icon-box-blue' },
                ].map(({ icon: Icon, label, value, unit, color, cls }) => (
                  <div key={label} className="stat-tile">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                      <div className={`icon-box ${cls}`}><Icon size={15} /></div>
                    </div>
                    <div className="stat-label">{label}</div>
                    <div className="stat-value" style={{ color, fontSize: 24 }}>
                      {value}<span className="stat-unit">{unit}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Wear trend chart */}
            <div className="card fade-up" style={{ marginBottom: 16 }}>
              <div className="card-header">
                <span className="card-title"><TrendingDown size={14} /> Wear Score History</span>
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  Dots: green=Low · amber=Medium · red=High
                </span>
              </div>
              <div className="card-body">
                {history.length > 0
                  ? <Line data={lineData} options={lineOptions} />
                  : (
                    <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>
                      No sessions recorded yet — run the Optimizer to populate history.
                    </div>
                  )}
              </div>
            </div>

            {/* Sessions table */}
            {history.length > 0 && (
              <div className="card fade-up" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <span className="card-title">Session Log</span>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Last {history.length} sessions</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        {['Session', 'Wear Score', 'Rating', 'Target SoC', 'Temp', 'Date'].map(h => (
                          <th key={h}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((s, i) => (
                        <tr key={i}>
                          <td className="mono" style={{ color: 'var(--text-tertiary)' }}>#{s.session_id}</td>
                          <td className="mono" style={{ fontWeight: 700, color: s.wear_rating === 'Low' ? 'var(--success)' : s.wear_rating === 'Medium' ? 'var(--warning)' : 'var(--danger)' }}>
                            {s.wear_score?.toFixed(1)}
                          </td>
                          <td>
                            <div className={`pill pill-${s.wear_rating === 'Low' ? 'green' : s.wear_rating === 'Medium' ? 'yellow' : 'red'}`}>
                              <div className="pill-dot" /> {s.wear_rating}
                            </div>
                          </td>
                          <td className="mono">{s.target_soc}%</td>
                          <td className="mono">{s.temperature}°C</td>
                          <td style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
                            {s.created_at ? new Date(s.created_at).toLocaleDateString() : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tips */}
            <div className="card fade-up">
              <div className="card-header">
                <span className="card-title"><Shield size={14} /> Battery Longevity Recommendations</span>
              </div>
              <div className="card-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
                {data.tips.map((tip, i) => (
                  <div key={i} style={{
                    display: 'flex', gap: 10, padding: '10px 14px',
                    background: 'var(--bg-overlay)', borderRadius: 8,
                    border: '1px solid var(--border)',
                  }}>
                    <span style={{ color: 'var(--success)', fontSize: 12, flexShrink: 0, marginTop: 1 }}>✓</span>
                    <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{tip}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}
