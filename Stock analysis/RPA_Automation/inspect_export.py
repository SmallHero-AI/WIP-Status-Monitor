# -*- coding: utf-8 -*-
import os, glob, time

dirs = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.environ.get('TEMP', ''),
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
    r"C:\Users\loadmin\Desktop",
    r"C:\Users\loadmin\Documents",
    r"C:\Users\loadmin\Downloads",
]

found_files = []
for d in dirs:
    if not d or not os.path.exists(d):
        continue
    for ext in ['*.txt', '*.xls', '*.xlsx']:
        for f in glob.glob(os.path.join(d, ext)):
            try:
                mt = os.path.getmtime(f)
                # Check if it was modified in the last 30 minutes
                if time.time() - mt < 1800:
                    found_files.append((f, mt))
            except:
                pass

found_files.sort(key=lambda x: x[1], reverse=True)
print(f"Found {len(found_files)} files modified in last 30 minutes:")
for f, mt in found_files[:10]:
    print(f"File: {f} | Size: {os.path.getsize(f)} bytes | Time: {time.ctime(mt)}")
    # Print first 5 lines of txt files
    if f.endswith('.txt'):
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as file:
                lines = [file.readline().strip() for _ in range(5)]
            print("--- Content ---")
            for l in lines:
                print(repr(l))
            print("---------------")
        except Exception as e:
            print("Read error:", e)
