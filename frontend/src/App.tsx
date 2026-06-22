import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Optimizer from './pages/Optimizer'
import BatteryHealth from './pages/BatteryHealth'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/"           element={<Home />} />
          <Route path="/optimizer"  element={<Optimizer />} />
          <Route path="/battery"    element={<BatteryHealth />} />
          <Route path="/analytics"  element={<Analytics />} />
        </Routes>
      </main>
    </div>
  )
}
