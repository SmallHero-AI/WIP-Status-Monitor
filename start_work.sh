#!/bin/bash
# ==============================================================================
# 在家中或另一端開始工作前的同步與啟動腳本
# ==============================================================================

echo "=== [1/4] 正在拉取主專案最新程式碼... ==="
git pull origin main

echo "=== [2/4] 正在拉取量化網頁伺服器子專案最新程式碼... ==="
cd "Stock analysis/修正版_V5_Server" || exit
git pull origin main
cd ../..

echo "=== [3/4] 正在執行多指標交叉組合搜尋引擎，生成排行榜數據... ==="
cd "Stock analysis" || exit
python search_best_combinations.py
cd ..

echo "=== [4/4] 正在啟動量化網頁伺服器 (請瀏覽 http://localhost:8000/index_v3.html) ==="
cd "Stock analysis/修正版_V5_Server" || exit
node server.js
