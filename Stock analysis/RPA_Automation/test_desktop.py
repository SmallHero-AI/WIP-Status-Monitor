# -*- coding: utf-8 -*-
import ctypes
import win32api, win32process, win32gui

def get_desktop_winsta():
    try:
        # GetProcessWindowStation
        h_winsta = ctypes.windll.user32.GetProcessWindowStation()
        # GetThreadDesktop
        h_desk = ctypes.windll.user32.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
        
        # Get window station name
        winsta_name = ctypes.create_string_buffer(256)
        ctypes.windll.user32.GetUserObjectInformationA(h_winsta, 2, winsta_name, 256, None)
        
        # Get desktop name
        desk_name = ctypes.create_string_buffer(256)
        ctypes.windll.user32.GetUserObjectInformationA(h_desk, 2, desk_name, 256, None)
        
        return winsta_name.value.decode('utf-8', errors='replace'), desk_name.value.decode('utf-8', errors='replace')
    except Exception as e:
        return "Error", str(e)

winsta, desk = get_desktop_winsta()
print("Window Station:", winsta)
print("Desktop:", desk)

# Try to open WinSta0\Default
try:
    hwinsta = ctypes.windll.user32.OpenWindowStationA(b"WinSta0", False, 0x37F) # WINSTA_ALL_ACCESS
    if hwinsta:
        print("Successfully opened WinSta0")
        hdesk = ctypes.windll.user32.OpenDesktopA(b"Default", 0, False, 0x1FF) # DESKTOP_ALL_ACCESS
        if hdesk:
            print("Successfully opened Default desktop")
            # Set thread desktop
            ret = ctypes.windll.user32.SetThreadDesktop(hdesk)
            print("SetThreadDesktop ret:", ret)
            
            # Now try SetCursorPos
            try:
                import win32api
                win32api.SetCursorPos((500, 500))
                print("SetCursorPos succeeded after switching thread desktop!")
            except Exception as ex:
                print("SetCursorPos failed after switching:", ex)
        else:
            print("Failed to open Default desktop, error:", ctypes.windll.kernel32.GetLastError())
    else:
        print("Failed to open WinSta0, error:", ctypes.windll.kernel32.GetLastError())
except Exception as e:
    print("Desktop switch exception:", e)
