import { NavLink } from 'react-router-dom'
import { Zap, Home, BarChart3, Battery, Activity } from 'lucide-react'

const links = [
  { to: '/',          label: 'Home',        icon: Home },
  { to: '/optimizer', label: 'Optimizer',   icon: Zap },
  { to: '/battery',   label: 'Battery',     icon: Battery },
  { to: '/analytics', label: 'Analytics',   icon: BarChart3 },
]

export default function Navbar() {
  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 50,
      background: 'rgba(10,15,30,0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--clr-border)',
    }}>
      <div style={{
        maxWidth: 1280, margin: '0 auto',
        padding: '0 24px',
        display: 'flex', alignItems: 'center', height: 64,
        gap: 8,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 'auto' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #3b82f6, #06d6a0)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(59,130,246,0.5)',
          }}>
            <Activity size={20} color="#fff" />
          </div>
          <span style={{
            fontFamily: 'Space Grotesk, sans-serif',
            fontWeight: 700, fontSize: '1.1rem',
            background: 'linear-gradient(135deg, #60a5fa, #06d6a0)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>EV Optimizer</span>
        </div>

        {/* Nav links */}
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '8px 16px', borderRadius: 10,
              fontSize: '0.88rem', fontWeight: 600,
              textDecoration: 'none',
              transition: 'all 0.2s',
              color: isActive ? '#fff' : 'var(--clr-text-muted)',
              background: isActive
                ? 'linear-gradient(135deg, rgba(59,130,246,0.25), rgba(6,214,160,0.15))'
                : 'transparent',
              border: isActive ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
            })}
          >
            <Icon size={16} />
            <span className="hidden sm:inline">{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
