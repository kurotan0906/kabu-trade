# TradingView 利用規約レビュー（TV Screener 一括取得 Phase 2 判断材料）

**Date:** 2026-04-18（レビュー実施日）／2026-04-19（本ドキュメント作成）
**Scope:** `tradingview-screener` PyPI パッケージ経由でサーバー定期バッチから TradingView のスクリーナー API を叩く行為の規約適合性
**関連:**
- `docs/superpowers/logs/2026-04-18-tv-screener-bulk-phase1.md`
- `docs/superpowers/logs/2026-04-18-tv-screener-bulk-phase2.md`

> **ユーザーへのお願い:** 本ドキュメントは一次情報（TradingView 公式 Policies ページ）から抜粋した引用と、それに対する自分たちの解釈を記録したものです。**法的助言ではありません**。最終判断の前に必ずユーザー自身で原文リンクを開いて再確認してください。

---

## 1. 参照した一次情報

- **URL:** https://www.tradingview.com/policies/
- **参照日:** 2026-04-18
- **ページ上の最終更新日:** 明示されていない
- **使用パッケージ:** `tradingview-screener` v3.1.x（PyPI, MIT License, 2026-02-26 リリース）
  - リポジトリ: https://github.com/shner-elmo/TradingView-Screener
  - 動作: TradingView の非公開スクリーナーエンドポイント `https://scanner.tradingview.com/japan/scan` に POST
  - スクレイピングではなく **公式 API 呼び出し**（README にも記載）

## 2. 関連規約条項（英語原文抜粋）

TradingView の利用規約（Section 3 相当）から、本件に関連する文言を引用する。

> **(a) 非表示用途の全面禁止**
> "prohibited uses include, but are not limited to, any form of automated trading, automated order generation, price referencing, order verification, **algorithmic decision-making**"
>
> "any **machine-driven processes** that do not involve the direct, human-readable display of such data"

> **(b) 第三者ツールによる迂回も禁止**
> "expressly forbid direct non-display usage by our users, as well as the development, offering, or utilization of any **third-party products, tools, or services**"

> **(c) 商用利用の不許可**
> "we do not permit commercial usage of any of our services or APIs"

> **(d) 再配布・サブライセンス禁止**
> "forbid the sublicensing, assigning, transferring, selling, loaning, or any distribution of TradingView content"

## 3. 我々の用途への当てはめ

| 条項 | 本システムの用途 | 判定 |
|---|---|---|
| (a) machine-driven processes / algorithmic decision-making | Cloud Run Job が日次で screener API を叩き、スコア算出・DB 保存 | **抵触する可能性が高い**（人が直接見る用途ではなく、スクリプトが集計する過程） |
| (b) 第三者ツール (`tradingview-screener`) | PyPI 経由で導入 | **抵触する可能性が高い**（規約はツール経由も除外していない） |
| (c) 商用利用 | 個人の学習・資産管理用途。広告なし、非公開、ユーザー本人のみ利用 | 厳密解釈では「commercial=対価を得ている」と取ればクリア。だが TV は明示的に非営利利用の例外を認めていない |
| (d) 再配布 | スコアを第三者に配布・販売していない | クリア |

**結論**: 厳密に読む限り (a)(b) は灰色〜抵触。

## 4. それでも Phase 2 に進めた判断根拠

2026-04-18 にユーザーと合意の上で採用した「Option A: 予定どおり Phase 2 へ進む」の理由を、後日検証できるよう明文化する。

1. **TradingView への負荷は refactor 前後で減少する方向**
   - 現行 hybrid モードは `tradingview-ta` を **per-symbol** で呼び出し、日次で約 **4,000 コール / 日** を TV に投げていた
   - screener モードに切り替えると **1 コール / 日** に集約される
   - 規約への露出量はむしろ 1/4,000 に圧縮される

2. **hybrid モードも同じ規約リスクに既に晒されていた**
   - hybrid で使っている `tradingview-ta` も (a)(b) に同様に抵触する可能性がある
   - Phase 2 は規約リスクを **新規に発生させる** ものではなく、**既存のリスクを置き換えつつ圧縮** するものという整理

3. **個人利用・少量アクセス**
   - CAPTCHA / rate limit に引っかかった事例は今のところ無し
   - 1 日 1 回のスクリーナー呼び出しは、他の TradingView ユーザーが手動でスクリーナー画面を数十回開くのと負荷的には近い

4. **撤退コストが低い**
   - `SCORING_DATA_SOURCE` env var で即座に `yfinance` に戻せる（Service / Job 両方）
   - コードの hybrid / tv / yfinance パスは Phase 3 で削除予定だが、それまでは温存

## 5. 残リスクと監視・撤退基準

- **想定シナリオ:** TV から CAPTCHA 要求 / IP ブロック / アカウント警告が来る
- **監視:**
  - Cloud Logging で `tv_screener snapshot` ログが継続的に `total=3700+` を返すかを毎日確認
  - バッチ失敗率（`失敗=N / total=3745`）が急増したら検知
- **即時撤退手順:**
  ```
  gcloud run services update kabu-trade-backend --region=us-central1 \
    --update-env-vars SCORING_DATA_SOURCE=yfinance
  gcloud run jobs update kabu-trade-batch --region=us-central1 \
    --update-env-vars SCORING_DATA_SOURCE=yfinance
  ```
- **中長期オプション（Phase 3 後の追加検討）:**
  - TradingView **有償プラン**（Premium / Commercial 契約）への切替で明示ライセンスを取得
  - もしくは `tradingview-ta` / screener から完全離脱し、yfinance / J-Quants / 楽天証券 API 等に一本化

## 6. ユーザーが追加検証すべき項目

- [ ] 上記引用が現行の https://www.tradingview.com/policies/ と一致するか原文確認
- [ ] 「個人の資産管理目的の非公開ダッシュボード」が non-display の例外として許容されるか、TV サポートに問い合わせる価値があるか判断
- [ ] 商用化・第三者提供を検討する段階になったら、必ずライセンスを確認
- [ ] `tradingview-screener` パッケージの README / Issue で最新のコンプラ注意書きが追加されていないか定期チェック

---

## 参考リンク

- [TradingView Policies](https://www.tradingview.com/policies/)
- [tradingview-screener (PyPI)](https://pypi.org/project/tradingview-screener/)
- [shner-elmo/TradingView-Screener (GitHub)](https://github.com/shner-elmo/TradingView-Screener)
