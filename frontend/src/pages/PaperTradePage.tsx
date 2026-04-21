import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PageHeader,
  Button,
  Card,
  CardBody,
  Stat,
  EmptyState,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
} from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type {
  AccountInitialized,
  PaperSummary,
  PaperHolding,
  PaperTrade,
  ChartPoint,
  PerformanceItem,
} from '@/types/paperTrade';
import InitCapitalDialog from '@/components/paper-trade/InitCapitalDialog';
import ResetConfirmDialog from '@/components/paper-trade/ResetConfirmDialog';
import BuyDialog from '@/components/paper-trade/BuyDialog';
import SellDialog from '@/components/paper-trade/SellDialog';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

// Simple SVG multi-line chart
interface SimpleChartProps {
  data: ChartPoint[];
}
const AssetChart = ({ data }: SimpleChartProps) => {
  if (data.length === 0) return null;
  const W = 800;
  const H = 240;
  const pad = { l: 70, r: 20, t: 10, b: 30 };
  const iW = W - pad.l - pad.r;
  const iH = H - pad.t - pad.b;

  const allVals = data.flatMap((d) => [d.total_value, d.holdings_value, d.cash]);
  const minY = Math.min(...allVals);
  const maxY = Math.max(...allVals);
  const range = maxY - minY || 1;

  const xScale = (i: number) => pad.l + (i / Math.max(data.length - 1, 1)) * iW;
  const yScale = (v: number) => pad.t + iH - ((v - minY) / range) * iH;

  const path = (key: keyof ChartPoint) =>
    data
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d[key] as number)}`)
      .join(' ');

  const yTicks = 4;
  const tickVals = Array.from({ length: yTicks + 1 }, (_, i) => minY + (range / yTicks) * i);
  const xLabelStep = Math.max(1, Math.floor(data.length / 6));

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full">
        {tickVals.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={W - pad.r} y1={yScale(v)} y2={yScale(v)} stroke="#e2e8f0" strokeDasharray="2 4" />
            <text x={pad.l - 6} y={yScale(v) + 4} fill="#64748b" fontSize="10" textAnchor="end">
              {`¥${(v / 10000).toFixed(0)}万`}
            </text>
          </g>
        ))}
        {data.filter((_, i) => i % xLabelStep === 0).map((d, _i, _arr) => {
          const orig = data.indexOf(d);
          return (
            <text key={d.date} x={xScale(orig)} y={H - pad.b + 16} fill="#64748b" fontSize="10" textAnchor="middle">
              {d.date.slice(5)}
            </text>
          );
        })}
        {data.length === 1 ? (
          <>
            <circle cx={xScale(0)} cy={yScale(data[0].total_value)} r="4" fill="#2563eb" />
            <circle cx={xScale(0)} cy={yScale(data[0].holdings_value)} r="3" fill="#10b981" />
            <circle cx={xScale(0)} cy={yScale(data[0].cash)} r="3" fill="#94a3b8" />
          </>
        ) : (
          <>
            <path d={path('total_value')} fill="none" stroke="#2563eb" strokeWidth="2" />
            <path d={path('holdings_value')} fill="none" stroke="#10b981" strokeWidth="1.5" />
            <path d={path('cash')} fill="none" stroke="#94a3b8" strokeWidth="1.5" />
          </>
        )}
        <g transform={`translate(${pad.l + 10}, ${pad.t + 6})`}>
          <rect width="14" height="2" y="5" fill="#2563eb" />
          <text x="18" y="9" fill="#475569" fontSize="11">総資産</text>
          <rect width="14" height="2" y="5" x="60" fill="#10b981" />
          <text x="78" y="9" fill="#475569" fontSize="11">保有評価額</text>
          <rect width="14" height="2" y="5" x="145" fill="#94a3b8" />
          <text x="163" y="9" fill="#475569" fontSize="11">現金</text>
        </g>
      </svg>
    </div>
  );
};

const PaperTradePage = () => {
  const [account, setAccount] = useState<AccountInitialized | null>(null);
  const [summary, setSummary] = useState<PaperSummary | null>(null);
  const [holdings, setHoldings] = useState<PaperHolding[]>([]);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [chart, setChart] = useState<ChartPoint[]>([]);
  const [performance, setPerformance] = useState<PerformanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [initOpen, setInitOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [buyOpen, setBuyOpen] = useState(false);
  const [sellingHolding, setSellingHolding] = useState<PaperHolding | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const acc = await paperTradeApi.getAccount();
      if (!acc.initialized) {
        setAccount(null);
        setSummary(null);
        setHoldings([]);
        setTrades([]);
        setChart([]);
        setPerformance([]);
        return;
      }
      setAccount(acc);
      const [s, h, t, c, p] = await Promise.all([
        paperTradeApi.getSummary(),
        paperTradeApi.listHoldings(),
        paperTradeApi.listTrades(100, 0),
        paperTradeApi.getChart(),
        paperTradeApi.getPerformance(),
      ]);
      setSummary(s);
      setHoldings(h);
      setTrades(t.items);
      setChart(c);
      setPerformance(p);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (loading) return <div className="p-6 text-sm text-slate-500">読み込み中...</div>;

  if (!account) {
    return (
      <>
        <PageHeader title="ペーパートレード" description="仮想資金で売買を試す" />
        <Card>
          <CardBody>
            <EmptyState
              title="仮想口座を作成しましょう"
              description="初期資金を設定すると、擬似的な売買シミュレーションを開始できます。"
            />
            <div className="flex justify-center pt-4">
              <Button variant="accent" onClick={() => setInitOpen(true)}>
                初期資金を設定して開始
              </Button>
            </div>
          </CardBody>
        </Card>
        <InitCapitalDialog
          open={initOpen}
          onClose={() => setInitOpen(false)}
          onInitialized={refresh}
        />
      </>
    );
  }

  const s = summary;

  return (
    <div>
      <PageHeader
        title="ペーパートレード"
        description="仮想資金で売買を試す"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setResetOpen(true)}>リセット</Button>
            <Button variant="accent" onClick={() => setBuyOpen(true)}>買い付け</Button>
          </div>
        }
      />
      <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-6 mb-4">
        <Stat label="総資産" value={formatYen(s?.total_value)} accent="brand" />
        <Stat label="現金残高" value={formatYen(s?.cash_balance)} />
        <Stat label="保有評価額" value={formatYen(s?.holdings_value)} />
        <Stat label="含み損益" value={formatYen(s?.unrealized_pl)} accent={(s?.unrealized_pl ?? 0) >= 0 ? 'success' : 'danger'} />
        <Stat label="実現損益" value={formatYen(s?.realized_pl)} accent={(s?.realized_pl ?? 0) >= 0 ? 'success' : 'danger'} />
        <Stat label="リターン" value={formatPct(s?.return_pct)} accent={(s?.return_pct ?? 0) >= 0 ? 'success' : 'danger'} />
      </div>

      {chart.length > 0 && (
        <Card className="mb-4">
          <CardBody>
            <h2 className="mb-2 text-base font-semibold text-slate-900">資産推移</h2>
            <AssetChart data={chart} />
          </CardBody>
        </Card>
      )}

      <Card className="mb-4">
        <CardBody>
          <h2 className="mb-3 text-base font-semibold text-slate-900">保有銘柄 ({holdings.length})</h2>
          {holdings.length === 0 ? (
            <EmptyState title="保有銘柄がありません" description="「買い付け」から擬似取引を開始してください。" />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>銘柄</Th>
                  <Th className="text-right">株数</Th>
                  <Th className="text-right">取得単価</Th>
                  <Th className="text-right">現在値</Th>
                  <Th className="text-right">評価額</Th>
                  <Th className="text-right">含み損益</Th>
                  <Th></Th>
                </Tr>
              </Thead>
              <Tbody>
                {holdings.map((h) => (
                  <Tr key={h.id}>
                    <Td>
                      <Link to={`/paper-trade/symbols/${encodeURIComponent(h.symbol)}`} className="text-brand-600 hover:underline">
                        <div className="font-semibold">{h.symbol}</div>
                        <div className="text-xs text-slate-500">{h.name}</div>
                      </Link>
                    </Td>
                    <Td className="text-right">{h.quantity.toLocaleString()}</Td>
                    <Td className="text-right">{formatYen(h.avg_price)}</Td>
                    <Td className="text-right">{formatYen(h.current_price)}</Td>
                    <Td className="text-right">{formatYen(h.market_value)}</Td>
                    <Td className="text-right">
                      <div className={(h.unrealized_pl ?? 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}>
                        {formatYen(h.unrealized_pl)}
                        <div className="text-xs">{formatPct(h.unrealized_pl_pct)}</div>
                      </div>
                    </Td>
                    <Td className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => setSellingHolding(h)}>売却</Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      {performance.length > 0 && (
        <Card className="mb-4">
          <CardBody>
            <h2 className="mb-3 text-base font-semibold text-slate-900">銘柄別パフォーマンス</h2>
            <Table>
              <Thead>
                <Tr>
                  <Th>銘柄</Th>
                  <Th className="text-right">取引回数</Th>
                  <Th className="text-right">勝ち</Th>
                  <Th className="text-right">実現損益</Th>
                  <Th className="text-right">含み損益</Th>
                  <Th className="text-right">合計損益</Th>
                  <Th className="text-right">リターン</Th>
                </Tr>
              </Thead>
              <Tbody>
                {performance.map((p) => (
                  <Tr key={p.symbol}>
                    <Td>
                      <Link to={`/paper-trade/symbols/${encodeURIComponent(p.symbol)}`} className="text-brand-600 hover:underline">
                        <div className="font-semibold">{p.symbol}</div>
                        <div className="text-xs text-slate-500">{p.name}</div>
                      </Link>
                    </Td>
                    <Td className="text-right">{p.trade_count}</Td>
                    <Td className="text-right">{p.win_count}</Td>
                    <Td className={'text-right ' + (p.realized_pl >= 0 ? 'text-emerald-700' : 'text-rose-700')}>{formatYen(p.realized_pl)}</Td>
                    <Td className={'text-right ' + (p.unrealized_pl >= 0 ? 'text-emerald-700' : 'text-rose-700')}>{formatYen(p.unrealized_pl)}</Td>
                    <Td className={'text-right ' + (p.total_pl >= 0 ? 'text-emerald-700' : 'text-rose-700')}>{formatYen(p.total_pl)}</Td>
                    <Td className="text-right">{formatPct(p.return_pct)}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardBody>
          <h2 className="mb-3 text-base font-semibold text-slate-900">取引履歴 ({trades.length})</h2>
          {trades.length === 0 ? (
            <EmptyState title="取引履歴がありません" description="" />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>日時</Th>
                  <Th>銘柄</Th>
                  <Th>区分</Th>
                  <Th className="text-right">数量</Th>
                  <Th className="text-right">単価</Th>
                  <Th className="text-right">約定額</Th>
                  <Th className="text-right">実現損益</Th>
                </Tr>
              </Thead>
              <Tbody>
                {trades.map((t) => (
                  <Tr key={t.id}>
                    <Td>{new Date(t.executed_at).toLocaleString()}</Td>
                    <Td>
                      <Link to={`/paper-trade/symbols/${encodeURIComponent(t.symbol)}`} className="text-brand-600 hover:underline">
                        {t.symbol}
                      </Link>
                    </Td>
                    <Td>
                      <Badge tone={t.action === 'buy' ? 'brand' : 'warn'}>{t.action === 'buy' ? '買' : '売'}</Badge>
                    </Td>
                    <Td className="text-right">{t.quantity.toLocaleString()}</Td>
                    <Td className="text-right">{formatYen(t.price)}</Td>
                    <Td className="text-right">{formatYen(t.total_amount)}</Td>
                    <Td className="text-right">
                      {t.realized_pl != null ? (
                        <span className={t.realized_pl >= 0 ? 'text-emerald-700' : 'text-rose-700'}>{formatYen(t.realized_pl)}</span>
                      ) : '—'}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      <ResetConfirmDialog open={resetOpen} onClose={() => setResetOpen(false)} currentInitialCash={account.initial_cash} onReset={refresh} />
      <BuyDialog open={buyOpen} onClose={() => setBuyOpen(false)} cashBalance={account.cash_balance} onSubmitted={refresh} />
      <SellDialog open={sellingHolding !== null} onClose={() => setSellingHolding(null)} holding={sellingHolding} onSubmitted={refresh} />
    </div>
  );
};

export default PaperTradePage;
