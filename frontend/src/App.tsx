import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'
import UiSandboxPage from './pages/__UiSandboxPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/stocks/:code" element={<StockDetailPage />} />
        <Route path="/ranking" element={<StockRankingPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/simulator" element={<SimulatorPage />} />
        <Route path="/history" element={<AnalysisHistoryPage />} />
        <Route path="/__ui" element={<UiSandboxPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
