"""
================================================================================
  箭頭符號清洗單元測試
  用途：驗證 clean_arrow_symbols 函數的清洗效果是否正確
================================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stock_exporter import clean_arrow_symbols, batch_clean_only, CONFIG

def test_clean_arrow_symbols():
    """測試各種箭頭符號的清洗結果"""

    # 格式：(輸入值, 預期輸出)
    test_cases = [
        ("82.5▲",    82.5),
        ("12.3↓",    12.3),
        ("-5.6▼",   -5.6),
        ("100.0↑",  100.0),
        ("0△",        0.0),
        ("99.9▽",    99.9),
        ("1,234.5",  1234.5),  # 千分位
        ("0.00",       0.0),
        ("N/A",       None),   # 無效值
        ("",          None),   # 空字串
        (None,        None),   # None 值
        (float('nan'), None),  # NaN
        (82.5,        82.5),   # 已是數字（不需清洗）
        ("82.5▲▲",   82.5),   # 多個箭頭
    ]

    print("=" * 55)
    print("  箭頭符號清洗函數單元測試")
    print("=" * 55)

    all_pass = True
    for i, (input_val, expected) in enumerate(test_cases, 1):
        result = clean_arrow_symbols(input_val)
        ok = (result == expected) or (result is None and expected is None)
        status = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_pass = False
        print(f"  [{i:2d}] {status} | 輸入：{repr(str(input_val)):15s} | 預期：{str(expected):8s} | 實際：{result}")

    print()
    if all_pass:
        print("✅ 所有測試通過！")
    else:
        print("❌ 有測試未通過，請檢查 clean_arrow_symbols 函數。")

    return all_pass


def test_clean_mode():
    """測試批次清洗模式（需要有現成的 Excel 檔案）"""
    print("\n" + "=" * 55)
    print("  批次清洗模式測試（需有 Excel 檔案）")
    print("=" * 55)

    source = CONFIG["temp_export_folder"]
    output = CONFIG["output_folder"]

    import glob
    files = glob.glob(os.path.join(source, "*.xlsx"))
    if not files:
        print(f"  ⚠️  在 {source} 找不到 Excel 檔案，跳過此測試。")
        return

    print(f"  找到 {len(files)} 個 Excel 檔案，開始清洗測試...")
    batch_clean_only(source, output, CONFIG["stock_names"], CONFIG["date_suffix"])


if __name__ == "__main__":
    test_clean_arrow_symbols()
    # 若要測試批次清洗，取消下行的註解：
    # test_clean_mode()
