# UI 全体刷新 設計書

作成日: 2026-04-11

## 背景

kabu-trade の React フロントエンドは機能追加を積み重ねた結果、以下の UX 問題を抱えている:

- **ナビゲーション不在**: `App.tsx` は 6 ルートを定義するだけで共通ヘッダーが無く、ページ間移動は URL 直打ちに依存。
- **インライン style の散在**: 全ページが `style={{...}}` 直書きで色 (`#1f2937`, `#a78bfa` 等) が重複定義され、トーン不統一。
- **導線切れ**: 銘柄詳細からポートフォリオに追加できない / ポートフォリオから銘柄詳細に戻れない等、機能間がリンクされていない。
- **ホームが貧弱**: HomePage は「Kabu Trade」見出しと検索ボックスのみで、ダッシュボード的な俯瞰が存在しない。
- **モバイル非対応**: 固定幅レイアウトとテーブル直置きで狭い画面で崩れる。

本設計は上記を解消し、Tailwind CSS v4 ベースの統一デザインシステム + AppShell + ダッシュボード型ホーム + ページ間導線を段階的に導入する。

## 要件サマリ

| 項目 | 決定 |
|---|---|
| スタイリング | **Tailwind CSS v4**（Vite 公式プラグイン `@tailwindcss/vite`） |
| ナビゲーション | **上部固定ヘッダー**（モバイルはハンバーガー + ドロワー） |
| ホーム | **ダッシュボード型**（KPI / TOP5 / 保有 / シグナル / クイックシミュ） |
| テーマ | **Clean Light**（slate-50 背景、violet-600 + slate-900 アクセント） |
| 導線 MUST | A. 詳細→ポートフォリオ追加 / B. ポートフォリオ銘柄→詳細 / C. ランキング行クイックアクション / D. ホームカード→ディープリンク / G. `⌘K` グローバル検索 |
| 対象デバイス | **PC / タブレット / スマホ**（375px〜レスポンシブ） |
| ロールアウト | **フェーズ分け**（基盤 → Shell/ホーム → 主要ページ → 補助ページ） |
| UI ライブラリ | 採用しない（Tailwind + `class-variance-authority` で自前プリミティブ） |

## 1. 基盤 (Foundation)

### 1.1 依存追加

```
tailwindcss@^4  @tailwindcss/vite  class-variance-authority  clsx
```

- `@tailwindcss/vite` を `vite.config.ts` に登録、`src/index.css` に `@import "tailwindcss"` を追加。
- Google Fonts `Inter` + `Noto Sans JP` を `index.html` で読み込む。

### 1.2 デザイントークン

`tailwind.config.ts` に以下を定義（Tailwind v4 は CSS ファースト設定も可）:

| トークン | 値 |
|---|---|
| `font-sans` | `'Inter','Noto Sans JP', ui-sans-serif, system-ui` |
| `color.bg` | `slate-50` (ベース) / `white` (カード) |
| `color.fg` | `slate-900` 本文 / `slate-500` セカンダリ |
| `color.accent` | `violet-600` (スコア/プログレス)、`slate-900` (CTA) |
| `color.success/warn/danger` | `emerald-500 / amber-500 / rose-500` |
| `radius` | `rounded-lg` = 10px、`rounded-md` = 6px |
| `shadow` | `shadow-sm` = カード基本、`shadow-md` = Dialog |
| `spacing` | Tailwind デフォルト、ページ余白は `p-4 md:p-6` |

### 1.3 UI プリミティブ (`frontend/src/components/ui/`)

| コンポーネント | 用途 |
|---|---|
| `Button` | CTA / Secondary / Ghost / Destructive (cva バリアント) |
| `Card`, `CardHeader`, `CardBody`, `CardFooter` | 情報ブロック |
| `Stat` | KPI 表示 (label + value + delta) |
| `Badge` | レーティング / フェーズ / シグナル |
| `Table`, `Thead`, `Tr`, `Td` | 共通テーブル（sticky header 対応） |
| `Input`, `Select`, `NumberInput` | フォーム |
| `Dialog` | モーダル (銘柄追加、検索、バッチ進捗) |
| `EmptyState` | データゼロ時の CTA 表示 |
| `PageHeader` | ページタイトル + アクション右寄せ |
| `Toolbar` | セレクタ/フィルタ行 |
| `Progress` | 横プログレスバー（進捗率・スコアバー兼用） |
| `Tabs` | 詳細ページのセクション切替 |

既存 `components/common/{ErrorMessage,Loading}.tsx` は `ui/` に吸収してリネーム。

### 1.4 不変条件

- **全ページのインライン `style` を廃止**する（SVG 内の `style` は許容）。
- `App.css` は Tailwind のベースレイヤ用に最小化し、グローバル CSS は追加しない。
- 色コードのハードコードは `ui/` 配下と `tailwind.config` 以外で禁止。

## 2. AppShell とナビゲーション

### 2.1 ルート再構成

`App.tsx` を以下に書き換え:

```tsx
<BrowserRouter>
  <Routes>
    <Route element={<AppShell />}>
      <Route path="/" element={<HomePage />} />
      <Route path="/ranking" element={<StockRankingPage />} />
      <Route path="/portfolio" element={<PortfolioPage />} />
      <Route path="/simulator" element={<SimulatorPage />} />
      <Route path="/history" element={<AnalysisHistoryPage />} />
      <Route path="/stocks/:code" element={<StockDetailPage />} />
    </Route>
  </Routes>
</BrowserRouter>
```

### 2.2 AppShell (`frontend/src/components/layout/AppShell.tsx`)

- `min-h-screen bg-slate-50 text-slate-900 font-sans`
- ヘッダー (`h-14 sticky top-0 bg-white/80 backdrop-blur border-b border-slate-200 z-40`)
- 本文 (`<main class="mx-auto max-w-6xl px-4 md:px-6 py-6"><Outlet /></main>`)

### 2.3 ヘッダー構成

**デスクトップ (≥768px)**
```
[ロゴ KABU TRADE]  [ホーム|ランキング|ポートフォリオ|シミュレータ|履歴]        [🔍 ⌘K] [▶ バッチ]
```
- 現在ページはアクセント下線 (`border-b-2 border-violet-600`)
- `NavLink` の `isActive` でハイライト切替

**モバイル (<768px)**
```
[☰] [KABU TRADE]                                   [🔍]
```
- `☰` タップで `Dialog` ベースのスライドインドロワー (左からスライド)
- ドロワー内にメイン 5 リンクをスタック表示
- 現在ページのみアクセント背景 (`bg-violet-50`)

### 2.4 グローバル検索 (`⌘K` / `Ctrl+K`)

- `components/search/CommandPalette.tsx` (Dialog ラッパ)
- キーボードショートカット (`useEffect` で `keydown` を購読) または 🔍 アイコンクリックで起動
- 入力欄: プレースホルダ「銘柄コード or 銘柄名」
- Enter で `/stocks/:code` に遷移（コードは `.T` を自動付与、数字のみ / `\d{4}` 判定）
- フェーズ B では銘柄コード遷移のみサポート。将来的に `/scores?q=` 等と連動可。

### 2.5 バッチ実行ボタン

- 現行 `StockRankingPage` の `alert()` + インラインボタンを廃止。
- ヘッダー右の `▶ バッチ` ボタンから `Dialog` を開き、`scoresApi.triggerBatch()` を実行。
- Dialog 内で `getBatchStatus` をポーリング (5 秒間隔、最大 30 回) して進捗表示。

## 3. ホームダッシュボード

### 3.1 レイアウト（`max-w-6xl` 内 12 カラムグリッド）

```
┌────────────────┬───────────────┬──────────────┬──────────────┐
│ 評価額 (Stat)  │ 目標進捗 Stat │ フェーズ Stat │ NISA残枠 Stat│  ← 1段目 (モバイル: 2x2)
├────────────────┴───────────┬───┴──────────────┴──────────────┤
│ スコア TOP5 (col-span-2)   │ 保有銘柄クイック                │  ← 2段目
├────────────────────────────┼──────────────────────────────────┤
│ 最新 TV シグナル            │ クイックシミュレータ            │  ← 3段目
└────────────────────────────┴──────────────────────────────────┘
```

### 3.2 カード詳細

- **評価額 Stat**: `portfolioApi.getSummary().total_value` + 前日比（将来、株価 API 統合後に有効化。現状は非表示）
- **目標進捗 Stat**: `progress_rate` + 横プログレスバー（`Progress` プリミティブ、violet-600）
- **フェーズ Stat**: `current_phase` を `Badge` 表示（積立期: sky / 成長期: violet / 安定期: emerald）
- **NISA 残枠 Stat**: `nisa_remaining` / `NISA_GROWTH_ANNUAL_LIMIT` の % 併記
- **スコア TOP5**: `scoresApi.listScores(limit=5)`。各行 `銘柄名 | スコアバー | レーティング | TV シグナル`。行全体が `Link` で `/stocks/:code` へ。
- **保有銘柄クイック**: `portfolioApi.listHoldings()` 先頭 5 件。行クリックで `/stocks/:code` (導線 B)。
- **最新 TV シグナル**: `tradingviewApi.listSignals(limit=5)`。Badge + 時刻、クリックで詳細へ。
- **クイックシミュレータ**: 月次積立 + 想定年利の 2 入力 + CTA `→ シミュレータで詳細`。入力値はクエリパラメータで `/simulator?monthly=...&rate=...` に渡す。

### 3.3 Empty States

- 保有銘柄ゼロ → 「まだ保有銘柄がありません」+ CTA `→ ポートフォリオに追加`
- スコア未計算 → 「スコアデータが未生成」+ CTA `▶ バッチを実行` (ヘッダーのバッチ Dialog を開く)
- TV シグナル無 → 「シグナルがまだありません」+ Claude 依頼文を折りたたみ表示

## 4. ページ別の見直し

### 4.1 StockRankingPage

- `PageHeader` に「銘柄スコアランキング」+ 最終更新時刻。右側 `Toolbar` に `ProfileSelector`。
- テーブルは `Table` プリミティブ化、`sticky` ヘッダー、行ホバーは `hover:bg-slate-100`。
- 各行に **クイックアクション**（ホバーで表示、icon ボタン 2 個）:
  - `★` ウォッチリスト（将来機能用、現段階では UI のみ）
  - `＋` 保有追加 → StockDetailPage の Dialog を流用（`Dialog` を `components/portfolio/AddHoldingDialog.tsx` として共通化）
- モバイル（`<md`）では `Card` リストに切替（`hidden md:block` + `md:hidden` で出し分け）:
  ```
  [銘柄名 / コード]
  [スコアバー]              [レーティング Badge]
  [ファンダ | テクニカル | TVシグナル]
  ```

### 4.2 StockDetailPage

- 上部 `PageHeader`: 銘柄コード + 名称 + セクター。右側に **「ポートフォリオに追加」ボタン**（導線 A）。
- `AddHoldingDialog` で数量 / 単価 / 購入日 / 口座種別を入力して `portfolioApi.createHolding()`。成功時は Dialog 内に成功メッセージを 2 秒表示してから自動クローズ（Toast プリミティブは今回見送り）。
- 既存 `StockInfo / ChartAnalysisPanel / AnalysisAxesPanel` を `Card` でラップし、タブ `概要 | チャート | 分析軸` に整理（Tabs プリミティブを追加）。

### 4.3 PortfolioPage

- サマリーカード群を `Stat` に統一し、`PhaseIndicator` と並列表示。
- 設定フォーム (`target_amount` 等) は `Dialog` に移動、`PageHeader` 右側 `⚙ 設定` から開く。
- 保有銘柄テーブルを `Table` プリミティブ化、**銘柄名を `Link` 化**（導線 B）。
- 追加フォームも `Dialog` 化（`＋ 保有追加`）。モバイルは `Card` リストに切替。

### 4.4 SimulatorPage

- 入力フォームを `Card` + `Input` プリミティブに統一。
- URL クエリ `?monthly=...&rate=...&pv=...&years=...` を受け取れるようにして、ホームのクイック入力から値を引き継ぐ。
- 結果カード 3 枚 (`final_value / total_contributed / total_gain`) は `Stat` 統一。
- `FutureValueChart` は SVG のまま、軸ラベルと凡例を `Badge` 化。
- 「必要年利逆算」は折りたたみ可能な補助セクションに降格。

### 4.5 AnalysisHistoryPage

- `Table` プリミティブ化、モバイルは `Card` リスト。
- 各行の `新しい→古い` ソートを維持。再計算ボタンは追加しない。

## 5. ロールアウトフェーズ

### Phase A: 基盤（独立 PR）

1. `npm install tailwindcss @tailwindcss/vite class-variance-authority clsx`
2. `vite.config.ts` / `src/index.css` / `tailwind.config.ts` セットアップ
3. Google Fonts 読み込み
4. `components/ui/` に 10 プリミティブ作成
5. サンドボックスルート `/__ui` (開発時のみ) でプリミティブを目視確認。マージ前に削除。
6. 既存ページは一切変更しない

**検証**: `npm run build` が通る / サンドボックスで全プリミティブが正しく表示される

### Phase B: AppShell + ホーム（独立 PR）

1. `AppShell` + ルート再構成
2. ヘッダー（デスクトップ / モバイル + ドロワー）
3. `CommandPalette` (`⌘K`)
4. バッチ実行 `Dialog`
5. `HomePage` を Dashboard に差し替え（必要 API 呼び出し）

**検証**: 全ルートに遷移可能 / 375px / 768px / 1280px でヘッダーが崩れない / `⌘K` が動く / バッチ実行 Dialog がポーリング表示する / Dashboard が `/portfolio/summary`, `/scores?limit=5`, `/tradingview-signals?limit=5` を表示する

### Phase C: 主要ページ刷新（独立 PR、3 コミットに分割可）

1. `StockRankingPage` の Tailwind 化 + モバイル Card リスト + クイックアクション
2. `StockDetailPage` の Tabs 化 + 「ポートフォリオに追加」Dialog
3. `PortfolioPage` の Dialog 化 + 銘柄リンク化

**検証**: 導線 A/B/C が動作 / 各ページがモバイル幅で崩れない

### Phase D: 補助ページ + 最終掃除（独立 PR）

1. `SimulatorPage` Tailwind 化 + URL クエリ対応
2. `AnalysisHistoryPage` Tailwind 化
3. 残存インライン style の全除去（grep で `style={{` を探し 0 件にする）
4. `App.css` 最小化
5. 動作確認チェックリスト実施

**検証**: `grep -r 'style={{' frontend/src | wc -l` が 0（SVG 内は例外的に許容）

## 非機能要件

- **アクセシビリティ**: Dialog は `role="dialog" aria-modal` 準拠、キーボード操作（`Esc` 閉じる、`Tab` フォーカストラップ）。`Button` には `aria-label`。
- **ダークモード**: 将来対応可能にするため Tailwind の `dark:` バリアントで色を記述しておく（Phase A で準備のみ、有効化は別タスク）。
- **パフォーマンス**: 追加依存は Tailwind + cva + clsx のみ。ダッシュボードの 3 API 呼び出しは `Promise.all` で並列。

## 編集しないファイル（保護対象）

- `backend/` 配下一切
- `frontend/src/types/`, `frontend/src/services/api/` （API 契約不変）
- `frontend/src/components/stock/StockChart.tsx`（チャート描画ロジックは別途）
- 既存 `FutureValueChart.tsx` は SVG のまま、ラッパだけ変更

## 検証チェックリスト

最終回帰（Phase D 完了時）:

- [ ] 全 6 ルートが描画 → 遷移可能
- [ ] ヘッダーのリンクが `isActive` で下線
- [ ] `⌘K` で検索 Dialog、銘柄コード入力 → 詳細へ
- [ ] ヘッダー `▶ バッチ` で Dialog 起動、進捗表示
- [ ] ホームダッシュボードの 7 カードが正しい API から取得したデータで描画
- [ ] ホームの TOP5 行 / 保有行クリック → 詳細へ（導線 B/D）
- [ ] ランキング行ホバー → クイックアクション表示、`＋` で AddHoldingDialog（導線 C）
- [ ] 詳細ページの「ポートフォリオに追加」→ Dialog → 作成成功（導線 A）
- [ ] ポートフォリオの銘柄名 Link → 詳細へ（導線 B）
- [ ] ホームクイックシミュ入力 → `/simulator?monthly=...` 遷移で値が反映
- [ ] 375px / 768px / 1280px で全ページ崩れなし
- [ ] `grep -r 'style={{' frontend/src` が SVG 以外でゼロ
- [ ] `npm run build` エラーなし
