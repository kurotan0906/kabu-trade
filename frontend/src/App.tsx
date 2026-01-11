import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/stocks/:code" element={<StockDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
