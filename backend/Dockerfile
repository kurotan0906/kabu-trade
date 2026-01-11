FROM python:3.11-slim as builder

WORKDIR /app

# システム依存関係のインストール（ビルド用）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 本番用イメージ
FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール（最小限）
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージから依存関係をコピー
COPY --from=builder /root/.local /root/.local

# パスに追加
ENV PATH=/root/.local/bin:$PATH

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーション起動（本番モード）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
