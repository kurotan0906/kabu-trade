# セットアップ手順

## 前提条件

- Python 3.11以上
- Node.js 18以上
- Docker & Docker Compose
- kabuステーション（SBI証券）がインストールされ、APIが有効になっていること

## 1. リポジトリのクローン

```bash
git clone https://github.com/kurotan0906/kabu-trade.git
cd kabu-trade
```

## 2. Docker Composeで一括起動（推奨）

すべてのサービスをDockerで統一管理します。環境の一貫性が保たれ、AWSへの移行も容易です。

### 2.1 環境変数の設定

`backend/.env`ファイルを作成：

```bash
# backend/.envファイルを手動で作成
cat > backend/.env << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/kabu_trade
REDIS_URL=redis://redis:6379/0

# kabuステーションAPI
KABU_STATION_API_TOKEN=  # 空欄でOK（自動取得）
KABU_STATION_PASSWORD=your_api_password_here
KABU_STATION_API_URL=https://localhost:18080/kabusapi

# Provider settings
USE_MOCK_PROVIDER=true  # モックプロバイダーを使用する場合はtrue（開発・テスト用）

# Application
APP_NAME=kabu-trade
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:5173
EOF
```

**重要**: kabuステーションAPIが準備できていない場合は、`USE_MOCK_PROVIDER=true`に設定してください。

### 2.2 すべてのサービスを起動

```bash
# すべてのサービス（PostgreSQL、Redis、バックエンド、フロントエンド）を起動
docker compose up --build

# バックグラウンドで起動する場合
docker compose up -d --build
```

### 2.3 データベースマイグレーション

```bash
# バックエンドコンテナでマイグレーションを実行
docker compose exec backend alembic upgrade head
```

### 2.4 アクセス

- **フロントエンド**: http://localhost:5173
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

### 2.5 ログ確認

```bash
# すべてのサービスのログを確認
docker compose logs -f

# 特定のサービスのログを確認
docker compose logs -f backend
docker compose logs -f frontend
```

### 2.6 停止

```bash
# すべてのサービスを停止
docker compose down

# ボリュームも削除する場合（データベースのデータも削除されます）
docker compose down -v
```

## 3. ローカル環境で起動（オプション）

Dockerを使わず、ローカル環境で直接起動する場合：

### 3.1 バックエンドのセットアップ

#### 3.1.1 仮想環境の作成

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3.1.2 依存関係のインストール

```bash
pip install -r requirements.txt
```

#### 3.1.3 環境変数の設定

`backend/.env`ファイルを作成（上記2.1を参照）

#### 3.1.4 データベースの起動

```bash
cd ..
docker compose up -d postgres redis
```

#### 3.1.5 データベースマイグレーション

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

#### 3.1.6 バックエンドの起動

```bash
uvicorn app.main:app --reload
```

バックエンドAPIは http://localhost:8000 で起動します。

### 3.2 フロントエンドのセットアップ

#### 3.2.1 依存関係のインストール

```bash
cd frontend
npm install
```

#### 3.2.2 フロントエンドの起動

```bash
npm run dev
```

フロントエンドは http://localhost:5173 で起動します。

## 4. Docker Composeの利点

### 4.1 環境の一貫性

- 開発環境と本番環境で同じ構成
- チームメンバー間で環境差がない
- システムライブラリも含めて管理

### 4.2 AWSへの移行が容易

- ECS/Fargateへの移行が簡単
- コンテナイメージをそのまま使用可能
- 環境変数で設定を切り替え

### 4.3 セットアップの簡素化

- Dockerだけで起動可能
- Python/Node.jsの環境構築が不要
- 依存関係の管理が簡単

## 5. kabuステーションAPIの設定

1. SBI証券のメンバーズサイトにログイン
2. kabuステーションを起動
3. APIシステム設定で「APIを利用する」にチェック
4. APIパスワードを設定
5. `.env`ファイルの`KABU_STATION_PASSWORD`に設定したパスワードを入力

## 6. 動作確認

1. フロントエンド（http://localhost:5173）にアクセス
2. 銘柄コード（例: 7203）を入力して検索
3. 銘柄情報とチャートが表示されることを確認

## トラブルシューティング

### macOS (Apple Silicon) での仮想環境作成エラー

**問題**: `python -m venv venv` や `ensurepip` が `Operation not permitted` エラーで失敗する

**原因**: macOS の保護機能により、ホームディレクトリ配下（`~/src` など）で `ensurepip` が実行できない場合がある

**解決方法**: 仮想環境を `/opt/venvs/` 配下に作成し、プロジェクトからシンボリックリンクを張る

```bash
# 1. /opt/venvs ディレクトリを作成（初回のみ、sudo が必要な場合あり）
sudo mkdir -p /opt/venvs

# 2. 仮想環境を /opt/venvs 配下に作成
python3.11 -m venv /opt/venvs/kabu-trade

# 3. プロジェクトの backend/venv をシンボリックリンクに置き換え
cd backend
rm -rf venv  # 既存の venv がある場合
ln -s /opt/venvs/kabu-trade venv

# 4. 仮想環境を有効化
source venv/bin/activate
# または
source ~/src/kabu-trade/backend/venv/bin/activate
```

**確認方法**:
```bash
# 仮想環境が正しく有効化されているか確認
which python
# 出力例: /opt/venvs/kabu-trade/bin/python

which pip
# 出力例: /opt/venvs/kabu-trade/bin/pip
```

### npm キャッシュの権限エラー

**問題**: `npm install` で `EPERM` エラーが発生し、キャッシュフォルダにアクセスできない

**原因**: macOS の保護機能により、ホームディレクトリ配下（`~/.npm`）で権限問題が発生する場合がある。過去のnpmバージョンの不具合でroot所有のファイルが残っている可能性がある。

**解決方法**: npmキャッシュを `/opt/npm-cache` 配下に配置する

```bash
# 1. /opt/npm-cache ディレクトリを作成（初回のみ、sudo が必要）
sudo mkdir -p /opt/npm-cache
sudo chown -R $(whoami):$(id -gn) /opt/npm-cache

# 2. 既存の.npmフォルダを削除（問題のあるキャッシュをクリア）
sudo rm -rf ~/.npm

# 3. frontend/.npmrc ファイルを作成（既に作成済みの場合はスキップ）
cd frontend
echo "cache=/opt/npm-cache" > .npmrc

# 4. 依存関係をインストール
npm install
```

**確認方法**:
```bash
# npmキャッシュの場所を確認
npm config get cache
# 出力例: /opt/npm-cache

# .npmrcファイルの内容を確認
cat frontend/.npmrc
# 出力例: cache=/opt/npm-cache
```

### pandas-ta のインストールエラー

**問題**: `pip install -r requirements.txt` で `pandas-ta==0.3.14b0` が PyPI から取得できず失敗する

**原因**: Python 3.11 環境では pandas-ta の該当バージョンが PyPI に存在しない、または不安定

**解決方法**: `requirements.txt` で SourceForge ミラーから直接インストールする形式に変更

`backend/requirements.txt` に以下の行を記載:
```
pandas-ta @ https://downloads.sourceforge.net/project/pandas-ta.mirror/0.3.14/PandasTA-v0.3.14b%20source%20code.tar.gz
```

**注意**: pandas-ta 0.3.14b0 をインポート時に以下の警告が表示される場合があります（エラーではない）:
```
UserWarning: pkg_resources is deprecated ... slated for removal as early as 2025-11-30
```
これは pandas-ta が内部で `pkg_resources` を使用しているためです。現時点では動作に影響はありません。

**確認方法**:
```bash
python - << 'EOF'
import pandas_ta as ta
print("pandas-ta OK:", ta.__version__)
EOF
# 出力例: pandas-ta OK: 0.3.14b0
```

### データベース接続エラー

- PostgreSQLが起動しているか確認: `docker-compose ps`
- 接続情報が正しいか確認: `.env`ファイルの`DATABASE_URL`

### Redis接続エラー

- Redisが起動しているか確認: `docker-compose ps`
- 接続情報が正しいか確認: `.env`ファイルの`REDIS_URL`

### kabuステーションAPI接続エラー

- kabuステーションが起動しているか確認
- APIが有効になっているか確認
- パスワードが正しいか確認
- ファイアウォールでポート18080がブロックされていないか確認

## 環境情報（2026-01-12時点）

### 動作確認済み環境

- **OS**: macOS (Apple Silicon)
- **Python**: 3.11.14
- **pip**: 25.3
- **仮想環境**: `/opt/venvs/kabu-trade`（macOS の保護制限回避のため）
- **シンボリックリンク**: `backend/venv` → `/opt/venvs/kabu-trade`

### 依存関係のインストール状況

- ✅ すべての依存関係が正常にインストール済み
- ✅ pandas-ta 0.3.14b0 が SourceForge ミラーから正常にインストール済み
- ✅ 動作確認済み（`import pandas_ta as ta` が成功）

### 次のステップ

依存関係のインストールが完了したため、以降は以下に進むことができます：

1. アプリ起動（uvicorn/FastAPI）
2. データベース接続設定
3. 指標計算の実装
