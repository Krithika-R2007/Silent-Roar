import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import Dashboard from './pages/Dashboard'
import IntelligenceMap from './pages/IntelligenceMap'
import Investigations from './pages/Investigations'
import InvestigationDetail from './pages/InvestigationDetail'
import NetworkAnalysis from './pages/NetworkAnalysis'
import Alerts from './pages/Alerts'
import EvidencePage from './pages/EvidencePage'
import SignalWatch from './pages/SignalWatch'
import Reports from './pages/Reports'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<IntelligenceMap />} />
          <Route path="/investigations" element={<Investigations />} />
          <Route path="/investigations/:id" element={<InvestigationDetail />} />
          <Route path="/network" element={<NetworkAnalysis />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/evidence" element={<EvidencePage />} />
          <Route path="/signalwatch" element={<SignalWatch />} />
          <Route path="/reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
