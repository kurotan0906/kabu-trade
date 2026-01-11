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

## 2. バックエンドのセットアップ

### 2.1 仮想環境の作成

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2.2 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2.3 環境変数の設定

`.env`ファイルを作成：

```bash
cp .env.example .env
# .envファイルを編集
```

`.env`ファイルの内容：

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kabu_trade
REDIS_URL=redis://localhost:6379/0

# kabuステーションAPI
KABU_STATION_API_TOKEN=  # 空欄でOK（自動取得）
KABU_STATION_PASSWORD=your_api_password_here
KABU_STATION_API_URL=https://localhost:18080/kabusapi

# Application
APP_NAME=kabu-trade
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 2.4 データベースの起動

```bash
cd ..
docker-compose up -d postgres redis
```

### 2.5 データベースマイグレーション

```bash
cd backend
alembic upgrade head
```

### 2.6 バックエンドの起動

```bash
uvicorn app.main:app --reload
```

バックエンドAPIは http://localhost:8000 で起動します。
APIドキュメントは http://localhost:8000/docs で確認できます。

## 3. フロントエンドのセットアップ

### 3.1 依存関係のインストール

```bash
cd frontend
npm install
```

### 3.2 フロントエンドの起動

```bash
npm run dev
```

フロントエンドは http://localhost:5173 で起動します。

## 4. kabuステーションAPIの設定

1. SBI証券のメンバーズサイトにログイン
2. kabuステーションを起動
3. APIシステム設定で「APIを利用する」にチェック
4. APIパスワードを設定
5. `.env`ファイルの`KABU_STATION_PASSWORD`に設定したパスワードを入力

## 5. 動作確認

1. フロントエンド（http://localhost:5173）にアクセス
2. 銘柄コード（例: 7203）を入力して検索
3. 銘柄情報とチャートが表示されることを確認

## トラブルシューティング

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
