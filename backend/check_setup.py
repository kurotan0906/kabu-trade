#!/usr/bin/env python3
"""
セットアップ確認スクリプト
"""

import sys
import os

def check_python_version():
    """Pythonバージョンの確認"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"✗ Python 3.11以上が必要です（現在: {version.major}.{version.minor}.{version.micro}）")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_files():
    """必要なファイルの存在確認"""
    required_files = [
        "app/main.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/stock.py",
        "app/models/stock_price.py",
        "app/schemas/stock.py",
        "app/external/providers/base.py",
        "app/external/providers/kabu_station.py",
        "app/external/kabu_station_client.py",
        "app/repositories/stock_repository.py",
        "app/services/stock_service.py",
        "app/api/v1/stocks.py",
        "requirements.txt",
        "alembic.ini",
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✓ {file}")
    
    if missing_files:
        print("\n✗ 以下のファイルが見つかりません:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

def check_imports():
    """インポートの構文チェック"""
    print("\nインポート構文チェック:")
    
    files_to_check = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/stock.py",
        "app/models/stock_price.py",
    ]
    
    errors = []
    for file in files_to_check:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    compile(f.read(), file, 'exec')
                print(f"✓ {file}")
            except SyntaxError as e:
                print(f"✗ {file}: {e}")
                errors.append((file, e))
    
    return len(errors) == 0

def check_env_file():
    """環境変数ファイルの確認"""
    if os.path.exists(".env"):
        print("\n✓ .envファイルが存在します")
        return True
    else:
        print("\n⚠ .envファイルが存在しません（.env.exampleをコピーして作成してください）")
        return False

def main():
    """メイン処理"""
    print("=" * 50)
    print("Kabu Trade バックエンド セットアップ確認")
    print("=" * 50)
    
    all_ok = True
    
    print("\n1. Pythonバージョン確認:")
    if not check_python_version():
        all_ok = False
    
    print("\n2. ファイル存在確認:")
    if not check_files():
        all_ok = False
    
    print("\n3. インポート構文チェック:")
    if not check_imports():
        all_ok = False
    
    print("\n4. 環境変数ファイル確認:")
    check_env_file()
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✓ 基本的な構造は問題ありません")
        print("\n次のステップ:")
        print("1. 依存関係をインストール: pip install -r requirements.txt")
        print("2. .envファイルを作成して設定")
        print("3. Docker Composeでデータベースを起動")
        print("4. データベースマイグレーション: alembic upgrade head")
        print("5. アプリケーション起動: uvicorn app.main:app --reload")
    else:
        print("✗ いくつかの問題が見つかりました")
        sys.exit(1)

if __name__ == "__main__":
    main()
