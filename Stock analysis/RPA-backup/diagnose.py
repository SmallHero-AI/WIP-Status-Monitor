# -*- coding: utf-8 -*-
import pyautogui
import pygetwindow as gw
import glob, os, time, sys
from datetime import datetime

# 強制 UTF-8 輸出
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=== 完整環境診斷 ===", flush=True)
print(f"螢幕: {pyautogui.size()}", flush=True)
mx, my = pyautogui.position()
print(f"滑鼠: ({mx}, {my})", flush=True)
print(flush=True)

# ── 所有視窗（安全印出）──
all_wins = gw.getAllWindows()
print(f"目前開啟視窗 ({len(all_wins)} 個):", flush=True)
for w in all_wins:
    t = w.title.strip()
    if not t:
        continue
    try:
        safe_title = t.encode('utf-8', errors='replace').decode('utf-8')
        print(f"  [{w.width}x{w.height}] {safe_title}", flush=True)
    except Exception:
        print(f"  [?x?] (無法顯示標題)", flush=True)
print(flush=True)

# ── 找看盤軟體（搜尋含 HTS 或 贏家 等關鍵字）──
keywords = ['贏家', 'winner', '快手', '台新', 'hts', 'Winner', 'HTS']
found_winner = None
for w in all_wins:
    for kw in keywords:
        if kw.lower() in w.title.lower():
            found_winner = w
            break
    if found_winner:
        break

if found_winner:
    title = found_winner.title.encode('utf-8', errors='replace').decode('utf-8')
    print(f"看盤軟體: {title}", flush=True)
    print(f"  位置: ({found_winner.left}, {found_winner.top})", flush=True)
    print(f"  大小: {found_winner.width} x {found_winner.height}", flush=True)
    # 顯示中心點 (left + width//2, top + height//2)
    cx = found_winner.left + found_winner.width // 2
    cy = found_winner.top + found_winner.height // 2
    print(f"  視窗中心: ({cx}, {cy})", flush=True)
else:
    print("未找到看盤軟體（請確認已開啟台新贏家快手）", flush=True)
print(flush=True)

# ── 找 Excel ──
excel_wins = [w for w in all_wins if 'excel' in w.title.lower() or '.xlsx' in w.title.lower()]
if excel_wins:
    print(f"Excel 視窗:", flush=True)
    for ew in excel_wins:
        print(f"  {ew.title}", flush=True)
else:
    print("目前無 Excel 視窗", flush=True)
print(flush=True)

# ── 最近 xlsx ──
print("最近 Excel 檔案（24小時內）:", flush=True)
dirs = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.environ.get("TEMP", ""),
    r"C:\Users\loadmin\Desktop",
    r"C:\Users\loadmin\Documents",
]
now_ts = time.time()
found_files = []
for d in dirs:
    if not d or not os.path.exists(d):
        continue
    for f in glob.glob(os.path.join(d, "*.xlsx")) + glob.glob(os.path.join(d, "*.xls")):
        mt = os.path.getmtime(f)
        if now_ts - mt < 86400:
            found_files.append((mt, f))

found_files.sort(reverse=True)
if found_files:
    for mt, fp in found_files[:8]:
        ts = datetime.fromtimestamp(mt).strftime("%H:%M:%S")
        print(f"  [{ts}] {fp}", flush=True)
else:
    print("  (無)", flush=True)

print(flush=True)
print("診斷完成。", flush=True)
