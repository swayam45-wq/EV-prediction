import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Zap, Battery, BarChart3,
  Settings, BellRing, Wifi
} from 'lucide-react'

const navItems = [
  { to: '/',          label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/optimizer', label: 'Optimizer',   icon: Zap },
  { to: '/battery',   label: 'Battery',     icon: Battery },
  { to: '/analytics', label: 'Analytics',   icon: BarChart3 },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="brand">
        <div className="brand-logo">
          <img src="/logo.png" alt="VoltWise Logo" style={{ width: 32, height: 32, borderRadius: 8, objectFit: 'cover' }} />
          <div>
            <div className="brand-name">VoltWise</div>
            <div className="brand-tagline">EV Intelligence</div>
          </div>
        </div>
      </div>

      {/* Vehicle status card */}
      <div className="vehicle-card">
        <div className="vehicle-model">Demo EV · 75 kWh</div>
        <div className="vehicle-sub">VIN: WM3DEMO2026</div>
        <div className="soc-bar-wrap">
          <div className="soc-label">
            <span>State of Charge</span>
            <span style={{ color: '#10b981', fontWeight: 700 }}>72%</span>
          </div>
          <div className="soc-bar">
            <div className="soc-fill" style={{ width: '72%' }} />
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
          <div className="pill pill-green">
            <div className="pill-dot" />
            Charging
          </div>
          <div className="pill pill-blue" style={{ marginLeft: 'auto', fontSize: 10 }}>
            <Wifi size={9} /> Live
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="nav-section">
        <div className="nav-section-label">Menu</div>
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={16} className="nav-icon" />
            {label}
          </NavLink>
        ))}

        <div className="nav-section-label" style={{ marginTop: 20 }}>System</div>
        <button className="nav-item">
          <BellRing size={16} className="nav-icon" />
          Alerts
          <span style={{
            marginLeft: 'auto', background: '#ef4444', color: '#fff',
            fontSize: 10, fontWeight: 700, borderRadius: 999,
            padding: '1px 6px', minWidth: 18, textAlign: 'center',
          }}>2</span>
        </button>
        <button className="nav-item">
          <Settings size={16} className="nav-icon" />
          Settings
        </button>
      </nav>

      {/* Footer */}
      <div style={{
        padding: '14px 16px',
        borderTop: '1px solid var(--border)',
        fontSize: 11,
        color: 'var(--text-tertiary)',
      }}>
        <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 2 }}>VoltWise v2.0</div>
        <div>Backend · FastAPI + XGBoost</div>
      </div>
    </aside>
  )
}
