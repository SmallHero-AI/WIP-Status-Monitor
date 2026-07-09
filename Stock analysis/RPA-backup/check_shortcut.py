# -*- coding: utf-8 -*-
import os, glob
import win32com.client

def get_shortcut_target(shortcut_path):
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        return shortcut.TargetPath
    except Exception as e:
        return f"Error: {e}"

search_dirs = [
    r"C:\Users\loadmin\Desktop",
    r"C:\Users\Public\Desktop",
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    r"C:\Users\loadmin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
]

print("Searching for HTS shortcuts...")
for d in search_dirs:
    if not os.path.exists(d):
        continue
    # Search recursively for lnk files
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith('.lnk') and any(kw in f for kw in ['贏家', 'HTS', 'Kway', 'Winner', '快手', '台新']):
                lnk_path = os.path.join(root, f)
                target = get_shortcut_target(lnk_path)
                print(f"Shortcut: {lnk_path} -> Target: {target}")
