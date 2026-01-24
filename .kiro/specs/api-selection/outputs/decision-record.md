# DecisionRecord

- decided_at: 2026-01-24

## 採用
- 三菱UFJ eスマート証券 / kabuステーションAPI

## 採用理由
- ゲート条件（プライム市場対応/無料開始/鮮度）を満たす候補を採用する

## 不採用
- Twelve Data / Tokyo Stock Exchange (XJPX)
- RapidAPI / Yahu Financials (Yahoo Finance API on RapidAPI)

## 不採用理由
- ゲート条件を満たさない、または根拠不足のため保留/不採用

## 導入前提（機密は含めない）
- JQUANTS_ID_TOKEN を設定する（値は記録しない）
- 鮮度（遅延/直近欠落）と呼び出し制限が要件に許容範囲か一次情報で確認する

## UI/説明で明示すべき事項
- （未記録）

