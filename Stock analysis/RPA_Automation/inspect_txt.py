# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

file_path = r"C:\ML_Speed\user\2330.txt"

# Try reading as CP950/Big5 since it's a Taiwanese system
try:
    with open(file_path, "r", encoding="cp950", errors="replace") as f:
        print("--- Reading with cp950 ---")
        for i in range(15):
            line = f.readline()
            if not line:
                break
            print(f"Line {i+1}: {repr(line)}")
except Exception as e:
    print("CP950 read error:", e)

# Try reading as UTF-8
try:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        print("--- Reading with utf-8 ---")
        for i in range(5):
            line = f.readline()
            if not line:
                break
            print(f"Line {i+1}: {repr(line)}")
except Exception as e:
    print("UTF-8 read error:", e)
