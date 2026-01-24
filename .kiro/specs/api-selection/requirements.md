# Requirements Document

## Project Description (Input)
apiの選定を行いたいです

## Introduction
本仕様は、株取引支援システム（Kabu Trade）が利用する**外部株式データAPI**（銘柄情報、株価、財務など）の候補を洗い出し、評価軸に基づいて比較し、採用APIと導入方針を合意可能な形で決定するための要件を定義します。  
本プロダクトは「外部データ取得の差し替え（実サービス/モック）」を前提としているため、API選定の成果は将来の差し替え・拡張にも耐える形で残すことを目的とします。

## Requirements

### Requirement 1: 候補APIの洗い出しとスコープ定義
**Objective:** As a 開発者, I want 候補APIと評価対象のスコープを明確化できる, so that 以降の比較と意思決定がブレなく進められる

#### Acceptance Criteria
1.1 The API Selection Process shall 評価対象となるデータ種別（例: 銘柄基本情報、株価時系列、財務指標）と利用目的（例: 画面表示、分析入力）を文書化する
1.2 The API Selection Process shall 初期段階の必須マーケット要件として「日本のプライム市場に対応していること」を明文化する
1.3 The API Selection Process shall 候補APIの一覧を作成し、各候補に対して少なくとも「提供元/名称、対応データ種別、認証方式、利用規約の要点、料金体系の要点」を記録する
1.4 The API Selection Process shall 初期候補として、少なくとも「kabuステーション系API（実データ）」と「モック相当（開発/検証用）」の位置づけを明示する（候補の網羅は要求しない）
1.5 The API Selection Process shall 「直近データの欠落（例: 直近12週間が取得不可）」を初期段階の重要リスクとして扱い、欠落期間・影響・回避策（別API併用/有償移行/スコープ変更）を候補ごとに記録する

### Requirement 2: 評価軸（比較基準）と合否条件
**Objective:** As a プロダクトオーナー, I want 候補APIを同一基準で評価できる, so that 採用判断を説明可能にできる

#### Acceptance Criteria
2.1 The API Selection Process shall 評価軸を定義し、少なくとも「データ範囲/品質、遅延/更新頻度、可用性、認証/認可、レート制限、コスト、利用規約/再配布可否、実装容易性/SDK有無、運用負荷」を含める
2.2 The API Selection Process shall 各評価軸に対して、判定方法（確認手段）と合否条件（最低要件）を明文化する
2.3 The API Selection Process shall 初期段階のコスト要件として「無料で気軽に登録して利用開始できる（無料プランまたは無料トライアルでPoCが可能）」の合否条件を定義する
2.4 If 利用規約上の禁止事項（例: 再配布不可、用途制限）がプロダクト要件と矛盾する場合, the API Selection Process shall 当該候補を「不採用」または「要スコープ変更」として扱い、その理由を記録する
2.5 The API Selection Process shall 評価結果を第三者が追試できるように、参照した根拠（公式ドキュメント名/版、問い合わせ結果、確認日）を記録する
2.6 The API Selection Process shall データ鮮度の最低要件（例: 「直近N営業日/直近Xヶ月が取得できること」）を合否条件として定義し、満たさない候補は初期段階の採用対象から除外する
2.7 The API Selection Process shall コーポレートアクション（分割/併合/配当等）による調整の有無と、調整済み/未調整データの提供方針を評価項目として記録する

### Requirement 3: 技術的成立性の確認（PoCレベルの検証）
**Objective:** As a 開発者, I want 候補APIがシステムに組み込めることを事前確認できる, so that 選定後の手戻りを減らせる

#### Acceptance Criteria
3.1 The API Selection Process shall 候補APIごとに「必要な認証情報の種類」と「ローカル開発環境での疎通可否」を確認し、結果を記録する
3.2 When 候補APIが銘柄検索/銘柄詳細/株価取得のいずれかを提供しない場合, the API Selection Process shall 代替手段（別API併用、機能スコープ変更）を提示し、影響範囲を記録する
3.3 The API Selection Process shall 既存の「外部データ取得の差し替え」前提（実サービス/モック）と矛盾しない導入形態であることを確認し、制約がある場合は明文化する
3.4 If 候補APIが「無料開始」の条件を満たすが「直近データ鮮度」の条件を満たさない場合, the API Selection Process shall 初期段階のフォールバック構成（例: 直近のみ別API、段階的に有償移行）を必須の検討項目として記録する

### Requirement 4: 選定結果の決定と成果物の作成
**Objective:** As a チーム, I want 選定結果を合意できる形で残せる, so that 将来の運用・変更時に判断根拠を追える

#### Acceptance Criteria
4.1 The API Selection Process shall 採用API（単一または複数）と採用理由、および不採用候補の理由を一覧化して記録する
4.2 The API Selection Process shall 主要なリスク（例: 料金変動、レート制限、仕様変更、提供終了）と対策（例: モック維持、代替候補、監視）を記録する
4.3 The API Selection Process shall 導入に必要な前提（例: 契約、アカウント作成、取得できる環境変数の種類）を整理し、機密情報を本文に含めない
4.4 The API Selection Process shall 初心者ユーザーが誤解しやすい制約（例: データ遅延、直近欠落、調整の有無）を「UI/説明で明示すべき事項」として抽出し、採用時の付帯要件として記録する

### Requirement 5: 更新運用（ドリフト防止）
**Objective:** As a 運用者, I want API選定情報を最新に保てる, so that 実装や運用が現実と乖離しない

#### Acceptance Criteria
5.1 When 採用APIの仕様/価格/利用規約に変更が検知された場合, the API Selection Process shall 影響評価を行い、必要なら評価表と選定結果を更新する
5.2 The API Selection Process shall 更新履歴（更新日、変更点、判断への影響）を記録できる
5.3 When データ鮮度/期間/遅延の仕様が変更された場合, the API Selection Process shall 直ちに「致命条件（データ欠落/遅延）」の再評価を行い、必要なら採用方針とフォールバック構成を更新する


