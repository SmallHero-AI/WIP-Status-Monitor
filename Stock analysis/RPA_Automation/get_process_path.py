# -*- coding: utf-8 -*-
import ctypes
import win32api, win32process, win32gui, win32con

def get_process_path(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        h_process = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        if h_process:
            path = win32process.GetModuleFileNameEx(h_process, 0)
            win32api.CloseHandle(h_process)
            return path
    except Exception as e:
        return f"Error: {e}"
    return "Unknown"

# Find HTS window
KEYWORDS = ['贏家', 'HTS', 'Kway', 'Winner', '快手', '台新']
wins = []
def cb(hwnd, _):
    try:
        t = win32gui.GetWindowText(hwnd)
        if any(kw in t for kw in KEYWORDS):
            wins.append((hwnd, t))
    except:
        pass
win32gui.EnumWindows(cb, None)

for h, t in wins:
    path = get_process_path(h)
    print(f"Window: {t} | Path: {path}")
