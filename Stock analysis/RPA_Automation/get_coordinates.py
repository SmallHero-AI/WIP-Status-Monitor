"""
================================================================================
  座標測量輔助工具
  用途：幫助您測量螢幕上各個元素的精確像素座標
        用於填入 stock_exporter.py 的 CONFIG 設定
================================================================================

使用方法：
  python get_coordinates.py

執行後：
  - 程式會每隔 1 秒印出目前滑鼠位置（x, y）
  - 將滑鼠移到目標位置後，記錄顯示的座標
  - 按 Ctrl+C 結束
================================================================================
"""

import pyautogui
import time
import sys

print("=" * 50)
print("  滑鼠座標測量工具")
print("=" * 50)
print("移動滑鼠到目標位置，每秒顯示一次座標")
print("按 Ctrl+C 結束程式\n")

print("📌 您需要測量的座標：")
print("  1. K 線圖右鍵點擊位置（kline_right_click_pos）")
print("  2. 右鍵選單「匯出至 Excel」的位置（menu_offset_y）\n")

print("-" * 30)

try:
    while True:
        x, y = pyautogui.position()
        position_str = f"  目前位置：X={x:4d}, Y={y:4d}"
        print(position_str, end='\r', flush=True)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\n測量完成，請將座標填入 stock_exporter.py 的 CONFIG 區塊。")
    x, y = pyautogui.position()
    print(f"最後記錄座標：({x}, {y})")
