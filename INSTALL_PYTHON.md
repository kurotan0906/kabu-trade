# Python 3.11 インストール手順

## 現在の状況

- 現在のPython: 3.9.6
- 必要なPython: 3.11以上
- Homebrew: 未インストール

## インストール方法

### 方法1: Homebrewを使用（推奨）

ターミナルで以下を実行してください：

```bash
# 1. Homebrewをインストール（管理者パスワードが必要）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. インストール後、パスを通す（Apple Silicon Macの場合）
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc

# 3. Python 3.11をインストール
brew install python@3.11

# 4. インストール確認
python3.11 --version

# 5. アップグレードスクリプトを実行
cd /Users/mfujii/Documents/source/kabu-trade
./scripts/upgrade_python.sh
```

### 方法2: Python公式インストーラーを使用

1. **Python公式サイトにアクセス**
   - https://www.python.org/downloads/
   - Python 3.11.x または 3.12.x をダウンロード

2. **インストーラーを実行**
   - ダウンロードした `.pkg` ファイルを開く
   - インストールウィザードに従ってインストール

3. **インストール確認**
   ```bash
   python3.11 --version
   # または
   python3.12 --version
   ```

4. **仮想環境を再作成**
   ```bash
   cd /Users/mfujii/Documents/source/kabu-trade/backend
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 方法3: pyenvを使用

```bash
# 1. pyenvをインストール
curl https://pyenv.run | bash

# 2. シェル設定ファイルに追加
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# 3. Python 3.11をインストール
pyenv install 3.11.9

# 4. プロジェクトで使用
cd /Users/mfujii/Documents/source/kabu-trade
pyenv local 3.11.9

# 5. 仮想環境を再作成
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## インストール後の確認

```bash
# Pythonバージョン確認
python3.11 --version
# または
python3.12 --version

# 仮想環境内で確認
cd backend
source venv/bin/activate
python --version
```

## トラブルシューティング

### Pythonが見つからない場合

```bash
# パスを確認
which python3.11
which python3.12

# シェル設定ファイルを再読み込み
source ~/.zshrc
```

### 仮想環境の作成に失敗する場合

```bash
# 既存の仮想環境を削除
cd backend
rm -rf venv

# 新しいPythonで仮想環境を作成
python3.11 -m venv venv
source venv/bin/activate
```

## 次のステップ

Python 3.11以上をインストール後：

1. `./scripts/upgrade_python.sh` を実行
2. または、手動で仮想環境を再作成（上記参照）
