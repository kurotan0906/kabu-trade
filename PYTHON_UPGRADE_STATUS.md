# Python アップグレード状況

## 現在の状況

- ✅ Python 3.11.14がインストール済み: `/opt/homebrew/bin/python3.11`
- ⚠️ 仮想環境の再作成で権限エラーが発生

## 問題

仮想環境の作成時に権限エラーが発生しています：
```
ERROR: Could not install packages due to an OSError: [Errno 1] Operation not permitted
```

## 解決方法

### 方法1: 手動で仮想環境を作成

ターミナルで以下を実行してください：

```bash
cd /Users/mfujii/Documents/source/kabu-trade/backend

# 既存の仮想環境を削除
rm -rf venv

# PATHにHomebrewのパスを追加
export PATH="/opt/homebrew/bin:$PATH"

# 仮想環境を作成
/opt/homebrew/bin/python3.11 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをインストール（必要に応じて）
curl -sS https://bootstrap.pypa.io/get-pip.py | python

# pipをアップグレード
pip install --upgrade pip

# 依存関係をインストール
pip install fastapi uvicorn[standard] sqlalchemy alembic asyncpg psycopg2-binary redis httpx aiohttp python-dotenv pydantic-settings pydantic pandas numpy
```

### 方法2: シェル設定ファイルにPATHを追加

`~/.zshrc` に以下を追加：

```bash
export PATH="/opt/homebrew/bin:$PATH"
```

その後、シェルを再起動：

```bash
source ~/.zshrc
```

その後、通常の方法で仮想環境を作成：

```bash
cd /Users/mfujii/Documents/source/kabu-trade/backend
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 方法3: 権限の確認

仮想環境ディレクトリの権限を確認：

```bash
cd /Users/mfujii/Documents/source/kabu-trade/backend
ls -la | grep venv
```

必要に応じて権限を修正：

```bash
chmod -R u+w venv
```

## 確認

仮想環境が正常に作成されたら：

```bash
cd backend
source venv/bin/activate
python --version  # Python 3.11.14 と表示されるはず
pip list  # インストールされたパッケージが表示される
```

## 次のステップ

仮想環境が正常に作成されたら：

1. アプリケーションの動作確認:
   ```bash
   python -c "from app.main import app; print('✓ 成功')"
   ```

2. バックエンドを起動:
   ```bash
   uvicorn app.main:app --reload
   ```
