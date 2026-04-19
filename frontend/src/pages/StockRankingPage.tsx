import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scoresApi, type SortField } from '@/services/api/scoresApi';
import type { StockScore, BatchStatus, ProfileKey } from '@/types/stockScore';
import { tradingviewApi } from '@/services/api/tradingviewApi';
import type { TradingViewSignal } from '@/types/tradingviewSignal';
import ProfileSelector from '@/components/stock/ProfileSelector';
import {
  PageHeader,
  Toolbar,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Progress,
  EmptyState,
  Card,
  CardBody,
} from '@/components/ui';
import HoldingDialog from '@/components/portfolio/HoldingDialog';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const RATING_TONE: Record<string, 'brand' | 'success' | 'slate' | 'warn' | 'danger'> = {
  '強い買い': 'brand',
  '買い': 'success',
  '中立': 'slate',
  '売り': 'warn',
  '強い売り': 'danger',
};

const TV_TONE: Record<string, 'brand' | 'success' | 'slate' | 'warn' | 'danger'> = {
  STRONG_BUY: 'success',
  BUY: 'brand',
  NEUTRAL: 'slate',
  SELL: 'warn',
  STRONG_SELL: 'danger',
};

const StockRankingPage = () => {
  const [scores, setScores] = useState<StockScore[]>([]);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [tvSignals, setTvSignals] = useState<Record<string, TradingViewSignal>>({});
  const [profile, setProfile] = useState<ProfileKey | 'none'>('none');
  const [sort, setSort] = useState<SortField>('total_score');
  const [addTarget, setAddTarget] = useState<{ symbol: string; name: string | null } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    const tvPromise = tradingviewApi.listSignals().catch(() => [] as TradingViewSignal[]);
    const profileParam: ProfileKey | undefined = profile === 'none' ? undefined : profile;
    Promise.all([
      scoresApi.listScores(sort, 100, profileParam),
      scoresApi.getBatchStatus(),
      tvPromise,
    ])
      .then(([s, b, tv]) => {
        setScores(s);
        setBatchStatus(b);
        const map: Record<string, TradingViewSignal> = {};
        tv.forEach((sig) => {
          map[sig.symbol] = sig;
        });
        setTvSignals(map);
      })
      .finally(() => setLoading(false));
  }, [profile, sort]);

  const handleTriggerBatch = async () => {
    setTriggering(true);
    try {
      await scoresApi.triggerBatch();
      alert('バッチスコアリングを開始しました');
    } catch {
      alert('エラーが発生しました');
    } finally {
      setTriggering(false);
    }
  };

  const primaryScore = (s: StockScore) =>
    profile === 'none' ? s.total_score : s.profile_score ?? s.total_score;

  const description = batchStatus
    ? `最終更新: ${
        batchStatus.finished_at
          ? new Date(batchStatus.finished_at).toLocaleString('ja-JP')
          : '未実行'
      }${batchStatus.status === 'running' ? '（実行中...）' : ''}`
    : undefined;

  return (
    <div>
      <PageHeader
        title="銘柄スコアランキング"
        description={description}
        actions={
          <>
            <Button
              variant="accent"
              onClick={handleTriggerBatch}
              disabled={triggering || batchStatus?.status === 'running'}
            >
              {triggering ? '開始中...' : 'スコアリング実行'}
            </Button>
            <Button
              variant="secondary"
              onClick={() =>
                alert(
                  'Claude Code で「スコア上位100銘柄をTradingView一括分析して /api/v1/tradingview-signals に保存して」と依頼してください'
                )
              }
            >
              TVバッチ分析
            </Button>
          </>
        }
      />

      <Toolbar>
        <ProfileSelector value={profile} onChange={setProfile} />
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <span>並び替え:</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortField)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
          >
            <option value="total_score">総合スコア</option>
            <option value="kurotenko_score">黒転株（黒点子）</option>
            <option value="fundamental_score">ファンダメンタル</option>
            <option value="technical_score">テクニカル</option>
          </select>
        </label>
      </Toolbar>

      {loading ? (
        <div className="p-6 text-sm text-slate-500">読み込み中...</div>
      ) : scores.length === 0 ? (
        <EmptyState
          title="スコアデータがありません"
          description="「スコアリング実行」ボタンからバッチを開始してください。"
        />
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block">
            <Table>
              <Thead>
                <Tr>
                  <Th className="w-12">#</Th>
                  <Th>銘柄</Th>
                  <Th>
                    {profile === 'none'
                      ? '総合スコア'
                      : scores[0]?.profile_name ?? 'プロファイル'}
                  </Th>
                  <Th>レーティング</Th>
                  <Th>ファンダ</Th>
                  <Th>テクニカル</Th>
                  <Th>黒点子</Th>
                  <Th>TVシグナル</Th>
                  <Th className="text-right">現在値</Th>
                  <Th className="text-right">操作</Th>
                </Tr>
              </Thead>
              <Tbody>
                {scores.map((s, i) => {
                  const tvSig = tvSignals[s.symbol.replace('.T', '')];
                  const score = primaryScore(s);
                  return (
                    <Tr key={s.id}>
                      <Td className="text-slate-500">{i + 1}</Td>
                      <Td>
                        <button
                          type="button"
                          onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}
                          className="text-left"
                        >
                          <div className="font-semibold text-brand-600 hover:underline">
                            {s.symbol}
                          </div>
                          <div className="text-xs text-slate-500">{s.name ?? '—'}</div>
                        </button>
                      </Td>
                      <Td className="min-w-[140px]">
                        {score !== null ? (
                          <div className="flex items-center gap-2">
                            <Progress value={score} className="w-24" />
                            <span className="tabular-nums text-xs font-semibold text-slate-700">
                              {Math.round(score)}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </Td>
                      <Td>
                        {s.rating ? (
                          <Badge tone={RATING_TONE[s.rating] ?? 'slate'}>{s.rating}</Badge>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </Td>
                      <Td className="tabular-nums text-slate-700">
                        {s.fundamental_score !== null ? Math.round(s.fundamental_score) : '—'}
                      </Td>
                      <Td className="tabular-nums text-slate-700">
                        {s.technical_score !== null ? Math.round(s.technical_score) : '—'}
                      </Td>
                      <Td className="tabular-nums text-slate-700">
                        {s.kurotenko_score !== null
                          ? `${Math.round(s.kurotenko_score)}%`
                          : '—'}
                      </Td>
                      <Td>
                        {tvSig && tvSig.recommendation ? (
                          <Badge tone={TV_TONE[tvSig.recommendation] ?? 'slate'}>
                            {tvSig.recommendation.replaceAll('_', ' ')}
                          </Badge>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </Td>
                      <Td className="text-right tabular-nums text-slate-700">
                        {formatYen(s.close_price)}
                      </Td>
                      <Td className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() =>
                              navigate(`/stocks/${s.symbol.replace('.T', '')}`)
                            }
                          >
                            詳細
                          </Button>
                          <Button
                            size="sm"
                            variant="accent"
                            onClick={() =>
                              setAddTarget({ symbol: s.symbol, name: s.name })
                            }
                          >
                            追加
                          </Button>
                        </div>
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </div>

          {/* Mobile card list */}
          <div className="md:hidden flex flex-col gap-3">
            {scores.map((s, i) => {
              const tvSig = tvSignals[s.symbol.replace('.T', '')];
              const score = primaryScore(s);
              return (
                <Card key={s.id}>
                  <CardBody className="pt-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-xs text-slate-500">#{i + 1}</div>
                        <div className="font-semibold text-brand-600">{s.symbol}</div>
                        <div className="text-xs text-slate-500">{s.name ?? '—'}</div>
                      </div>
                      {s.rating && (
                        <Badge tone={RATING_TONE[s.rating] ?? 'slate'}>{s.rating}</Badge>
                      )}
                    </div>
                    <div className="mt-3">
                      <div className="text-xs text-slate-500 mb-1">
                        {profile === 'none'
                          ? '総合スコア'
                          : s.profile_name ?? 'プロファイル'}
                      </div>
                      {score !== null ? (
                        <div className="flex items-center gap-2">
                          <Progress value={score} className="flex-1" />
                          <span className="text-xs font-semibold tabular-nums">
                            {Math.round(score)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 text-sm">—</span>
                      )}
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-600">
                      <div>
                        <div className="text-slate-400">ファンダ</div>
                        <div className="tabular-nums font-semibold">
                          {s.fundamental_score !== null
                            ? Math.round(s.fundamental_score)
                            : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400">テクニカル</div>
                        <div className="tabular-nums font-semibold">
                          {s.technical_score !== null
                            ? Math.round(s.technical_score)
                            : '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400">黒点子</div>
                        <div className="tabular-nums font-semibold">
                          {s.kurotenko_score !== null
                            ? `${Math.round(s.kurotenko_score)}%`
                            : '—'}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-slate-600">
                      <span className="text-slate-400">現在値: </span>
                      <span className="tabular-nums font-semibold text-slate-700">
                        {formatYen(s.close_price)}
                      </span>
                    </div>
                    {tvSig && tvSig.recommendation && (
                      <div className="mt-3">
                        <Badge tone={TV_TONE[tvSig.recommendation] ?? 'slate'}>
                          TV: {tvSig.recommendation.replaceAll('_', ' ')}
                        </Badge>
                      </div>
                    )}
                    <div className="mt-4 flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="flex-1"
                        onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}
                      >
                        詳細
                      </Button>
                      <Button
                        size="sm"
                        variant="accent"
                        className="flex-1"
                        onClick={() => setAddTarget({ symbol: s.symbol, name: s.name })}
                      >
                        追加
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        </>
      )}

      {addTarget && (
        <HoldingDialog
          mode="create"
          open={!!addTarget}
          onClose={() => setAddTarget(null)}
          defaultSymbol={addTarget.symbol}
          defaultName={addTarget.name}
        />
      )}
    </div>
  );
};

export default StockRankingPage;
