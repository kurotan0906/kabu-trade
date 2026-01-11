# Kabu Trade Backend

株取引支援システムのバックエンドAPI（FastAPI）

## セットアップ

### 1. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env`ファイルを作成し、`.env.example`を参考に設定してください。

```bash
cp .env.example .env
# .envファイルを編集
```

### 4. データベースのセットアップ

Docker ComposeでPostgreSQLとRedisを起動：

```bash
cd ..
docker-compose up -d postgres redis
```

### 5. データベースマイグレーション

```bash
alembic upgrade head
```

### 6. アプリケーションの起動

```bash
uvicorn app.main:app --reload
```

APIドキュメントは http://localhost:8000/docs で確認できます。

## プロジェクト構造

```
backend/
├── app/
│   ├── api/          # APIルーティング
│   ├── core/         # コア設定（config, database, exceptions等）
│   ├── models/       # データベースモデル
│   ├── schemas/      # Pydanticスキーマ
│   ├── services/     # ビジネスロジック
│   ├── repositories/ # データアクセス層
│   ├── external/     # 外部API連携
│   └── utils/        # ユーティリティ
├── alembic/          # データベースマイグレーション
├── tests/            # テスト
└── requirements.txt  # 依存関係
```
