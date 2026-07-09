# -*- coding: utf-8 -*-
import ctypes
import win32api, win32process, win32gui, win32con

def switch_to_default_desktop():
    h_winsta = ctypes.windll.user32.GetProcessWindowStation()
    hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F) # WINSTA_ALL_ACCESS
    if hwinsta:
        hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF) # DESKTOP_ALL_ACCESS
        if hdesk:
            ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
            return ret == 1
    return False

if switch_to_default_desktop():
    print("Successfully switched to Default desktop!")
    
    # Let's list top-level windows
    wins = []
    def cb(h, _):
        try:
            t = win32gui.GetWindowText(h)
            if t.strip():
                wins.append((h, t))
        except: pass
    win32gui.EnumWindows(cb, None)
    
    print(f"Found {len(wins)} windows.")
    print("Searching for HTS/Winner...")
    found_hts = False
    for h, t in wins:
        if any(kw in t for kw in ['贏家', 'HTS', 'Kway', 'Winner', '快手', '台新']):
            rect = win32gui.GetWindowRect(h)
            print(f"Found target window: {repr(t)} (hwnd={h}) at {rect}")
            found_hts = True
    if not found_hts:
        print("Target window not found on Default desktop.")
else:
    print("Failed to switch to Default desktop.")
