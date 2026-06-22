import { useEffect, useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { Battery, Shield, Cpu, TrendingDown, AlertTriangle } from 'lucide-react'
import { getBatteryHealth } from '../api'
import type { BatteryHealthResponse } from '../types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

/* ── SoH Arc gauge ───────────────────────────────────────── */
function SohGauge({ soh }: { soh: number }) {
  const color = soh > 85 ? '#06d6a0' : soh > 70 ? '#f59e0b' : '#ef4444'
  const label = soh > 85 ? 'Excellent' : soh > 70 ? 'Good' : 'Degraded'
  const pct = (soh - 0) / 100
  // 270-degree arc (from 135° to 405°)
  const r = 80, cx = 110, cy = 110
  const startAngle = 135 * (Math.PI / 180)
  const endAngle = (135 + 270 * pct) * (Math.PI / 180)
  const arc = (angle: number) => [cx + r * Math.cos(angle), cy + r * Math.sin(angle)]
  const [sx, sy] = arc(startAngle)
  const [ex, ey] = arc(endAngle)
  const largeArc = 270 * pct > 180 ? 1 : 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <svg width="220" height="160" viewBox="0 0 220 160" style={{ filter: `drop-shadow(0 0 20px ${color}40)` }}>
        {/* Track */}
        <path d={`M ${arc(startAngle).join(' ')} A ${r} ${r} 0 1 1 ${arc(405 * Math.PI / 180).join(' ')}`}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" strokeLinecap="round" />
        {/* Arc */}
        {soh > 0 && <path d={`M ${sx} ${sy} A ${r} ${r} 0 ${largeArc} 1 ${ex} ${ey}`}
          fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
          style={{ transition: 'all 1s ease' }} />}
        {/* Value */}
        <text x={cx} y={cy + 4} textAnchor="middle" fill="#f0f4ff"
          fontSize="30" fontWeight="700" fontFamily="Space Grotesk, sans-serif">{soh.toFixed(1)}%</text>
        <text x={cx} y={cy + 22} textAnchor="middle" fill="#8b9dc3" fontSize="11">State of Health</text>
      </svg>
      <div className={`badge badge-${soh > 85 ? 'green' : soh > 70 ? 'yellow' : 'red'}`}>
        {label}
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

  const wearHistory = data?.wear_history ?? []

  const lineData = {
    labels: wearHistory.map((_, i) => `Session ${i + 1}`),
    datasets: [{
      label: 'Wear Score',
      data: wearHistory.map(h => h.wear_score),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.1)',
      borderWidth: 2, tension: 0.4, fill: true,
      pointBackgroundColor: wearHistory.map(h =>
        h.wear_rating === 'Low' ? '#06d6a0' : h.wear_rating === 'Medium' ? '#f59e0b' : '#ef4444'
      ),
      pointRadius: 5,
    }],
  }

  const lineOptions = {
    responsive: true,
    plugins: {
      legend: { labels: { color: '#8b9dc3' } },
    },
    scales: {
      x: { ticks: { color: '#4a5a7a' }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: {
        min: 0, max: 100,
        ticks: { color: '#8b9dc3' }, grid: { color: 'rgba(255,255,255,0.04)' },
        title: { display: true, text: 'Wear Score', color: '#8b9dc3' },
      },
    },
  }

  return (
    <div className="page">
      <h1 className="page-title fade-in-up">Battery Health</h1>
      <p className="page-subtitle fade-in-up delay-1">
        Real-time battery State of Health, wear trend analysis, and ML model insights.
      </p>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
          <div className="spinner" />
        </div>
      )}

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 20px',
          background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
          borderRadius: 12, color: '#f59e0b', marginBottom: 24 }}>
          <AlertTriangle size={18} />
          Backend not reachable — start the FastAPI server on port 8000.
        </div>
      )}

      {data && (
        <>
          {/* SoH gauge + summary row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 24, marginBottom: 24 }}>
            <div className="glass-card fade-in-up" style={{ padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
              <SohGauge soh={data.summary.inferred_soh_percent} />
              <div className="divider" style={{ width: '100%' }} />
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '0.78rem', color: 'var(--clr-text-muted)', marginBottom: 4 }}>ML Model Status</p>
                <div className="badge badge-blue">
                  <Cpu size={12} />
                  {(data.ml_model_info as { status?: string }).status === 'ml_model_active' ? 'XGBoost Active' : 'Heuristic Mode'}
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {[
                { icon: Battery,     label: 'Total Sessions',   val: data.summary.total_charging_sessions,                     color: '#3b82f6',  unit: '' },
                { icon: TrendingDown,label: 'Avg Savings',       val: data.summary.avg_savings_percent.toFixed(1),              color: '#06d6a0',  unit: '%' },
                { icon: Shield,      label: 'Avg Wear Score',    val: data.summary.avg_wear_score.toFixed(1),                   color: '#a78bfa',  unit: '/100' },
                { icon: Battery,     label: 'Total Energy',      val: data.summary.total_energy_charged_kwh.toFixed(1),         color: '#f59e0b',  unit: 'kWh' },
              ].map(({ icon: Icon, label, val, color, unit }, i) => (
                <div key={label} className={`glass-card fade-in-up delay-${i + 1}`} style={{ padding: 24 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <p style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--clr-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>{label}</p>
                      <p className="stat-value" style={{ color }}>
                        {val}<span style={{ fontSize: '1rem', color: 'var(--clr-text-muted)', marginLeft: 3 }}>{unit}</span>
                      </p>
                    </div>
                    <div style={{ width: 44, height: 44, borderRadius: 12, background: `${color}18`, border: `1px solid ${color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon size={22} color={color} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Wear trend chart */}
          <div className="glass-card fade-in-up delay-2" style={{ padding: 28, marginBottom: 24 }}>
            <h2 style={{ fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendingDown size={18} color="#3b82f6" /> Wear Score Trend
            </h2>
            {wearHistory.length > 0
              ? <Line data={lineData} options={lineOptions} />
              : <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--clr-text-muted)' }}>
                  No charging sessions yet — run the optimizer to see your wear trend!
                </div>
            }
          </div>

          {/* Recent sessions table */}
          {wearHistory.length > 0 && (
            <div className="glass-card fade-in-up delay-3" style={{ padding: 28, marginBottom: 24 }}>
              <h2 style={{ fontWeight: 700, marginBottom: 20 }}>Recent Sessions</h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {['Session', 'Wear Score', 'Rating', 'Target SoC', 'Temp (°C)', 'Date'].map(h => (
                        <th key={h} style={{ textAlign: 'left', padding: '10px 14px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--clr-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--clr-border)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {wearHistory.map((s, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '12px 14px', color: 'var(--clr-text-muted)', fontSize: '0.88rem' }}>#{s.session_id}</td>
                        <td style={{ padding: '12px 14px', fontWeight: 700, color: s.wear_rating === 'Low' ? '#06d6a0' : s.wear_rating === 'Medium' ? '#f59e0b' : '#ef4444' }}>{s.wear_score?.toFixed(1)}</td>
                        <td style={{ padding: '12px 14px' }}>
                          <span className={`badge badge-${s.wear_rating === 'Low' ? 'green' : s.wear_rating === 'Medium' ? 'yellow' : 'red'}`}>{s.wear_rating}</span>
                        </td>
                        <td style={{ padding: '12px 14px', color: 'var(--clr-text-muted)', fontSize: '0.88rem' }}>{s.target_soc}%</td>
                        <td style={{ padding: '12px 14px', color: 'var(--clr-text-muted)', fontSize: '0.88rem' }}>{s.temperature}°C</td>
                        <td style={{ padding: '12px 14px', color: 'var(--clr-text-faint)', fontSize: '0.82rem' }}>{s.created_at ? new Date(s.created_at).toLocaleDateString() : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="glass-card fade-in-up delay-4" style={{ padding: 28, borderColor: 'rgba(6,214,160,0.2)' }}>
            <h2 style={{ fontWeight: 700, marginBottom: 16, color: '#06d6a0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={18} /> Longevity Tips
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
              {data.tips.map((tip, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, padding: '12px 16px', background: 'rgba(6,214,160,0.05)', borderRadius: 10, border: '1px solid rgba(6,214,160,0.1)' }}>
                  <span style={{ color: '#06d6a0', fontSize: '1rem', flexShrink: 0 }}>✓</span>
                  <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.88rem', lineHeight: 1.6 }}>{tip}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
