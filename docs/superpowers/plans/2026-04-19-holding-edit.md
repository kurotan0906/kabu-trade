# 保有銘柄編集機能 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ポートフォリオ画面から保有銘柄の各項目（銘柄名、株数、取得単価、取得日、口座区分）をモーダルダイアログで編集できるようにする。

**Architecture:** 既存の `AddHoldingDialog` を `HoldingDialog` にリネーム・汎用化し、`mode: 'create' | 'edit'` で追加・編集の両方に対応。バックエンドAPI (`PUT /portfolio/holdings/{id}`) と `portfolioApi.updateHolding()` は変更不要。

**Tech Stack:** React 18 + TypeScript + Tailwind v4 + 既存 UI primitives（`Dialog`, `Field`, `Input`, `NumberInput`, `Select`, `Button`）

**仕様書:** `docs/superpowers/specs/2026-04-19-holding-edit-design.md`

**備考:** フロントエンドに自動テスト基盤が無いため、TDDの「failing test」ステップは `npm run build`（`tsc` による型チェック）＋ブラウザ手動確認に置き換える。

---

## ファイル構成

| 操作 | パス | 責務 |
|---|---|---|
| Create | `frontend/src/components/portfolio/HoldingDialog.tsx` | 追加・編集両対応のモーダル |
| Delete | `frontend/src/components/portfolio/AddHoldingDialog.tsx` | 置き換え対象 |
| Modify | `frontend/src/pages/PortfolioPage.tsx` | 編集ボタン追加、編集ダイアログ配線 |
| Modify | `frontend/src/pages/StockDetailPage.tsx` | import を新コンポーネントに切替 |
| Modify | `frontend/src/pages/StockRankingPage.tsx` | import を新コンポーネントに切替 |

---

## Task 1: HoldingDialog コンポーネントを作成（create/edit 両対応）

既存 `AddHoldingDialog` のロジックを汎用化した新コンポーネントを追加する。この時点では旧 `AddHoldingDialog` は残しておき、既存の利用箇所は壊さない。

**Files:**
- Create: `frontend/src/components/portfolio/HoldingDialog.tsx`

- [ ] **Step 1: 新ファイルを作成**

```tsx
import { useEffect, useState } from 'react';
import { Dialog, Field, Input, Select, NumberInput, Button } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { AccountType, Holding, HoldingCreate } from '@/types/portfolio';

type Mode = 'create' | 'edit';

interface Props {
  open: boolean;
  onClose: () => void;
  mode: Mode;
  /** create モード時の初期 symbol（省略時は空文字） */
  defaultSymbol?: string;
  /** create モード時の初期 name */
  defaultName?: string | null;
  /** edit モード時の編集対象 holding（mode="edit" の時は必須） */
  holding?: Holding;
  /** 作成/保存成功時に呼ばれる */
  onSaved?: () => void;
}

const emptyDraft = (symbol: string, name?: string | null): HoldingCreate => ({
  symbol,
  name: name ?? null,
  quantity: 0,
  avg_price: 0,
  purchase_date: null,
  account_type: 'general',
});

const draftFromHolding = (h: Holding): HoldingCreate => ({
  symbol: h.symbol,
  name: h.name,
  quantity: h.quantity,
  avg_price: h.avg_price,
  purchase_date: h.purchase_date,
  account_type: h.account_type,
});

export const HoldingDialog = ({
  open,
  onClose,
  mode,
  defaultSymbol = '',
  defaultName = null,
  holding,
  onSaved,
}: Props) => {
  const [draft, setDraft] = useState<HoldingCreate>(() =>
    mode === 'edit' && holding ? draftFromHolding(holding) : emptyDraft(defaultSymbol, defaultName)
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!open) return;
    if (mode === 'edit' && holding) {
      setDraft(draftFromHolding(holding));
    } else {
      setDraft(emptyDraft(defaultSymbol, defaultName));
    }
    setError(null);
    setSuccess(false);
  }, [open, mode, holding, defaultSymbol, defaultName]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.symbol || draft.quantity <= 0 || draft.avg_price <= 0) {
      setError('銘柄コード、株数、取得単価を入力してください。');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (mode === 'edit' && holding) {
        await portfolioApi.updateHolding(holding.id, {
          name: draft.name,
          quantity: draft.quantity,
          avg_price: draft.avg_price,
          purchase_date: draft.purchase_date,
          account_type: draft.account_type,
        });
      } else {
        await portfolioApi.createHolding(draft);
      }
      setSuccess(true);
      onSaved?.();
      setTimeout(() => {
        onClose();
      }, 600);
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : mode === 'edit'
            ? '保存に失敗しました'
            : '登録に失敗しました';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const title = mode === 'edit' ? '保有銘柄を編集' : '保有銘柄を追加';
  const submitLabel = mode === 'edit' ? '保存' : '追加する';
  const submittingLabel = mode === 'edit' ? '保存中...' : '追加中...';
  const successLabel = mode === 'edit' ? '保存しました。' : '追加しました。';

  return (
    <Dialog open={open} onClose={onClose} title={title} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="銘柄コード">
            <Input
              value={draft.symbol}
              onChange={(e) => setDraft({ ...draft, symbol: e.target.value })}
              placeholder="7203.T"
              required
              disabled={mode === 'edit'}
            />
          </Field>
          <Field label="銘柄名">
            <Input
              value={draft.name ?? ''}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="トヨタ自動車"
            />
          </Field>
          <Field label="株数">
            <NumberInput
              value={draft.quantity}
              onChange={(v) => setDraft({ ...draft, quantity: v })}
              min={0}
            />
          </Field>
          <Field label="取得単価 (円)">
            <NumberInput
              value={draft.avg_price}
              onChange={(v) => setDraft({ ...draft, avg_price: v })}
              min={0}
              step={0.01}
            />
          </Field>
          <Field label="取得日">
            <Input
              type="date"
              value={draft.purchase_date ?? ''}
              onChange={(e) =>
                setDraft({ ...draft, purchase_date: e.target.value || null })
              }
            />
          </Field>
          <Field label="口座区分">
            <Select
              value={draft.account_type}
              onChange={(e) =>
                setDraft({ ...draft, account_type: e.target.value as AccountType })
              }
            >
              <option value="general">特定/一般</option>
              <option value="nisa_growth">NISA成長枠</option>
              <option value="nisa_tsumitate">NISAつみたて</option>
            </Select>
          </Field>
        </div>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
            {successLabel}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? submittingLabel : submitLabel}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default HoldingDialog;
```

- [ ] **Step 2: 型チェック**

Run: `cd frontend && npm run build`
Expected: エラーなく完了（`dist/` 生成）

- [ ] **Step 3: コミット**

```bash
git add frontend/src/components/portfolio/HoldingDialog.tsx
git commit -m "feat(portfolio): HoldingDialog コンポーネント追加（create/edit両対応）"
```

---

## Task 2: PortfolioPage の呼び出しを HoldingDialog に置換（まだ create モードのみ）

既存 `AddHoldingDialog` の利用を新 `HoldingDialog` に切り替える。編集機能の配線はまだせず、動作が崩れないことだけを確認。

**Files:**
- Modify: `frontend/src/pages/PortfolioPage.tsx:4` (import)
- Modify: `frontend/src/pages/PortfolioPage.tsx:241-247` (利用箇所)

- [ ] **Step 1: import 文を書き換え**

置換前 (`frontend/src/pages/PortfolioPage.tsx:4`):
```tsx
import AddHoldingDialog from '@/components/portfolio/AddHoldingDialog';
```

置換後:
```tsx
import HoldingDialog from '@/components/portfolio/HoldingDialog';
```

- [ ] **Step 2: JSX 呼び出し箇所を書き換え**

置換前 (`frontend/src/pages/PortfolioPage.tsx:241-247`):
```tsx
      <AddHoldingDialog
        open={addOpen}
        onClose={() => setAddOpen(false)}
        symbol=""
        name={null}
        onCreated={refresh}
      />
```

置換後:
```tsx
      <HoldingDialog
        mode="create"
        open={addOpen}
        onClose={() => setAddOpen(false)}
        defaultSymbol=""
        defaultName={null}
        onSaved={refresh}
      />
```

- [ ] **Step 3: 型チェック**

Run: `cd frontend && npm run build`
Expected: エラーなく完了

- [ ] **Step 4: コミット**

```bash
git add frontend/src/pages/PortfolioPage.tsx
git commit -m "refactor(portfolio): PortfolioPage を HoldingDialog に移行"
```

---

## Task 3: StockDetailPage の呼び出しを HoldingDialog に置換

**Files:**
- Modify: `frontend/src/pages/StockDetailPage.tsx:25` (import)
- Modify: `frontend/src/pages/StockDetailPage.tsx:228-233` (利用箇所)

- [ ] **Step 1: import 文を書き換え**

置換前 (`frontend/src/pages/StockDetailPage.tsx:25`):
```tsx
import AddHoldingDialog from '@/components/portfolio/AddHoldingDialog';
```

置換後:
```tsx
import HoldingDialog from '@/components/portfolio/HoldingDialog';
```

- [ ] **Step 2: JSX 呼び出し箇所を書き換え**

置換前 (`frontend/src/pages/StockDetailPage.tsx:228-233`):
```tsx
        <AddHoldingDialog
          open={addOpen}
          onClose={() => setAddOpen(false)}
          symbol={currentStock.code}
          name={currentStock.name ?? null}
        />
```

置換後:
```tsx
        <HoldingDialog
          mode="create"
          open={addOpen}
          onClose={() => setAddOpen(false)}
          defaultSymbol={currentStock.code}
          defaultName={currentStock.name ?? null}
        />
```

- [ ] **Step 3: 型チェック**

Run: `cd frontend && npm run build`
Expected: エラーなく完了

- [ ] **Step 4: コミット**

```bash
git add frontend/src/pages/StockDetailPage.tsx
git commit -m "refactor(stock-detail): HoldingDialog に移行"
```

---

## Task 4: StockRankingPage の呼び出しを HoldingDialog に置換

**Files:**
- Modify: `frontend/src/pages/StockRankingPage.tsx:24` (import)
- Modify: `frontend/src/pages/StockRankingPage.tsx:353-358` (利用箇所)

- [ ] **Step 1: import 文を書き換え**

置換前 (`frontend/src/pages/StockRankingPage.tsx:24`):
```tsx
import AddHoldingDialog from '@/components/portfolio/AddHoldingDialog';
```

置換後:
```tsx
import HoldingDialog from '@/components/portfolio/HoldingDialog';
```

- [ ] **Step 2: JSX 呼び出し箇所を書き換え**

置換前 (`frontend/src/pages/StockRankingPage.tsx:353-358`):
```tsx
        <AddHoldingDialog
          open={!!addTarget}
          onClose={() => setAddTarget(null)}
          symbol={addTarget.symbol}
          name={addTarget.name}
        />
```

置換後:
```tsx
        <HoldingDialog
          mode="create"
          open={!!addTarget}
          onClose={() => setAddTarget(null)}
          defaultSymbol={addTarget.symbol}
          defaultName={addTarget.name}
        />
```

- [ ] **Step 3: 型チェック**

Run: `cd frontend && npm run build`
Expected: エラーなく完了

- [ ] **Step 4: コミット**

```bash
git add frontend/src/pages/StockRankingPage.tsx
git commit -m "refactor(stock-ranking): HoldingDialog に移行"
```

---

## Task 5: 旧 AddHoldingDialog.tsx を削除

全利用箇所の移行が終わったため、旧ファイルを削除する。

**Files:**
- Delete: `frontend/src/components/portfolio/AddHoldingDialog.tsx`

- [ ] **Step 1: 残存参照が無いことを確認**

Run: `grep -rn "AddHoldingDialog" frontend/src`
Expected: 出力なし（0件）

- [ ] **Step 2: ファイル削除**

Run: `rm frontend/src/components/portfolio/AddHoldingDialog.tsx`

- [ ] **Step 3: 型チェック**

Run: `cd frontend && npm run build`
Expected: エラーなく完了

- [ ] **Step 4: コミット**

```bash
git add -A frontend/src/components/portfolio/AddHoldingDialog.tsx
git commit -m "chore(portfolio): 旧 AddHoldingDialog を削除"
```

---

## Task 6: PortfolioPage に編集UIを配線

保有銘柄テーブルに「編集」ボタンを追加し、クリックで `HoldingDialog` を `mode="edit"` で開く。

**Files:**
- Modify: `frontend/src/pages/PortfolioPage.tsx`

- [ ] **Step 1: state と handler を追加**

`PortfolioPage` 関数コンポーネント内、他の state 定義のすぐ下に `editingHolding` state を追加する。

置換前 (`frontend/src/pages/PortfolioPage.tsx:99-105` 付近):
```tsx
const PortfolioPage = () => {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [settings, setSettings] = useState<PortfolioSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
```

置換後:
```tsx
const PortfolioPage = () => {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [settings, setSettings] = useState<PortfolioSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editingHolding, setEditingHolding] = useState<Holding | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
```

- [ ] **Step 2: テーブルの操作列に「編集」ボタンを追加**

置換前 (`frontend/src/pages/PortfolioPage.tsx:222-230` 付近、`<Td className="text-right">` で削除ボタンのみ持つブロック):
```tsx
                        <Td className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(h.id)}
                          >
                            削除
                          </Button>
                        </Td>
```

置換後:
```tsx
                        <Td className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingHolding(h)}
                            >
                              編集
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(h.id)}
                            >
                              削除
                            </Button>
                          </div>
                        </Td>
```

- [ ] **Step 3: 編集ダイアログを JSX に追加**

置換前 (`frontend/src/pages/PortfolioPage.tsx` の既存 `<HoldingDialog mode="create" ...>` の直後):
```tsx
      <HoldingDialog
        mode="create"
        open={addOpen}
        onClose={() => setAddOpen(false)}
        defaultSymbol=""
        defaultName={null}
        onSaved={refresh}
      />

      <SettingsDialog
```

置換後:
```tsx
      <HoldingDialog
        mode="create"
        open={addOpen}
        onClose={() => setAddOpen(false)}
        defaultSymbol=""
        defaultName={null}
        onSaved={refresh}
      />

      <HoldingDialog
        mode="edit"
        open={editingHolding !== null}
        onClose={() => setEditingHolding(null)}
        holding={editingHolding ?? undefined}
        onSaved={refresh}
      />

      <SettingsDialog
```

- [ ] **Step 4: 型チェック**

Run: `cd frontend && npm run build`
Expected: エラーなく完了

- [ ] **Step 5: コミット**

```bash
git add frontend/src/pages/PortfolioPage.tsx
git commit -m "feat(portfolio): 保有銘柄編集UIを追加"
```

---

## Task 7: ブラウザ手動確認

dev server を起動し、golden path と主要なエッジケースをブラウザで確認する。

- [ ] **Step 1: dev server 起動**

Run: `cd frontend && npm run dev`
Expected: `http://localhost:5173` で起動

- [ ] **Step 2: 追加フローが従来通り動くことを確認**

1. `/portfolio` を開く
2. 「+ 銘柄追加」をクリック
3. 適当な銘柄を入力して追加
4. 一覧に反映されることを確認

- [ ] **Step 3: 編集フローを確認**

1. 追加した保有銘柄の行で「編集」をクリック
2. ダイアログが開き、初期値が現在のデータで埋まっていることを確認
3. `symbol`（銘柄コード）がグレーアウトして編集不可になっていることを確認
4. `name`, `quantity`, `avg_price`, `purchase_date`, `account_type` を変更
5. 「保存」クリック
6. 「保存しました。」表示後、ダイアログが自動で閉じる
7. 一覧とサマリが更新されていることを確認

- [ ] **Step 4: バリデーションを確認**

1. 編集ダイアログを開く
2. 株数を 0 に変更して「保存」クリック
3. 「銘柄コード、株数、取得単価を入力してください。」エラーが表示されることを確認
4. 取得単価を 0 にしても同様
5. キャンセルして閉じる

- [ ] **Step 5: StockDetailPage / StockRankingPage の追加フローが壊れていないことを確認**

1. `/stocks/7203` を開き、「保有に追加」ボタンから追加ダイアログが正常に動くこと
2. `/ranking` を開き、任意の銘柄の追加ボタンからダイアログが正常に動くこと

- [ ] **Step 6: 削除ボタンが従来通り動くことを確認**

1. `/portfolio` で任意の銘柄を削除
2. 確認ダイアログで OK → 一覧から消える

- [ ] **Step 7: 動作OKなら最終確認コミット（差分があれば）**

dev server 確認のみで追加修正が無ければスキップ。修正があった場合のみコミット。

```bash
git status
# 必要に応じて
git add -A
git commit -m "fix(portfolio): 手動確認で見つかった問題を修正"
```

---

## 完了条件

- [ ] `npm run build` が通る
- [ ] 追加・編集・削除の3フローが手動確認でOK
- [ ] `grep -rn "AddHoldingDialog" frontend/src` が 0件
- [ ] StockDetailPage / StockRankingPage の追加フローが壊れていない

## 完了後の運用

- `~/.claude/projects/.../memory/` に本実装の進捗メモリを追加（global CLAUDE.md の規約に従う）
- `docs/superpowers/logs/2026-04-19-holding-edit.md` に実装サマリを記録
