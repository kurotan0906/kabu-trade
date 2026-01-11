import { useParams } from 'react-router-dom'

const StockDetailPage = () => {
  const { code } = useParams<{ code: string }>()

  return (
    <div>
      <h1>銘柄詳細: {code}</h1>
      {/* TODO: Phase 1.4, 1.5で実装 */}
    </div>
  )
}

export default StockDetailPage
