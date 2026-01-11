# Kabu Trade Frontend

株取引支援システムのフロントエンド（React + TypeScript + Vite）

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. 開発サーバーの起動

```bash
npm run dev
```

アプリケーションは http://localhost:5173 で起動します。

### 3. ビルド

```bash
npm run build
```

## プロジェクト構造

```
frontend/
├── src/
│   ├── components/    # UIコンポーネント
│   │   ├── common/   # 共通コンポーネント
│   │   └── stock/    # 株情報関連コンポーネント
│   ├── pages/        # ページコンポーネント
│   ├── services/     # API通信層
│   ├── store/        # 状態管理（Zustand）
│   ├── hooks/        # カスタムフック
│   ├── types/        # TypeScript型定義
│   └── utils/        # ユーティリティ
├── public/           # 静的ファイル
└── package.json      # 依存関係
```
