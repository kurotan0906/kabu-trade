import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/stocks/:code" element={<StockDetailPage />} />
        <Route path="/ranking" element={<StockRankingPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
