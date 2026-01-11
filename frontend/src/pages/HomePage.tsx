import StockSearch from '@/components/stock/StockSearch';

const HomePage = () => {
  return (
    <div>
      <h1>Kabu Trade</h1>
      <p>株取引支援システム</p>
      <p>銘柄コードを入力して検索してください</p>
      <StockSearch />
    </div>
  );
};

export default HomePage;
