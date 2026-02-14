# Requirements Document

## Project Description (Input)
kabuステーションAPIを使用した外部データ取得（銘柄情報、株価履歴、リアルタイム価格）を、Kabu Trade のバックエンドから呼び出せるようにしたいです。ローカル環境（kabuステーションが稼働している環境）での利用を前提にし、既存の「外部データ取得の差し替え（実サービス/モック）」の方針に従います。

## Introduction
本仕様は、Kabu Trade が株価データの一次取得元として **kabuステーションAPI** を利用する際の「外部API呼び出し」に関する要件を定義します。  
対象はバックエンドの External/Provider 層で、既存の画面（銘柄検索/銘柄詳細/株価チャート）および評価ロジックが必要とするデータを、安定して取得・正規化・エラー分類できることを目的とします。

## Requirements

### Requirement 1: 接続設定と認証（トークン取得・更新）
**Objective:** As a 開発者, I want kabuステーションAPIの接続先と認証情報を安全に設定できる, so that ローカル環境差や運用変更に対応できる

#### Acceptance Criteria
1.1 The Kabu Station Integration shall 接続先（ベースURL）と認証に必要な値（APIパスワード等）を環境変数（設定）から読み取れる
1.2 When 認証トークンが未取得の状態でAPI呼び出しが必要になった場合, the Kabu Station Integration shall トークン取得処理を実行してからリクエストを行う
1.3 If 認証に失敗した場合, the Kabu Station Integration shall 認証失敗として分類し、上位層がユーザー/運用者に判別可能なエラーとして扱える
1.4 When 認証トークンが無効（例: 401）になった場合, the Kabu Station Integration shall トークンを再取得し、同一リクエストを**1回だけ**再試行する
1.5 The Kabu Station Integration shall 認証情報（トークン/パスワード等）をログや例外メッセージに出力しない

### Requirement 2: 銘柄情報（コード→名称・現在値）の取得
**Objective:** As a 利用者, I want 銘柄コードから銘柄名と現在値を取得できる, so that 銘柄詳細の表示と評価の起点にできる

#### Acceptance Criteria
2.1 When 銘柄情報の取得が要求された場合, the Kabu Station Integration shall 銘柄名と現在値を取得し、内部の `StockInfo` 相当のデータに正規化して返す
2.2 If 指定した銘柄コードが存在しない場合, the Kabu Station Integration shall 「銘柄が存在しない」ことを示すエラーとして扱える
2.3 The Kabu Station Integration shall 市場（取引所）指定を扱える（デフォルトは東証とし、将来の拡張で他市場へ対応できる）

### Requirement 3: 株価履歴（日足OHLCV）の取得
**Objective:** As a 利用者, I want 期間指定で株価履歴（OHLCV）を取得できる, so that チャート表示やテクニカル指標計算に利用できる

#### Acceptance Criteria
3.1 When 期間（例: 1m/3m/6m/1y）または開始日・終了日が指定された場合, the Kabu Station Integration shall 指定範囲に対応する日足OHLCVを取得して返す
3.2 The Kabu Station Integration shall 取得した株価履歴を日付昇順に整列して返す
3.3 If 取得範囲が不正（例: 終了日 < 開始日、期間指定と日付指定の矛盾）である場合, the Kabu Station Integration shall 入力不正として扱える
3.4 If 外部API応答が不完全（必須フィールド欠落など）である場合, the Kabu Station Integration shall 外部APIの不正応答として扱える
3.5 The Kabu Station Integration shall `open/high/low/close` と `volume` をそれぞれ数値として正規化し、桁や型の揺れ（文字列/数値）に耐えられる

### Requirement 4: リアルタイム価格の取得と市場状態
**Objective:** As a 利用者, I want リアルタイム価格を取得できる, so that 直近の状況を素早く把握できる

#### Acceptance Criteria
4.1 When リアルタイム価格の取得が要求された場合, the Kabu Station Integration shall 現在値を取得して返す
4.2 If 市場が休場中であることが判明した場合, the Kabu Station Integration shall 「休場中」を表すエラーとして扱える
4.3 If 現在値が取得できない（例: 0や欠落）場合, the Kabu Station Integration shall 「銘柄が存在しない」または「取得不能」を区別可能な形で扱える

### Requirement 5: エラー分類・タイムアウト・レート制限
**Objective:** As a 運用者, I want 外部API起因の失敗を適切に分類して扱える, so that 障害時に原因切り分けと復旧判断ができる

#### Acceptance Criteria
5.1 The Kabu Station Integration shall 外部API呼び出し失敗を少なくとも「認証失敗」「レート制限」「接続失敗/タイムアウト」「外部APIエラー（4xx/5xx）」に分類できる
5.2 If レート制限（例: HTTP 429）が発生した場合, the Kabu Station Integration shall レート制限として扱える
5.3 The Kabu Station Integration shall 外部API呼び出しにタイムアウトを設定し、ハングして処理をブロックし続けない
5.4 The Kabu Station Integration shall 失敗時に再試行を無制限に行わない（認証リトライ以外は、上位層が制御できる）

### Requirement 6: 代替（モック/他プロバイダー）への切替と可観測性
**Objective:** As a 開発者, I want kabuステーションが利用できない環境でも開発/検証を継続できる, so that 実データ依存で開発が止まらない

#### Acceptance Criteria
6.1 Where kabuステーションAPIが利用できない環境である場合, the system shall モックプロバイダー等の代替データ取得手段を選択できる（プロダクト方針の「差し替え」前提に従う）
6.2 The Kabu Station Integration shall 失敗時にデバッグ可能なログ（リクエスト種別、銘柄コード、HTTPステータス等）を出力できるが、機密情報は含めない

