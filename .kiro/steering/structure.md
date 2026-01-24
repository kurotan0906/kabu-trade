# プロジェクト構造

_updated_at: 2026-01-24_

## 組織化の思想

- **バックエンドはレイヤード**: API（入出力）/ Service（ユースケース）/ Repository（永続化）/ External（外部I/O）/ Core（横断）を分離し、変更の影響範囲を局所化する
- **フロントエンドは関心ごと単位で分割**: ページ（routes）と再利用可能コンポーネント、API通信、状態管理、型定義を分ける
- **“追加に強い”構造**: 新しいドメイン（例: strategy）を追加しても、既存のパターンに従えば大きな再編が不要になることを目標にする

## ディレクトリパターン

### Backend APIレイヤ
**Location**: `backend/app/api/`  
**Purpose**: ルーティング、入出力の境界（依存注入、HTTP固有の処理）  
**Example**: `backend/app/api/v1/stocks.py` にエンドポイント、Service呼び出しを配置

### Backend Serviceレイヤ
**Location**: `backend/app/services/`  
**Purpose**: ユースケースの中心。複数のRepository/External/Utilsを組み合わせる  
**Example**: `StockService`, `EvaluationService`, `AnalysisEngine`

### Backend Repositoryレイヤ
**Location**: `backend/app/repositories/`  
**Purpose**: DBアクセスの抽象化（クエリや永続化の詳細を閉じ込める）  
**Example**: `stock_repository.py`

### Backend Domain / Schema
**Location**: `backend/app/models/`, `backend/app/schemas/`  
**Purpose**: 永続化モデル（SQLAlchemy）と入出力スキーマ（Pydantic）を分離し、責務混在を避ける  
**Example**: `models/stock.py`, `schemas/stock.py`

### Backend Cross-cutting / External
**Location**: `backend/app/core/`, `backend/app/external/`, `backend/app/utils/`  
**Purpose**: 設定、DB/Redis、例外、ログ、外部APIクライアント、分析ユーティリティ  
**Example**: `core/config.py`, `core/redis_client.py`, `external/providers/*`

### Backend Tests
**Location**: `backend/tests/`  
**Purpose**: ユースケース/ゲート判定などのドメインロジックを中心に、pytest（必要に応じてpytest-asyncio）で検証する  
**Note**: `backend/pytest.ini` で `.venv` / `venv*` / `site-packages` を除外し、仮想環境内の誤収集を防ぐ

### Frontend UI
**Location**: `frontend/src/components/`, `frontend/src/pages/`  
**Purpose**: UI部品とページ（ルーティング単位）  
**Example**: `components/stock/*` は株情報ドメイン、`components/common/*` は再利用部品

### Frontend Data / State / Types
**Location**: `frontend/src/services/`, `frontend/src/store/`, `frontend/src/types/`, `frontend/src/hooks/`  
**Purpose**: API通信、状態管理（Zustand）、型定義、UIから切り離したロジック  
**Example**: `services/api/*Api.ts`, `store/stockStore.ts`

## 命名規約（基本）

- **Python**
  - **Files/Modules**: `snake_case.py`
  - **Classes**: `PascalCase`
  - **Functions/Vars**: `snake_case`
- **TypeScript/React**
  - **Components**: `PascalCase.tsx`（例: `StockChart.tsx`）
  - **Hooks**: `useXxx.ts`（例: `useStock`）
  - **Stores/Utils**: `camelCase.ts`

## Importの方針

### Frontend（推奨）

```typescript
// 優先: パスエイリアス（広域参照）
import { StockSearch } from '@/components/stock/StockSearch'

// 同一ディレクトリ内など局所: 相対import
import { Loading } from './Loading'
```

**Path Aliases**:
- `@/`: `frontend/src` にマップ（Vite と tsconfig の両方で定義）

### Backend（推奨）

- `from app.<layer>...` のような **アプリ内の絶対import** を基本にして、レイヤの依存関係が読み取りやすい状態を維持する

## 依存関係の原則（守りたいルール）

- **API層はHTTPの都合に閉じ込める**: ビジネスルールはServiceに寄せる
- **Serviceは“調停者”**: Repository/External/Utils を組み合わせるが、DBやHTTPの詳細に直接寄りすぎない
- **Repositoryは永続化の詳細を隠す**: 呼び出し側は「何を取得/保存するか」に集中する
- **Externalは境界を明確に**: 外部APIの仕様変更がドメイン全体に波及しないようにする

---
_パターンを記し、ディレクトリツリーの網羅は避ける。新規追加は既存パターンに従えば原則更新不要_
