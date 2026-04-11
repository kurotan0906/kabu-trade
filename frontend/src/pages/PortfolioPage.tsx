import { useEffect, useState } from 'react';
import { portfolioApi } from '@/services/api/portfolioApi';
import PhaseIndicator from '@/components/portfolio/PhaseIndicator';
import AddHoldingDialog from '@/components/portfolio/AddHoldingDialog';
import type { Holding, PortfolioSettings, PortfolioSummary } from '@/types/portfolio';
import {
  PageHeader,
  Button,
  Stat,
  Badge,
  Card,
  CardBody,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  EmptyState,
  Dialog,
  Field,
  NumberInput,
  Input,
} from '@/components/ui';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const accountLabel = (t: Holding['account_type']) =>
  t === 'general' ? '一般' : t === 'nisa_growth' ? 'NISA成長' : 'NISAつみたて';

const accountTone = (t: Holding['account_type']): 'brand' | 'warn' | 'slate' =>
  t === 'nisa_growth' ? 'warn' : t === 'nisa_tsumitate' ? 'brand' : 'slate';

const PortfolioPage = () => {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [settings, setSettings] = useState<PortfolioSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [h, s, st] = await Promise.all([
        portfolioApi.listHoldings(),
        portfolioApi.getSummary(),
        portfolioApi.getSettings(),
      ]);
      setHoldings(h);
      setSummary(s);
      setSettings(st);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('この保有銘柄を削除しますか？')) return;
    await portfolioApi.deleteHolding(id);
    await refresh();
  };

  const progressLabel =
    summary?.progress_rate != null ? `${summary.progress_rate.toFixed(1)}%` : '目標未設定';
  const plAccent: 'success' | 'danger' =
    summary && summary.unrealized_pl >= 0 ? 'success' : 'danger';

  return (
    <div>
      <PageHeader
        title="ポートフォリオ"
        description="保有銘柄と目標設定を管理します。"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setSettingsOpen(true)}>
              目標設定
            </Button>
            <Button variant="accent" onClick={() => setAddOpen(true)}>
              + 銘柄追加
            </Button>
          </div>
        }
      />

      {loading ? (
        <div className="p-6 text-sm text-slate-500">読み込み中...</div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat label="評価額合計" value={formatYen(summary?.total_value)} />
            <Stat
              label="含み損益"
              value={formatYen(summary?.unrealized_pl)}
              accent={plAccent}
            />
            <Stat
              label="目標進捗"
              value={progressLabel}
              hint={summary?.target_amount ? `目標: ${formatYen(summary.target_amount)}` : undefined}
            />
            <Stat label="NISA成長枠 残" value={formatYen(summary?.nisa_remaining)} />
          </div>

          <PhaseIndicator
            phase={summary?.current_phase ?? null}
            progressRate={summary?.progress_rate ?? null}
          />

          <Card>
            <CardBody>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-semibold text-slate-900">
                  保有銘柄 ({holdings.length})
                </h2>
              </div>
              {holdings.length === 0 ? (
                <EmptyState
                  title="保有銘柄がありません"
                  description="「+ 銘柄追加」から登録してください。"
                />
              ) : (
                <Table>
                  <Thead>
                    <Tr>
                      <Th>銘柄</Th>
                      <Th>口座</Th>
                      <Th className="text-right">株数</Th>
                      <Th className="text-right">取得単価</Th>
                      <Th className="text-right">取得額</Th>
                      <Th></Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {holdings.map((h) => (
                      <Tr key={h.id}>
                        <Td>
                          <div className="font-semibold text-slate-900">{h.symbol}</div>
                          <div className="text-xs text-slate-500">{h.name}</div>
                        </Td>
                        <Td>
                          <Badge tone={accountTone(h.account_type)}>
                            {accountLabel(h.account_type)}
                          </Badge>
                        </Td>
                        <Td className="text-right">{h.quantity.toLocaleString()}</Td>
                        <Td className="text-right">{formatYen(h.avg_price)}</Td>
                        <Td className="text-right">{formatYen(h.quantity * h.avg_price)}</Td>
                        <Td className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(h.id)}
                          >
                            削除
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              )}
            </CardBody>
          </Card>
        </div>
      )}

      <AddHoldingDialog
        open={addOpen}
        onClose={() => setAddOpen(false)}
        symbol=""
        name={null}
        onCreated={refresh}
      />

      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onSaved={async (patch) => {
          const updated = await portfolioApi.updateSettings(patch);
          setSettings(updated);
          await refresh();
          setSettingsOpen(false);
        }}
      />
    </div>
  );
};

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
  settings: PortfolioSettings | null;
  onSaved: (patch: Partial<PortfolioSettings>) => Promise<void>;
}

const SettingsDialog = ({ open, onClose, settings, onSaved }: SettingsDialogProps) => {
  const [target, setTarget] = useState<number>(settings?.target_amount ?? 0);
  const [monthly, setMonthly] = useState<number>(settings?.monthly_investment ?? 0);
  const [deadline, setDeadline] = useState<string>(settings?.target_deadline ?? '');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setTarget(settings?.target_amount ?? 0);
      setMonthly(settings?.monthly_investment ?? 0);
      setDeadline(settings?.target_deadline ?? '');
      setError(null);
    }
  }, [open, settings]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSaved({
        target_amount: target > 0 ? target : null,
        monthly_investment: monthly > 0 ? monthly : null,
        target_deadline: deadline || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="目標設定" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="目標額 (円)">
          <NumberInput value={target} onChange={setTarget} min={0} />
        </Field>
        <Field label="毎月積立 (円)">
          <NumberInput value={monthly} onChange={setMonthly} min={0} />
        </Field>
        <Field label="達成期限">
          <Input
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
          />
        </Field>
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? '保存中...' : '保存'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default PortfolioPage;
