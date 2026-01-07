# GitHub リポジトリ作成手順

## 1. GitHubでリポジトリを作成

1. GitHubにログイン: https://github.com
2. 右上の「+」ボタンをクリック → 「New repository」を選択
3. リポジトリ情報を入力:
   - Repository name: `kabu-trade` (またはお好みの名前)
   - Description: `株取引支援システム - 個人の投資効率化のためのツール`
   - Visibility: Private または Public (お好みで)
   - **Initialize this repository with: は全てチェックを外す** (既にローカルにファイルがあるため)
4. 「Create repository」をクリック

## 2. リモートリポジトリを追加してpush

GitHubでリポジトリを作成したら、以下のコマンドを実行してください：

```bash
cd /Users/mfujii/Documents/source/kabu-trade

# リモートリポジトリを追加（YOUR_USERNAMEをあなたのGitHubユーザー名に置き換えてください）
git remote add origin https://github.com/YOUR_USERNAME/kabu-trade.git

# またはSSHを使用する場合
# git remote add origin git@github.com:YOUR_USERNAME/kabu-trade.git

# ブランチ名をmainに設定（既にmainの場合は不要）
git branch -M main

# GitHubにpush
git push -u origin main
```

## 3. 認証について

### HTTPSを使用する場合
- 初回push時にGitHubのユーザー名とパスワード（またはPersonal Access Token）を求められます
- Personal Access Tokenを使用する場合:
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. 「Generate new token (classic)」をクリック
  3. 必要な権限を選択（repo権限が必要）
  4. トークンを生成してコピー
  5. パスワードの代わりにこのトークンを使用

### SSHを使用する場合
- SSH鍵が設定されている必要があります
- 未設定の場合は、HTTPSを使用することをお勧めします

## 4. 確認

pushが成功したら、GitHubのリポジトリページでファイルが表示されることを確認してください。

