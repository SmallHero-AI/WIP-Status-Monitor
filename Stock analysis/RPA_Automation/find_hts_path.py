# -*- coding: utf-8 -*-
import ctypes
import win32api, win32process, win32gui, win32con
import subprocess

def switch_to_default_desktop():
    try:
        hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F)
        if hwinsta:
            hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF)
            if hdesk:
                ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
                return ret == 1
    except:
        pass
    return False

switch_to_default_desktop()

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

if not wins:
    print("No HTS windows found.")
else:
    for h, t in wins:
        _, pid = win32process.GetWindowThreadProcessId(h)
        print(f"Window: {t} | HWND: {h} | PID: {pid}")
        # Run wmic to get path
        try:
            r = subprocess.run(f'wmic process where "ProcessId={pid}" get ExecutablePath, Name /value', 
                               shell=True, capture_output=True, text=True)
            print(r.stdout.strip())
        except Exception as e:
            print("Wmic error:", e)
