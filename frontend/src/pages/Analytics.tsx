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
  CategoryScale, LinearScale, BarElement, PointElement, LineElement,
  ArcElement, Title, Tooltip, Legend, Filler
)

const chartDefaults = {
  scales: {
    x: { ticks: { color: '#4a5a7a' }, grid: { color: 'rgba(255,255,255,0.04)' } },
    y: { ticks: { color: '#8b9dc3' }, grid: { color: 'rgba(255,255,255,0.04)' } },
  },
  plugins: {
    legend: { labels: { color: '#8b9dc3', font: { size: 12 } } },
  },
  responsive: true,
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    getAnalytics(30)
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const empty = !data || data.session_count === 0

  /* ── Chart configs ──────────────────────────────────────── */
  const wearChart = {
    labels: data?.wear_trend.map(w => w.date ? new Date(w.date).toLocaleDateString() : '') ?? [],
    datasets: [{
      label: 'Wear Score',
      data: data?.wear_trend.map(w => w.wear_score) ?? [],
      borderColor: '#a78bfa',
      backgroundColor: 'rgba(167,139,250,0.1)',
      borderWidth: 2, tension: 0.4, fill: true,
    }],
  }

  const savingsChart = {
    labels: data?.savings_trend.map(s => s.date ? new Date(s.date).toLocaleDateString() : '') ?? [],
    datasets: [{
      label: 'Savings (%)',
      data: data?.savings_trend.map(s => s.savings_percent) ?? [],
      borderColor: '#06d6a0',
      backgroundColor: 'rgba(6,214,160,0.1)',
      borderWidth: 2, tension: 0.4, fill: true,
    }],
  }

  const patternChart = {
    labels: data?.charging_pattern.map(p => p.hour) ?? [],
    datasets: [{
      label: 'Sessions Started',
      data: data?.charging_pattern.map(p => p.count) ?? [],
      backgroundColor: 'rgba(59,130,246,0.7)',
      borderRadius: 6,
    }],
  }

  const socDoughnut = {
    labels: data?.soc_distribution.map(s => `${s.range}%`) ?? [],
    datasets: [{
      data: data?.soc_distribution.map(s => s.count) ?? [],
      backgroundColor: ['#1e3a5f', '#1d4ed8', '#3b82f6', '#60a5fa', '#06d6a0'],
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 2,
    }],
  }

  return (
    <div className="page">
      <h1 className="page-title fade-in-up">Analytics Dashboard</h1>
      <p className="page-subtitle fade-in-up delay-1">
        Aggregated insights across all your charging sessions — savings, wear trends, and patterns.
      </p>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 20px',
          background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
          borderRadius: 12, color: '#f59e0b', marginBottom: 24 }}>
          <AlertTriangle size={18} />
          Backend not reachable — start the FastAPI server on port 8000.
        </div>
      )}

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
          <div className="spinner" />
        </div>
      )}

      {data && (
        <>
          {/* KPI row */}
          <div className="grid-4 fade-in-up" style={{ marginBottom: 24 }}>
            {[
              { icon: BarChart3,    label: 'Total Sessions',    val: data.session_count,               unit: '',    color: '#3b82f6' },
              { icon: DollarSign,  label: 'Total Saved',        val: `$${data.total_saved_usd.toFixed(2)}`, unit: '', color: '#06d6a0' },
              { icon: TrendingDown,label: 'Avg Wear Score',     val: data.wear_trend.length > 0
                ? (data.wear_trend.reduce((s, w) => s + w.wear_score, 0) / data.wear_trend.length).toFixed(1)
                : '—',                                            unit: '/100', color: '#a78bfa' },
              { icon: Zap,         label: 'Avg Savings',        val: data.savings_trend.length > 0
                ? `${(data.savings_trend.reduce((s, w) => s + w.savings_percent, 0) / data.savings_trend.length).toFixed(1)}%`
                : '—',                                            unit: '',    color: '#f59e0b' },
            ].map(({ icon: Icon, label, val, unit, color }) => (
              <div key={label} className="glass-card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--clr-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{label}</p>
                    <p style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.8rem', fontWeight: 700, color, lineHeight: 1 }}>
                      {val}<span style={{ fontSize: '0.85rem', color: 'var(--clr-text-muted)', marginLeft: 2 }}>{unit}</span>
                    </p>
                  </div>
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: `${color}18`, border: `1px solid ${color}30`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={20} color={color} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {empty ? (
            <div className="glass-card" style={{ padding: 64, textAlign: 'center' }}>
              <BarChart3 size={48} color="var(--clr-text-faint)" style={{ margin: '0 auto 16px' }} />
              <p style={{ color: 'var(--clr-text-muted)', fontSize: '1rem' }}>
                No sessions yet — run the <strong style={{ color: 'var(--clr-text)' }}>Optimizer</strong> a few times to populate charts.
              </p>
            </div>
          ) : (
            <>
              {/* Wear trend + Savings trend */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
                <div className="glass-card fade-in-up delay-1" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 20, color: '#a78bfa' }}>Wear Score Trend</h3>
                  <Line data={wearChart} options={chartDefaults as Parameters<typeof Line>[0]['options']} />
                </div>
                <div className="glass-card fade-in-up delay-2" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 20, color: '#06d6a0' }}>Savings Trend (%)</h3>
                  <Line data={savingsChart} options={chartDefaults as Parameters<typeof Line>[0]['options']} />
                </div>
              </div>

              {/* Charging pattern + SoC distribution */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                <div className="glass-card fade-in-up delay-3" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 4, color: '#3b82f6' }}>Charging Start Hours</h3>
                  <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.82rem', marginBottom: 16 }}>When do you most often plug in?</p>
                  <Bar data={patternChart} options={chartDefaults as Parameters<typeof Bar>[0]['options']} />
                </div>
                <div className="glass-card fade-in-up delay-4" style={{ padding: 24 }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 4, color: '#60a5fa' }}>Target SoC Distribution</h3>
                  <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.82rem', marginBottom: 16 }}>What charge level do you target?</p>
                  <div style={{ maxWidth: 280, margin: '0 auto' }}>
                    <Doughnut data={socDoughnut} options={{ responsive: true, plugins: { legend: { labels: { color: '#8b9dc3' } } } }} />
                  </div>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
