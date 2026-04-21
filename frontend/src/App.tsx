import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'
import PaperTradePage from './pages/PaperTradePage'
import PaperTradeSymbolPage from './pages/PaperTradeSymbolPage'
import { AppShell } from './components/layout/AppShell'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/ranking" element={<StockRankingPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/history" element={<AnalysisHistoryPage />} />
          <Route path="/stocks/:code" element={<StockDetailPage />} />
          <Route path="/paper-trade" element={<PaperTradePage />} />
          <Route path="/paper-trade/symbols/:symbol" element={<PaperTradeSymbolPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
