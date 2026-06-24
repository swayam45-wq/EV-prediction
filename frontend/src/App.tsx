import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Navbar'
import Home from './pages/Home'
import Optimizer from './pages/Optimizer'
import BatteryHealth from './pages/BatteryHealth'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div className="layout">
      <Sidebar />
      <div className="main-content">
        <Routes>
          <Route path="/"           element={<Home />} />
          <Route path="/optimizer"  element={<Optimizer />} />
          <Route path="/battery"    element={<BatteryHealth />} />
          <Route path="/analytics"  element={<Analytics />} />
        </Routes>
      </div>
    </div>
  )
}
