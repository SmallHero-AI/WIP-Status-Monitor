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

def get_process_integrity_level(pid):
    TOKEN_QUERY = 0x0008
    class SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", ctypes.c_ulong)]
    class TOKEN_MANDATORY_LABEL(ctypes.Structure):
        _fields_ = [("Label", SID_AND_ATTRIBUTES)]
        
    hProcess = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid) # PROCESS_QUERY_INFORMATION
    if not hProcess:
        return f"Failed to OpenProcess: {ctypes.windll.kernel32.GetLastError()}"
    
    hToken = ctypes.c_void_p()
    if not ctypes.windll.advapi32.OpenProcessToken(hProcess, TOKEN_QUERY, ctypes.byref(hToken)):
        ctypes.windll.kernel32.CloseHandle(hProcess)
        return f"Failed to OpenProcessToken: {ctypes.windll.kernel32.GetLastError()}"
        
    # Query size
    dwSize = ctypes.c_ulong(0)
    ctypes.windll.advapi32.GetTokenInformation(hToken, 25, None, 0, ctypes.byref(dwSize)) # TokenIntegrityLevel = 25
    
    buf = ctypes.create_string_buffer(dwSize.value)
    if not ctypes.windll.advapi32.GetTokenInformation(hToken, 25, buf, dwSize.value, ctypes.byref(dwSize)):
        ctypes.windll.kernel32.CloseHandle(hToken)
        ctypes.windll.kernel32.CloseHandle(hProcess)
        return "Failed GetTokenInformation"
        
    tml = TOKEN_MANDATORY_LABEL.from_buffer(buf)
    pSubAuthority = ctypes.windll.advapi32.GetSidSubAuthority(tml.Label.Sid, 0)
    dwIntegrityLevel = ctypes.c_ulong.from_address(pSubAuthority).value
    
    ctypes.windll.kernel32.CloseHandle(hToken)
    ctypes.windll.kernel32.CloseHandle(hProcess)
    
    if dwIntegrityLevel == 0x0000:
        return "Untrusted"
    elif dwIntegrityLevel == 0x1000:
        return "Low"
    elif dwIntegrityLevel == 0x2000:
        return "Medium"
    elif dwIntegrityLevel == 0x2100:
        return "Medium Plus"
    elif dwIntegrityLevel == 0x3000:
        return "High (Admin)"
    elif dwIntegrityLevel == 0x4000:
        return "System"
    else:
        return f"Unknown (0x{dwIntegrityLevel:X})"

if switch_to_default_desktop():
    wins = []
    def cb(h, _):
        try:
            t = win32gui.GetWindowText(h)
            if t.strip(): wins.append((h, t))
        except: pass
    win32gui.EnumWindows(cb, None)
    
    for h, t in wins:
        if any(kw in t for kw in ['贏家', 'HTS', 'Kway', 'Winner', '快手', '台新']):
            _, pid = win32process.GetWindowThreadProcessId(h)
            il = get_process_integrity_level(pid)
            print(f"Window: {repr(t)} | PID: {pid} | Integrity Level: {il}")
else:
    print("Failed to switch to Default desktop.")
