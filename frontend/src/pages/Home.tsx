import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Zap, Battery, TrendingDown, Shield, ArrowRight, Cpu, AlertCircle } from 'lucide-react'
import { getBatteryHealth } from '../api'
import type { BatteryHealthResponse } from '../types'

/* ── Animated battery gauge SVG ──────────────────────────── */
function BatteryGauge({ pct }: { pct: number }) {
  const r = 80, cx = 100, cy = 100
  const circumference = 2 * Math.PI * r
  const dash = (pct / 100) * circumference
  const color = pct > 60 ? '#06d6a0' : pct > 30 ? '#f59e0b' : '#ef4444'

  return (
    <svg viewBox="0 0 200 200" width="200" height="200" style={{ filter: `drop-shadow(0 0 16px ${color}60)` }}>
      {/* Track */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" />
      {/* Progress */}
      <circle
        cx={cx} cy={cy} r={r} fill="none"
        stroke={color} strokeWidth="14"
        strokeDasharray={`${dash} ${circumference}`}
        strokeLinecap="round"
        transform="rotate(-90 100 100)"
        style={{ transition: 'stroke-dasharray 1s ease' }}
      />
      {/* Center text */}
      <text x={cx} y={cy - 8} textAnchor="middle" fill="#f0f4ff"
        fontSize="32" fontWeight="700" fontFamily="Space Grotesk, sans-serif">
        {pct}%
      </text>
      <text x={cx} y={cy + 16} textAnchor="middle" fill="#8b9dc3" fontSize="12">
        State of Charge
      </text>
    </svg>
  )
}

/* ── Stat card ────────────────────────────────────────────── */
function StatCard({ icon: Icon, label, value, unit, color = '#3b82f6', delay = 0 }: {
  icon: React.ElementType; label: string; value: string | number;
  unit?: string; color?: string; delay?: number
}) {
  return (
    <div className={`glass-card fade-in-up delay-${delay}`} style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--clr-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>{label}</p>
          <p className="stat-value" style={{ color }}>
            {value}
            {unit && <span style={{ fontSize: '1.1rem', fontWeight: 500, color: 'var(--clr-text-muted)', marginLeft: 4 }}>{unit}</span>}
          </p>
        </div>
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: `${color}18`, border: `1px solid ${color}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={22} color={color} />
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const [health, setHealth] = useState<BatteryHealthResponse | null>(null)
  const [backendUp, setBackendUp] = useState(true)

  useEffect(() => {
    getBatteryHealth()
      .then(setHealth)
      .catch(() => setBackendUp(false))
      .finally(() => {/* no loading indicator on home */})
  }, [])

  const soc = 72 // Demo value — Phase 4 will pull from vehicle API
  const summary = health?.summary

  return (
    <div className="page">
      {/* ── Hero ────────────────────────────────────────────── */}
      <div className="fade-in-up" style={{ textAlign: 'center', marginBottom: 56, paddingTop: 16 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '6px 18px', borderRadius: 999,
          background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)',
          fontSize: '0.82rem', fontWeight: 600, color: '#60a5fa',
          marginBottom: 20,
        }}>
          <Cpu size={14} /> AI-Powered Charging Intelligence
        </div>

        <h1 className="page-title gradient-text" style={{ fontSize: 'clamp(2rem, 5vw, 3.2rem)', marginBottom: 16 }}>
          Smart EV Charging
        </h1>
        <p style={{ color: 'var(--clr-text-muted)', fontSize: '1.05rem', maxWidth: 540, margin: '0 auto 32px' }}>
          Minimize cost, protect battery health, and ensure your car is always ready —
          powered by Linear Programming and XGBoost ML.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/optimizer">
            <button className="btn-primary">
              <Zap size={18} /> Optimize Now <ArrowRight size={16} />
            </button>
          </Link>
          <Link to="/analytics">
            <button className="btn-secondary">
              View Analytics
            </button>
          </Link>
        </div>
      </div>

      {/* ── Backend status banner ────────────────────────────── */}
      {!backendUp && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '12px 20px',
          background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
          borderRadius: 12, marginBottom: 24, color: '#f59e0b', fontSize: '0.88rem',
        }}>
          <AlertCircle size={18} />
          <span>Backend not reachable — start the FastAPI server on port 8000. Demo values shown below.</span>
        </div>
      )}

      {/* ── Battery gauge + stats row ────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 24, alignItems: 'center', marginBottom: 32 }}>
        {/* Gauge */}
        <div className="glass-card fade-in-up" style={{
          padding: 32, display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: 16,
        }}>
          <BatteryGauge pct={soc} />
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', marginBottom: 4 }}>Current Vehicle</p>
            <p style={{ fontWeight: 700, color: 'var(--clr-text)' }}>Demo EV · 75 kWh</p>
            <div className="badge badge-green" style={{ marginTop: 8 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#06d6a0', animation: 'pulse-glow 2s infinite' }} />
              Plugged In
            </div>
          </div>
        </div>

        {/* Stats grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <StatCard icon={Battery}     label="Battery Health (SoH)" value={summary?.inferred_soh_percent ?? 96} unit="%" color="#06d6a0" delay={1} />
          <StatCard icon={TrendingDown} label="Avg Savings"          value={summary?.avg_savings_percent ?? 0} unit="%" color="#3b82f6" delay={2} />
          <StatCard icon={Zap}          label="Total Sessions"        value={summary?.total_charging_sessions ?? 0} color="#a78bfa" delay={3} />
          <StatCard icon={Shield}       label="Avg Wear Score"        value={summary ? `${summary.avg_wear_score}/100` : '—'} color={summary && summary.avg_wear_score < 20 ? '#06d6a0' : '#f59e0b'} delay={4} />
        </div>
      </div>

      {/* ── Feature cards ────────────────────────────────────── */}
      <h2 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.3rem', fontWeight: 700, marginBottom: 20 }}>
        How It Works
      </h2>
      <div className="grid-3">
        {[
          {
            icon: '⚡', title: 'LP Optimization', color: '#3b82f6',
            desc: 'Coin-or CBC solver finds the minimum-cost hourly charging schedule using Linear Programming — mathematically guaranteed optimal.',
          },
          {
            icon: '🤖', title: 'XGBoost ML Model', color: '#a78bfa',
            desc: 'Trained on 15,000 charging sessions, our XGBoost model predicts battery wear (R²=0.99) so you get personalized health advice.',
          },
          {
            icon: '💰', title: 'Cost Intelligence', color: '#06d6a0',
            desc: 'Dynamic pricing awareness shifts charging to off-peak hours. Users save 15–30% on electricity costs every session.',
          },
        ].map((f, i) => (
          <div key={i} className={`glass-card fade-in-up delay-${i + 1}`} style={{ padding: 28 }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: `${f.color}18`, border: `1px solid ${f.color}30`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24, marginBottom: 16,
            }}>{f.icon}</div>
            <h3 style={{ fontWeight: 700, marginBottom: 8, color: f.color }}>{f.title}</h3>
            <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.9rem', lineHeight: 1.7 }}>{f.desc}</p>
          </div>
        ))}
      </div>

      {/* ── Tips ─────────────────────────────────────────────── */}
      {health?.tips && health.tips.length > 0 && (
        <div className="glass-card fade-in-up" style={{ padding: 28, marginTop: 28 }}>
          <h3 style={{ fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Shield size={18} color="#06d6a0" /> Battery Health Tips
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {health.tips.map((tip, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, color: 'var(--clr-text-muted)', fontSize: '0.92rem' }}>
                <span style={{ color: '#06d6a0', flexShrink: 0 }}>✓</span> {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
