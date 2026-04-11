#!/bin/sh
set -e
cd /app
# Bind mount でホストの frontend が /app を覆うため、node_modules は匿名ボリューム側。
# package.json / lock が更新されたあと古いボリュームだと依存が欠けるので起動時に同期する。
npm install
exec "$@"
