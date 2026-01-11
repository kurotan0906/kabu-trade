# Python アップグレード手順

## 現在の状況

- 現在のPythonバージョン: 3.9.6
- 推奨バージョン: Python 3.11以上
- Homebrew: 未インストール

## アップグレード方法

### 方法1: HomebrewをインストールしてからPythonをアップグレード（推奨）

まず、Homebrewをインストール：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

インストール後、Python 3.11をインストール：

```bash
# Python 3.11をインストール
brew install python@3.11

# または最新版（3.12以上）
brew install python@3.12
```

インストール後、新しいPythonを使用するには：

```bash
# 新しいPythonのパスを確認
which python3.11
# または
which python3.12

# 仮想環境を再作成
cd backend
rm -rf venv
python3.11 -m venv venv
# または
python3.12 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 依存関係を再インストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 方法2: pyenvを使用

```bash
# pyenvをインストール（未インストールの場合）
brew install pyenv

# Python 3.11をインストール
pyenv install 3.11.9

# プロジェクトディレクトリで使用するPythonバージョンを設定
cd /Users/mfujii/Documents/source/kabu-trade
pyenv local 3.11.9

# 仮想環境を再作成
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 方法3: 公式インストーラーを使用

1. [Python公式サイト](https://www.python.org/downloads/)からPython 3.11以上をダウンロード
2. インストーラーを実行
3. インストール後、仮想環境を再作成

## アップグレード後の確認

```bash
# Pythonバージョン確認
python --version
# または
python3 --version

# 仮想環境内で確認
cd backend
source venv/bin/activate
python --version
```

## 注意事項

- 仮想環境を再作成する必要があります
- 依存関係を再インストールする必要があります
- pandas-taなどの一部のパッケージはPython 3.10以上が必要です

## アップグレード後の動作確認

```bash
# アプリケーションのインポート確認
cd backend
source venv/bin/activate
python -c "from app.main import app; print('✓ 成功')"

# バックエンド起動確認
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
