# 調査メモ（api-selection）

_created_at: 2026-01-24T06:10:30Z_

本ファイルは、`design.md` の意思決定の裏付けとなる調査ログです。設計レビューで必要な結論は `design.md` 側に要約し、ここには根拠と比較の素材を残します。

## 1. 既存コードの拡張ポイント（現状）

- **外部データ取得の抽象化**: `StockDataProvider`（`backend/app/external/providers/base.py`）
  - `get_stock_info(code)`
  - `get_stock_prices(code, start_date, end_date, period)`
  - `get_realtime_price(code)`
- **既存実装**
  - `KabuStationProvider`: kabuステーションAPI（ローカルホスト経由）を利用
  - `MockProvider`: 開発/検証用のモック

## 2. 候補API（一次情報リンク）

> 候補の網羅は目的ではないため、代表的なカテゴリの入口だけを置く。採用判断は `design.md` の評価軸に従って行う。

### 2.1 JPX公式: J-Quants API（日本株）

- **概要**: JPX（日本取引所グループ）によるデータAPI配信
- **公式**: [J-Quants API](https://jpx-jquants.com/?lang=ja)
- **仕様**: [API仕様（日本語）](https://jpx.gitbook.io/j-quants-ja/api-reference)
- **注意点（示唆）**:
  - 無料プランは「直近12週間を除く2年分」など、遅延/期間制約がある
  - 無料プランのAPIコール制限が小さい場合がある（例: 1分あたり少数回）
  - 「東京証券取引所に上場する銘柄」を対象とする旨の記載があり、プライム市場要件（`1.2`）との整合は要確認（銘柄一覧で市場区分を扱えるか等）

### 2.2 証券会社系: kabuステーションAPI（既存候補）

- **公式**: [kabuステーションAPI](https://kabu.com/item/kabustation_api/default.html)
- **OpenAPI/仕様（参考）**: [kabusapi reference](https://kabucom.github.io/kabusapi/ptal/index.html)
- **レート制限/仕様の要点（参考）**
  - トークン発行→`X-API-KEY` ヘッダで利用
  - 強制ログアウト等によりトークンの扱いに注意が必要

### 2.3 データベンダー系: Twelve Data（JPX）

- **公式**: [Twelve Data](https://twelvedata.com/)
- **JPXエクスチェンジ情報**: [Tokyo Stock Exchange (JPX)](https://twelvedata.com/exchanges/xjpx)
- **注意点（示唆）**:
  - JPXは有償プラン（Pro等）限定の可能性が高く、「無料で開始できる」（`2.3`）を満たさないリスクがある
  - 遅延（例: 20分遅延など）が明記されることがあるため、要件との整合確認が必要

### 2.4 無料データ系: Stooq（参考）

- **公式**: [Stooq Free Market Data](https://stooq.com/db/)
- **利用例（pandas-datareader）**: [pandas-datareader Stooq reader](https://pydata.github.io/pandas-datareader/readers/stooq.html)
- **注意点（示唆）**:
  - 利用規約で再配布が制限される旨が明記される場合があるため、UI表示やキャッシュ運用との整合確認が必須（`2.4`）
  - 安定性・更新頻度などの確認が必要

## 3. 追加で確認すべき論点（チェックリスト）

- **利用規約/再配布**: UIでの表示・キャッシュ・再配布の可否、商用/個人の範囲
- **遅延/更新頻度**: リアルタイム要件の有無、EODで足りるか
- **レート制限**: 画面操作やバッチ実行時のピークで破綻しないか
- **データ範囲**: 日本株（JPX）対応、特にプライム市場のカバレッジ、銘柄マスタ、財務指標の有無
- **コスト**: 初期段階で無料で開始できるか（無料プラン/トライアル）、無料枠の制約、スケール時の月額見積もり
- **運用**: 認証の更新、障害時のフォールバック、監視可能性

