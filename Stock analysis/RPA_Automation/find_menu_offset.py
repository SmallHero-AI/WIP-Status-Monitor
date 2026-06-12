"""
================================================================================
  右鍵選單偏移量測量工具
  用途：幫助您找出右鍵選單中「匯出至 Excel」的精確偏移量
================================================================================

使用方法：
  1. 先手動在 K 線圖上按右鍵，讓選單彈出
  2. 執行此腳本：python find_menu_offset.py
  3. 在 3 秒內移動滑鼠到「匯出至 Excel」選項上
  4. 程式會記錄位置，幫助您計算偏移量
================================================================================
"""

import pyautogui
import time

print("=" * 55)
print("  右鍵選單「匯出至 Excel」偏移量測量工具")
print("=" * 55)
print()
print("操作步驟：")
print("  1. 先在看盤軟體 K 線圖按右鍵（讓選單出現）")
print("  2. 回到此視窗後，輸入您的右鍵點擊座標")
print("  3. 再移動滑鼠到選單中的「匯出至 Excel」選項")
print("  4. 按 Enter 記錄位置")
print()

try:
    right_click_x = int(input("請輸入您的右鍵點擊 X 座標："))
    right_click_y = int(input("請輸入您的右鍵點擊 Y 座標："))
except ValueError:
    print("輸入格式錯誤，請輸入整數。")
    exit(1)

print()
print("請在 5 秒內移動滑鼠到「匯出至 Excel」選項上...")
for i in range(5, 0, -1):
    print(f"  倒數 {i}...", end='\r')
    time.sleep(1)

menu_x, menu_y = pyautogui.position()
offset_x = menu_x - right_click_x
offset_y = menu_y - right_click_y

print(f"\n\n測量結果：")
print(f"  右鍵點擊位置：({right_click_x}, {right_click_y})")
print(f"  選單項目位置：({menu_x}, {menu_y})")
print(f"  偏移量：offset_x = {offset_x}, offset_y = {offset_y}")
print()
print("請將以下設定填入 stock_exporter.py 的 CONFIG 區塊：")
print(f'  "kline_right_click_pos": ({right_click_x}, {right_click_y}),')
print(f'  "export_menu_offset_y": {offset_y},')
