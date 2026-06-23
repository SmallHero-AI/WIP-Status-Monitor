# -*- coding: utf-8 -*-
import os
import json
import sys
import subprocess
import pandas as pd

# 解決 Windows 主機 Console 輸出 Unicode Emojis 編碼錯誤
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
LEADERBOARD_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard.json")
STOCK_LIST_PATH = os.path.join(SCRIPT_DIR, "Stock original", "有價證券代號與名稱.xlsx")

# 12 檔預設基礎個股
base_stocks = {
    '2330': '台積電', '2360': '致茂', '6205': '詮欣', '6274': '台耀',
    '6669': '緯穎', '3189': '景碩', '3455': '由田', '3535': '晶彩科',
    '4908': '前鼎', '6269': '台郡', '3443': '創意', '6261': '久元'
}

def main():
    print("=" * 60)
    print("  [Start] V7 全自動化更新與推送管線 (update_and_push.py)...")
    print("=" * 60)

    # 1. 合併去重代碼名單，重建有價證券代號與名稱.xlsx
    stocks = base_stocks.copy()
    if os.path.exists(LEADERBOARD_PATH):
        try:
            with open(LEADERBOARD_PATH, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
                for item in leaderboard:
                    code = str(item['code']).strip()
                    name = str(item['name']).strip()
                    stocks[code] = name
        except Exception as e:
            print(f"⚠️  讀取 leaderboard.json 失敗: {e}")

    df = pd.DataFrame(list(stocks.items()), columns=['有價證券代號', '有價證券名稱'])
    os.makedirs(os.path.dirname(STOCK_LIST_PATH), exist_ok=True)
    df.to_excel(STOCK_LIST_PATH, index=False)
    print(f"✅ 1. 去重合併名單完成，共 {len(df)} 檔個股（12 檔基礎 + 精選 AI 策略個股）。")
    print(f"   已存入: {STOCK_LIST_PATH}")
    print("-" * 60)

    # 2. 啟動 RPA 行情下載程序
    print("🚀 2. 啟動 RPA 行情下載程序 (stock_exporter.py)...")
    try:
        p = subprocess.Popen(
            ["python", "stock_exporter.py"],
            cwd=os.path.join(SCRIPT_DIR, "RPA_Automation"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(input=b"\n\n\n")
        print("[RPA 輸出]:")
        print(stdout.decode('utf-8', errors='ignore'))
        if p.returncode != 0:
            print("[RPA 錯誤]:")
            print(stderr.decode('utf-8', errors='ignore'))
            print("⚠️  RPA 執行可能有部分未完全成功，程序將繼續後續步驟...")
    except Exception as e:
        print(f"❌  RPA 執行失敗: {e}")
        print("⚠️  將繼續後續的本機數據重算步驟...")
    print("-" * 60)

    # 3. 執行 12 檔基礎個股 Excel 行情更新
    print("🚀 3. 執行 12 檔預設個股 Excel 行情更新 (update_base_stocks_backtests.py)...")
    try:
        subprocess.run(["python", "update_base_stocks_backtests.py"], cwd=SCRIPT_DIR, check=True)
        print("✅ 3. 預設個股 Excel 歷史數據更新完成。")
    except Exception as e:
        print(f"❌  預設個股更新失敗: {e}")
    print("-" * 60)

    # 4. 執行高勝率策略重新篩選
    print("🚀 4. 執行高勝率策略重新篩選 (search_75_winrate.py)...")
    try:
        subprocess.run(["python", "search_75_winrate.py"], cwd=SCRIPT_DIR, check=True)
        print("✅ 4. 策略篩選與排行榜重建完成。")
    except Exception as e:
        print(f"❌  策略篩選與排行榜重建失敗: {e}")
    print("-" * 60)

    # 5. 重新生成 131 檔 AI 推薦個股回測 Excel
    print("🚀 5. 重新生成精選個股回測 Excel (export_high_win_excel.py)...")
    try:
        subprocess.run(["python", "export_high_win_excel.py"], cwd=SCRIPT_DIR, check=True)
        print("✅ 5. 精選個股 Excel 回測生成完成。")
    except Exception as e:
        print(f"❌  精選個股 Excel 回測生成失敗: {e}")
    print("-" * 60)

    # 6. 編譯網頁
    print("🚀 6. 編譯並更新網頁 (patch_dashboard_categories.py)...")
    try:
        subprocess.run(["python", "patch_dashboard_categories.py"], cwd=SCRIPT_DIR, check=True)
        print("✅ 6. 網頁編譯與注入完成。")
    except Exception as e:
        print(f"❌  網頁編譯與注入失敗: {e}")
    print("-" * 60)

    # 7. 自動提交與推送 Git 倉庫
    print("🚀 7. 自動提交與推送 Git 倉庫...")
    
    # 修正版_V6_Server 子倉庫推送
    server_dir = os.path.join(SCRIPT_DIR, "修正版_V6_Server")
    try:
        subprocess.run(["git", "add", "."], cwd=server_dir, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=server_dir, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", "V7 Auto Update:行情與策略數據自動更新(Server)"], cwd=server_dir, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=server_dir, check=True)
            print("✅ 7a. 修正版_V6_Server 已成功推送至 GitHub！")
        else:
            print("💡 7a. 修正版_V6_Server 無任何異動，無需提交。")
    except Exception as e:
        print(f"⚠️  7a. 修正版_V6_Server 提交或推送失敗: {e}")

    # 主倉庫推送
    root_dir = r"E:\G-AI-1"
    try:
        subprocess.run(["git", "add", "."], cwd=root_dir, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=root_dir, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", "V7 Auto Update:行情與策略數據自動更新(Root)"], cwd=root_dir, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=root_dir, check=True)
            print("✅ 7b. 主倉庫已成功推送至 GitHub！")
        else:
            print("💡 7b. 主倉庫無任何異動，無需提交。")
    except Exception as e:
        print(f"⚠️  7b. 主倉庫提交或推送失敗: {e}")

    print("=" * 60)
    print("  [Done] V7 全自動化更新管線執行完畢！")
    print("=" * 60)

if __name__ == "__main__":
    main()
