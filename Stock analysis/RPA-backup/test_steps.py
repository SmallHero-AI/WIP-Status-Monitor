# -*- coding: utf-8 -*-
"""
================================================================================
  RPA 逐步測試工具
  
  用途：單獨測試每個 Step，確認動作是否正確後再執行主程式
  
  執行方式：
    python test_steps.py          --> 依序測試所有步驟
    python test_steps.py mouse    --> 只測試滑鼠移動
    python test_steps.py step1    --> 只測試 Step1（輸入股號）
    python test_steps.py step2    --> 只測試 Step2（右鍵匯出）
================================================================================
"""

import pyautogui
import time
import sys
from datetime import datetime

pyautogui.FAILSAFE = True
MOUSE_DURATION = 0.4


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}", flush=True)


def countdown(sec=3, msg="開始測試"):
    print(f"\n⚠️  {sec} 秒後{msg}（移至左上角可中止）", flush=True)
    for i in range(sec, 0, -1):
        print(f"  {i}...", flush=True)
        time.sleep(1)
    print(flush=True)


# ================================================================
#  測試一：滑鼠基本移動
# ================================================================
def test_mouse():
    """測試滑鼠能否正常移動和點擊"""
    print("\n=== 測試：滑鼠基本移動 ===", flush=True)
    countdown(3, "移動滑鼠")

    positions = [
        (400, 300, "螢幕中左"),
        (960, 540, "螢幕正中"),
        (600, 400, "中間偏左"),
    ]

    for x, y, label in positions:
        log(f"移動到 ({x}, {y}) [{label}]")
        pyautogui.moveTo(x, y, duration=MOUSE_DURATION)
        time.sleep(0.3)
        rx, ry = pyautogui.position()
        ok = abs(rx - x) < 5 and abs(ry - y) < 5
        log(f"  → 實際位置 ({rx}, {ry}) {'✅ 正確' if ok else '❌ 偏差！'}")

    log("滑鼠測試完成！")


# ================================================================
#  測試二：Step1 模擬
# ================================================================
def test_step1():
    """
    測試 Step1：點擊 (155,125) → 輸入代號 → Enter
    注意：這會實際點擊和輸入，請確認看盤軟體已開啟
    """
    print("\n=== 測試 Step1：輸入股號 ===", flush=True)
    print("  測試代號：2330", flush=True)
    countdown(5, "執行 Step1（請切換至看盤軟體）")

    log("移動至搜尋框 (155, 125)")
    pyautogui.moveTo(155, 125, duration=MOUSE_DURATION)
    time.sleep(0.2)

    log("左鍵點擊")
    pyautogui.click()
    time.sleep(0.3)

    log("Ctrl+A 全選清空")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)

    log("輸入：2330")
    pyautogui.typewrite('2330', interval=0.15)
    time.sleep(0.2)

    log("按下 Enter")
    pyautogui.press('enter')
    time.sleep(2.0)

    log("Step1 測試完成！請確認看盤軟體是否切換至 2330（台積電）")


# ================================================================
#  測試三：Step2 模擬（只測試右鍵選單出現，不實際匯出）
# ================================================================
def test_step2_right_click_only():
    """
    只測試右鍵動作（不點擊匯出），驗證右鍵選單是否出現
    """
    print("\n=== 測試 Step2：右鍵 K 線圖（不匯出）===", flush=True)
    countdown(5, "執行右鍵（請切換至看盤軟體的 K 線圖頁面）")

    log("移動至 K 線圖 (500, 200)")
    pyautogui.moveTo(500, 200, duration=MOUSE_DURATION)
    time.sleep(0.2)

    log("右鍵點擊")
    pyautogui.rightClick()
    time.sleep(1.0)

    log("右鍵選單應已出現，按 Esc 關閉")
    pyautogui.press('escape')
    time.sleep(0.5)

    log("Step2（右鍵）測試完成！")
    log("若選單出現且 (550,475) 對應「匯出至 Excel」，則 Step2 正常。")


# ================================================================
#  測試四：完整 Step2（實際匯出）
# ================================================================
def test_step2_full():
    """
    完整測試 Step2：右鍵 → 點選匯出
    """
    print("\n=== 測試 Step2 完整：右鍵 + 匯出 ===", flush=True)
    countdown(5, "執行右鍵 + 點選匯出（請切換至看盤軟體）")

    log("右鍵點擊 K 線圖 (500, 200)")
    pyautogui.moveTo(500, 200, duration=MOUSE_DURATION)
    time.sleep(0.1)
    pyautogui.rightClick()
    time.sleep(0.8)

    log("點擊匯出選單項 (550, 475)")
    pyautogui.moveTo(550, 475, duration=MOUSE_DURATION)
    time.sleep(0.1)
    pyautogui.click()
    time.sleep(4.0)

    log("Step2 完整測試完成！請確認 Excel 是否已開啟")


# ================================================================
#  測試五：滑鼠座標標記（在螢幕上顯示目前位置）
# ================================================================
def show_coordinates(duration=10):
    """
    持續顯示滑鼠座標 N 秒，用於確認座標對應的位置
    """
    print(f"\n=== 座標顯示模式（{duration} 秒）===", flush=True)
    print("  移動滑鼠到目標位置，查看座標是否正確", flush=True)
    print(f"  需要確認的座標：", flush=True)
    print(f"    搜尋框      ：(155, 125)", flush=True)
    print(f"    K線圖右鍵   ：(500, 200)", flush=True)
    print(f"    匯出選單    ：(550, 475)", flush=True)
    print(flush=True)

    deadline = time.time() + duration
    while time.time() < deadline:
        x, y = pyautogui.position()
        remaining = int(deadline - time.time())
        print(f"  目前座標：({x:4d}, {y:4d})  剩餘 {remaining:2d} 秒", end='\r', flush=True)
        time.sleep(0.1)
    print(flush=True)


# ================================================================
#  主選單
# ================================================================

if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "menu"

    if arg == "mouse":
        test_mouse()

    elif arg == "step1":
        test_step1()

    elif arg == "step2":
        test_step2_right_click_only()

    elif arg == "step2full":
        test_step2_full()

    elif arg == "coords":
        show_coordinates(15)

    else:
        # 互動式選單
        print("=" * 50, flush=True)
        print("  RPA 逐步測試工具", flush=True)
        print("=" * 50, flush=True)
        print("  1. 測試滑鼠移動 (mouse)", flush=True)
        print("  2. 測試 Step1 輸入股號", flush=True)
        print("  3. 測試 Step2 右鍵（不匯出）", flush=True)
        print("  4. 測試 Step2 完整（右鍵+匯出）", flush=True)
        print("  5. 顯示即時座標 15 秒 (coords)", flush=True)
        print("  Q. 離開", flush=True)
        print(flush=True)

        choice = input("請選擇 (1-5/Q): ").strip()
        if   choice == '1': test_mouse()
        elif choice == '2': test_step1()
        elif choice == '3': test_step2_right_click_only()
        elif choice == '4': test_step2_full()
        elif choice == '5': show_coordinates(15)
        else: print("離開。")
