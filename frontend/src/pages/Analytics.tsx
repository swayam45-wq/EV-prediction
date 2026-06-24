import { useEffect, useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Bar, Doughnut, Line } from 'react-chartjs-2'
import { BarChart3, TrendingDown, Zap, DollarSign, AlertTriangle } from 'lucide-react'
import { getAnalytics } from '../api'
import type { AnalyticsResponse } from '../types'

ChartJS.register(
  CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend, Filler
)

const baseScaleOpts = {
  x: { ticks: { color: '#4a5060', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
  y: { ticks: { color: '#8b919e', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
}

const baseLegend = { labels: { color: '#8b919e', font: { size: 11 }, boxWidth: 12 } }

export default function Analytics() {
  const [data, setData] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    getAnalytics(30).then(setData).catch(() => setError(true)).finally(() => setLoading(false))
  }, [])

  const noSessions = !data || data.session_count === 0

  /* ── chart configs ────────────────────────────────────── */
  const wearChart = {
    labels: data?.wear_trend.map(w => w.date ? new Date(w.date).toLocaleDateString() : '') ?? [],
    datasets: [{
      label: 'Wear Score',
      data: data?.wear_trend.map(w => w.wear_score) ?? [],
      borderColor: 'rgba(14,165,233,0.7)', backgroundColor: 'rgba(14,165,233,0.06)',
      borderWidth: 1.5, tension: 0.4, fill: true,
    }],
  }

  const savingsChart = {
    labels: data?.savings_trend.map(s => s.date ? new Date(s.date).toLocaleDateString() : '') ?? [],
    datasets: [{
      label: 'Savings (%)',
      data: data?.savings_trend.map(s => s.savings_percent) ?? [],
      borderColor: 'rgba(16,185,129,0.7)', backgroundColor: 'rgba(16,185,129,0.06)',
      borderWidth: 1.5, tension: 0.4, fill: true,
    }],
  }

  const patternChart = {
    labels: data?.charging_pattern.map(p => p.hour) ?? [],
    datasets: [{
      label: 'Sessions',
      data: data?.charging_pattern.map(p => p.count) ?? [],
      backgroundColor: 'rgba(14,165,233,0.6)', borderRadius: 4,
    }],
  }

  const socDoughnut = {
    labels: data?.soc_distribution.map(s => `${s.range}%`) ?? [],
    datasets: [{
      data: data?.soc_distribution.map(s => s.count) ?? [],
      backgroundColor: ['#0c2a44', '#1d4ed8', '#0ea5e9', '#38bdf8', '#10b981'],
      borderColor: 'var(--bg-raised)', borderWidth: 3,
    }],
  }

  const avgWear = data?.wear_trend.length
    ? (data.wear_trend.reduce((s, w) => s + w.wear_score, 0) / data.wear_trend.length).toFixed(1)
    : '—'

  const avgSavings = data?.savings_trend.length
    ? `${(data.savings_trend.reduce((s, w) => s + w.savings_percent, 0) / data.savings_trend.length).toFixed(1)}%`
    : '—'

  return (
    <>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-inner">
          <div className="page-eyebrow">Reporting</div>
          <h1 className="page-title">Analytics</h1>
        </div>
      </div>

      <div className="page-body">
        {error && (
          <div className="alert alert-warning fade-up" style={{ marginBottom: 20 }}>
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            Backend not reachable — start the FastAPI server on port 8000.
          </div>
        )}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
            <div className="spinner-lg" />
          </div>
        )}

        {data && (
          <>
            {/* KPI row */}
            <div className="grid-4 fade-up" style={{ marginBottom: 16 }}>
              {[
                { icon: BarChart3,    label: 'Total Sessions',  value: data.session_count,                      unit: '',    color: 'var(--accent)',   cls: 'icon-box-blue' },
                { icon: DollarSign,  label: 'Total Saved',      value: `$${data.total_saved_usd.toFixed(2)}`,   unit: '',    color: 'var(--success)',  cls: 'icon-box-green' },
                { icon: TrendingDown,label: 'Avg Wear Score',   value: avgWear,                                  unit: '/100',color: 'var(--warning)', cls: 'icon-box-yellow' },
                { icon: Zap,         label: 'Avg Savings',      value: avgSavings,                               unit: '',    color: 'var(--success)',  cls: 'icon-box-green' },
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

            {noSessions ? (
              <div className="card" style={{ padding: '60px 24px', textAlign: 'center' }}>
                <BarChart3 size={40} color="var(--text-tertiary)" style={{ margin: '0 auto 14px' }} />
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  No session data yet
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                  Run the Optimizer a few times to populate charts.
                </div>
              </div>
            ) : (
              <>
                {/* Wear + Savings trends */}
                <div className="grid-2 fade-up" style={{ marginBottom: 16 }}>
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">Wear Score Trend</span>
                      <div className="pill pill-blue"><div className="pill-dot" />Per session</div>
                    </div>
                    <div className="card-body">
                      <Line data={wearChart} options={{ responsive: true, plugins: { legend: baseLegend }, scales: baseScaleOpts } as Parameters<typeof Line>[0]['options']} />
                    </div>
                  </div>
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">Cost Savings Trend</span>
                      <div className="pill pill-green"><div className="pill-dot" />%</div>
                    </div>
                    <div className="card-body">
                      <Line data={savingsChart} options={{ responsive: true, plugins: { legend: baseLegend }, scales: baseScaleOpts } as Parameters<typeof Line>[0]['options']} />
                    </div>
                  </div>
                </div>

                {/* Charging pattern + SoC distribution */}
                <div className="grid-2 fade-up">
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">Charging Start Hours</span>
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>When do you plug in?</span>
                    </div>
                    <div className="card-body">
                      <Bar data={patternChart} options={{ responsive: true, plugins: { legend: baseLegend }, scales: baseScaleOpts } as Parameters<typeof Bar>[0]['options']} />
                    </div>
                  </div>
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">Target SoC Distribution</span>
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Charge level preference</span>
                    </div>
                    <div className="card-body" style={{ display: 'flex', justifyContent: 'center' }}>
                      <div style={{ maxWidth: 240 }}>
                        <Doughnut
                          data={socDoughnut}
                          options={{
                            responsive: true,
                            plugins: {
                              legend: { position: 'bottom', labels: { color: '#8b919e', font: { size: 11 }, boxWidth: 12, padding: 16 } },
                            },
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </>
  )
}
