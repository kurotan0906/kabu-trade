# 保有銘柄編集機能 設計書

- **作成日**: 2026-04-19
- **対象機能**: ポートフォリオ画面から保有銘柄のデータを編集できるようにする
- **ステータス**: 設計承認済み

## 背景と目的

現在、ポートフォリオ画面 (`/portfolio`) では保有銘柄の「追加」「削除」は可能だが、「編集」UIが存在しない。株数の増減や取得単価の訂正、口座区分の変更などを行うためには一度削除して再追加する必要があり UX が悪い。

本機能により、保有銘柄の各項目をモーダルダイアログから編集できるようにする。

## スコープ

### 対象
- フロントエンド `PortfolioPage` に編集UIを追加
- 既存の `AddHoldingDialog` を汎用化して編集モードに対応

### 対象外
- バックエンドAPI変更（`PUT /portfolio/holdings/{id}` と `HoldingUpdate` スキーマは既存のまま使用）
- 銘柄コード (`symbol`) の変更（別銘柄は削除＆再追加で対応する既存方針を踏襲）
- 編集履歴の保存・監査ログ
- 取引 (Trade) からの保有銘柄自動更新

## 既存資産（変更なしで利用）

| レイヤ | 資産 | 用途 |
|---|---|---|
| Backend API | `PUT /api/v1/portfolio/holdings/{id}` | 更新エンドポイント |
| Backend Schema | `HoldingUpdate` (`name / quantity / avg_price / purchase_date / account_type`) | 更新ペイロード |
| Backend Service | `portfolio_service.update_holding()` | DB更新ロジック |
| Frontend API | `portfolioApi.updateHolding(id, patch)` | 更新API呼び出し |

## UI/UX 設計

### 編集UIパターン
**モーダルダイアログ方式**（追加UIと同等）。保有銘柄テーブルの各行に「編集」ボタンを追加し、クリックでダイアログを開く。

### 編集可能な項目

| 項目 | 編集可否 | 備考 |
|---|---|---|
| `symbol`（銘柄コード） | ❌ 読み取り専用 | 別銘柄は削除＆再追加 |
| `name`（銘柄名） | ✅ |  |
| `quantity`（株数） | ✅ | `> 0` バリデーション |
| `avg_price`（取得単価） | ✅ | `> 0` バリデーション |
| `purchase_date`（取得日） | ✅ | 任意項目 |
| `account_type`（口座区分） | ✅ | `general / nisa_growth / nisa_tsumitate` |

### 操作列レイアウト

```
| 銘柄 | 口座 | 株数 | 取得単価 | 取得額 | [編集] [削除] |
```

「編集」は `variant="ghost"` / `size="sm"` で削除ボタンと同じスタイル。

## コンポーネント構成

### `AddHoldingDialog.tsx` → `HoldingDialog.tsx` に汎用化

既存の `AddHoldingDialog` を改修して追加・編集の両モードに対応させる。

**新しい Props:**

```ts
interface Props {
  open: boolean;
  onClose: () => void;
  mode: 'create' | 'edit';
  /** create モード時の初期 symbol（既存の `symbol` prop 相当） */
  defaultSymbol?: string;
  /** create モード時の初期 name */
  defaultName?: string | null;
  /** edit モード時の編集対象 holding */
  holding?: Holding;
  onSaved?: () => void;
}
```

**モード別の挙動:**

| 挙動 | `create` | `edit` |
|---|---|---|
| ダイアログタイトル | 保有銘柄を追加 | 保有銘柄を編集 |
| `symbol` フィールド | 入力可 | 読み取り専用 (`disabled`) |
| 送信ボタン | 追加する | 保存 |
| 成功メッセージ | 追加しました。 | 保存しました。 |
| 送信時API | `portfolioApi.createHolding(draft)` | `portfolioApi.updateHolding(holding.id, patch)` |
| 初期値 | defaults（空） | `holding` からコピー |

**ファイル名:** `frontend/src/components/portfolio/HoldingDialog.tsx`
（`AddHoldingDialog.tsx` を削除して新規作成。既存の import 箇所を更新）

### `PortfolioPage.tsx` の変更点

1. `editingHolding: Holding | null` state を追加
2. テーブル行の操作列に「編集」ボタンを追加
3. 「編集」クリック時：`setEditingHolding(h)` + ダイアログオープン
4. `HoldingDialog` を `mode="edit"` で表示し、保存成功時に `refresh()`
5. 既存の `AddHoldingDialog` 呼び出しを `HoldingDialog mode="create"` に置換

### 影響を受けるその他の import 箇所

`AddHoldingDialog` を import している箇所（いずれも `mode="create"` に置換）：

- `frontend/src/pages/PortfolioPage.tsx`
- `frontend/src/pages/StockDetailPage.tsx`
- `frontend/src/pages/StockRankingPage.tsx`

## データフロー

```
PortfolioPage
  ├─ [編集]クリック(h)
  │   → setEditingHolding(h)
  │   → setEditOpen(true)
  │
  ├─ <HoldingDialog mode="edit" holding={editingHolding} ...>
  │   └─ 保存ボタン
  │       → portfolioApi.updateHolding(h.id, patch)
  │       → 成功表示（0.6秒）
  │       → onSaved()
  │       → onClose()
  │
  └─ onSaved = refresh()
       → portfolioApi.listHoldings() + getSummary() を再取得
```

## バリデーション

- `quantity > 0`
- `avg_price > 0`
- `symbol` は編集不可のため常に有効
- 失敗時：赤枠のエラーメッセージ（既存 `AddHoldingDialog` のパターンを踏襲）

## エラーハンドリング

| ケース | 挙動 |
|---|---|
| バリデーションNG | ダイアログ内に赤枠メッセージ表示、送信ブロック |
| API 4xx/5xx（404含む） | エラー文言を赤枠で表示、ダイアログは開いたまま（既存 `AddHoldingDialog` のパターンを踏襲） |

## テスト方針

### 手動テスト（必須）
1. `/portfolio` を開く
2. 保有銘柄の「編集」ボタンをクリック
3. 各項目（name / quantity / avg_price / purchase_date / account_type）を変更して保存
4. 一覧・サマリが更新されていることを確認
5. `symbol` が編集不可であることを確認
6. 株数 0 / 取得単価 0 でバリデーションエラーになることを確認
7. 追加ダイアログ（create モード）が従来通り動くことを確認
8. 削除ボタンが従来通り動くことを確認

### 自動テスト
Portfolio 周りの既存自動テストは存在しないため、本タスクでは追加しない（現状の方針に合わせる）。将来フロントエンドテスト基盤を導入する際に合わせて整備する。

## リスク・留意点

- **既存ダイアログのリネーム影響**：`AddHoldingDialog` を import している箇所を全て更新する必要あり。TypeScript のコンパイルエラーで検知可能。
- **楽観的更新はしない**：現状 `refresh()` で完全再取得しているため、一時的にUIがちらつく可能性はあるが、データ整合性を優先する。

## 成果物

- `frontend/src/components/portfolio/HoldingDialog.tsx`（`AddHoldingDialog.tsx` を置換）
- `frontend/src/pages/PortfolioPage.tsx`（編集UI追加）
- その他 `AddHoldingDialog` を import している箇所の更新
