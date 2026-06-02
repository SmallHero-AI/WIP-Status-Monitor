from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os
import glob
from threading import Thread
import time
import datetime
import sys
import ctypes
from ctypes import wintypes
import shutil

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False

# Win32 API for fallback folder selection
class BROWSEINFO(ctypes.Structure):
    _fields_ = [
        ("hwndOwner", wintypes.HWND),
        ("pidlRoot", wintypes.LPVOID),
        ("pszDisplayName", ctypes.c_wchar_p),
        ("lpszTitle", ctypes.c_wchar_p),
        ("ulFlags", wintypes.UINT),
        ("lpfn", wintypes.LPVOID),
        ("lParam", wintypes.LPARAM),
        ("iImage", ctypes.c_int),
    ]

def win32_select_directory(title):
    try:
        BIF_RETURNONLYFSDIRS = 0x0001
        BIF_NEWDIALOGSTYLE = 0x0040
        bi = BROWSEINFO()
        bi.lpszTitle = title
        bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
        pidl = ctypes.windll.shell32.SHBrowseForFolderW(ctypes.byref(bi))
        if pidl:
            path = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetPathFromIDListW(pidl, path)
            ctypes.windll.ole32.CoTaskMemFree(pidl)
            return path.value
        return None
    except:
        return None

def win32_msg_yes_no(title, message):
    MB_YESNO = 0x00000004
    MB_ICONQUESTION = 0x00000020
    IDYES = 6
    res = ctypes.windll.user32.MessageBoxW(0, message, title, MB_YESNO | MB_ICONQUESTION)
    return res == IDYES

def prompt_config():
    default_analysis = r"U:\PCB_PRE\PRE-共用表格與資料\各工程師資料區\毓茜\WIP-4月"
    default_source = r"L:\PC 資料\SALES\WIP Status"
    
    if HAS_TK:
        try:
            # We will create a temporary/hidden root window to ask the Yes/No question
            root = tk.Tk()
            root.withdraw()
            
            use_default = messagebox.askyesno(
                "WIP Monitor v1.8 配置",
                "是否使用預設分析路徑與自動複製母檔？\n\n"
                f"預設分析路徑：{default_analysis}\n"
                f"預設原始路徑：{default_source}"
            )
            
            if use_default:
                root.destroy()
                return {
                    "analysis": default_analysis,
                    "sync": True,
                    "source": default_source
                }
            
            # If No, continue with original UI
            root.deiconify()
            config = {"analysis": "", "sync": False, "source": ""}
            root.title("WIP Monitor v1.8 配置")
            root.geometry("550x350")
            root.attributes('-topmost', True)
            
            # Default paths for manual input (as in original v1.7)
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            def_analysis = os.path.join(base_dir, 'WIP Status')
            if not os.path.exists(def_analysis):
                def_analysis = r'E:\G-AI-1\WIP Status'

            # UI Elements
            tk.Label(root, text="1. WIP Status 分析路徑 (讀取 Excel 進行分析的地方):", font=("Arial", 10, "bold")).pack(pady=(15,0), anchor="w", padx=20)
            analysis_var = tk.StringVar(value=def_analysis)
            f1 = tk.Frame(root)
            f1.pack(fill="x", padx=20, pady=5)
            tk.Entry(f1, textvariable=analysis_var).pack(side="left", expand=True, fill="x")
            def browse_analysis():
                path = filedialog.askdirectory()
                if path: analysis_var.set(path)
            tk.Button(f1, text="瀏覽...", command=browse_analysis).pack(side="right", padx=(5,0))
            
            tk.Label(root, text="------------------------------------------------------------------").pack()

            sync_var = tk.BooleanVar(value=False)
            tk.Checkbutton(root, text="2. 是否固定時間從原始路徑抓取資料?", variable=sync_var, font=("Arial", 10, "bold"), fg="#0891b2").pack(pady=5, anchor="w", padx=20)
            
            tk.Label(root, text="3. WIP Status 原始資料路徑 (Server 來源):", font=("Arial", 10)).pack(anchor="w", padx=20)
            source_var = tk.StringVar(value="")
            f2 = tk.Frame(root)
            f2.pack(fill="x", padx=20, pady=5)
            tk.Entry(f2, textvariable=source_var).pack(side="left", expand=True, fill="x")
            def browse_source():
                path = filedialog.askdirectory()
                if path: source_var.set(path)
            tk.Button(f2, text="瀏覽...", command=browse_source).pack(side="right", padx=(5,0))
            
            def on_start():
                config["analysis"] = analysis_var.get()
                config["sync"] = sync_var.get()
                config["source"] = source_var.get()
                root.destroy()
                
            tk.Button(root, text="🚀 開始監控系統", command=on_start, height=2, width=25, bg="#22d3ee", font=("Arial", 10, "bold")).pack(pady=25)
            
            root.mainloop()
            return config
        except Exception as e:
            print(f"GUI prompt failed: {e}")
            # Fall through to ctypes
    
    # Native Win32 Fallback (No tkinter required)
    config = {"analysis": "", "sync": False, "source": ""}
    print("Tkinter not found. Using native Win32 dialogs...")
    
    use_default = win32_msg_yes_no(
        "WIP Monitor v1.8 配置",
        "是否使用預設分析路徑與自動複製母檔？\n\n"
        f"預設分析路徑：{default_analysis}\n"
        f"預設原始路徑：{default_source}"
    )
    if use_default:
        return {
            "analysis": default_analysis,
            "sync": True,
            "source": default_source
        }
    
    config["analysis"] = win32_select_directory("1. 請選擇 WIP Status 分析路徑 (讀取 Excel 進行分析的地方)")
    if not config["analysis"]: return None
    
    config["sync"] = win32_msg_yes_no("WIP Monitor v1.8 配置", "2. 是否啟動「自動抓取資料」功能？\n(將定期從原始路徑複製最新檔案)")
    
    if config["sync"]:
        config["source"] = win32_select_directory("3. 請選擇 WIP Status 原始資料路徑 (來源 Server)")
        if not config["source"]: return None
        
    return config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

config = prompt_config()
if config:
    ANALYSIS_FOLDER = config["analysis"]
    AUTO_SYNC = config["sync"]
    SOURCE_FOLDER = config["source"]
else:
    # Fallback
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    ANALYSIS_FOLDER = os.path.join(base_dir, 'WIP Status')
    AUTO_SYNC = False
    SOURCE_FOLDER = ""

if not os.path.exists(ANALYSIS_FOLDER):
    ANALYSIS_FOLDER = r'E:\G-AI-1\WIP Status'

cached_data = {"cities": [], "last_update": "", "file_name": ""}
global_df = None

PROCESS_ORDER = ["DF", "ET", "AOI", "ML1", "ML2", "LD", "NC", "CU", "KE", "AH", "RT", "MK", "OS", "VI", "PK"]

GEO_MAP = {
    "DF": {"name": "Yilan", "lat": 24.7021, "lng": 121.7377},
    "ET": {"name": "Keelung", "lat": 25.1283, "lng": 121.7419},
    "AOI": {"name": "Taipei", "lat": 25.0330, "lng": 121.5654},
    "ML1": {"name": "Taoyuan", "lat": 24.9936, "lng": 121.3010},
    "ML2": {"name": "Miaoli", "lat": 24.8138, "lng": 120.9675},
    "LD": {"name": "Hsinchu", "lat": 24.5601, "lng": 120.8209},
    "NC": {"name": "Taichung", "lat": 24.1477, "lng": 120.6736},
    "CU": {"name": "Yunlin", "lat": 23.7092, "lng": 120.4313},
    "KE": {"name": "Chiayi", "lat": 23.4800, "lng": 120.4500},
    "AH": {"name": "Tainan", "lat": 22.9997, "lng": 120.2270},
    "RT": {"name": "Kaohsiung", "lat": 22.6273, "lng": 120.3014},
    "MK": {"name": "Pingtung", "lat": 21.9015, "lng": 120.7454},
    "OS": {"name": "Taitung", "lat": 22.7583, "lng": 121.1444},
    "VI": {"name": "Hualien", "lat": 23.9871, "lng": 121.6016},
    "PK": {"name": "Nantou", "lat": 23.9739, "lng": 120.9777},
    "LAB": {"name": "Green Island", "lat": 22.6609, "lng": 121.4925},
    "QA": {"name": "Penghu", "lat": 23.5711, "lng": 119.5793}
}

def analyze_latest_file():
    global cached_data, global_df
    cycle = 0
    while True:
        cycle += 1
        now_str = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"\n[Cycle {cycle}] {now_str} | AUTO_SYNC={AUTO_SYNC} | SOURCE={SOURCE_FOLDER}")
        try:
            # Step 0: Auto-Sync if enabled
            if AUTO_SYNC and SOURCE_FOLDER and os.path.exists(SOURCE_FOLDER):
                source_files = glob.glob(os.path.join(SOURCE_FOLDER, "*.xls"))
                print(f"  [Sync] Found {len(source_files)} source files")
                if source_files:
                    latest_source = max(source_files, key=os.path.getmtime)
                    target_path = os.path.join(ANALYSIS_FOLDER, os.path.basename(latest_source))
                    
                    should_copy = False
                    if not os.path.exists(target_path):
                        should_copy = True
                        print(f"  [Sync] Target missing -> will copy: {os.path.basename(latest_source)}")
                    else:
                        src_mt = os.path.getmtime(latest_source)
                        tgt_mt = os.path.getmtime(target_path)
                        if src_mt > tgt_mt + 2:
                            should_copy = True
                            print(f"  [Sync] Source newer ({src_mt:.0f} > {tgt_mt:.0f}) -> will copy")
                        else:
                            print(f"  [Sync] Target up-to-date, skip copy")
                            
                    if should_copy:
                        shutil.copy2(latest_source, target_path)
                        print(f"  [Sync] Copied: {os.path.basename(latest_source)}")
            else:
                print(f"  [Sync] Skipped (AUTO_SYNC={AUTO_SYNC})")

            files = glob.glob(os.path.join(ANALYSIS_FOLDER, "*.xls"))
            print(f"  [Analyze] Found {len(files)} analysis files")
            if files:
                latest_file = max(files, key=os.path.getmtime)
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime('%Y-%m-%d %H:%M:%S')
                
                if cached_data.get("last_update") != file_mtime:
                    print(f"  [Analyze] NEW data detected! mtime={file_mtime}, file={os.path.basename(latest_file)}")
                    df = pd.read_excel(latest_file)
                    global_df = df.copy()
                    df['city_code'] = df['make_deptment_code'].astype(str)
                    
                    result = []
                    for dept_code, dept_df in df.groupby('city_code'):
                        info = GEO_MAP.get(dept_code, {"lat": 23.69, "lng": 120.96})
                        stations = []
                        for st_code, st_df in dept_df.groupby('station_code'):
                            customer_stats = []
                            for eng_num, c_df in st_df.groupby('eng_num'):
                                wpnl_sum = pd.to_numeric(c_df.get('wpnl_qty', 0), errors='coerce').fillna(0).sum()
                                stay_times = pd.to_numeric(c_df.get('停留時間', 0), errors='coerce').fillna(0)
                                if len(stay_times) > 0:
                                    max_idx = stay_times.idxmax()
                                    max_stay = float(stay_times[max_idx])
                                    max_rc = str(c_df.loc[max_idx, 'run_card']) if 'run_card' in c_df.columns else ''
                                else:
                                    max_stay = 0.0
                                    max_rc = ''
                                cust_category = str(c_df['客戶別'].iloc[0]).strip() if '客戶別' in c_df.columns else ""
                                
                                run_cards_detail = []
                                for _, row in c_df.iterrows():
                                    rc_code = str(row.get('run_card', ''))
                                    rc_wpnl = int(pd.to_numeric(row.get('wpnl_qty', 0), errors='coerce')) if not pd.isna(row.get('wpnl_qty')) else 0
                                    rc_stay = float(pd.to_numeric(row.get('停留時間', 0), errors='coerce')) if not pd.isna(row.get('停留時間')) else 0.0
                                    
                                    raw_fast = row.get('是否快單') if '是否快單' in c_df.columns else ''
                                    fast_type = str(raw_fast).strip() if not pd.isna(raw_fast) else ""
                                    fast_level = ""
                                    if "A" in fast_type: fast_level = "A"
                                    elif "B" in fast_type: fast_level = "B"
                                    elif "C" in fast_type: fast_level = "C"
                                    elif "D" in fast_type: fast_level = "D"
                                    
                                    run_cards_detail.append({
                                        "run_card": rc_code,
                                        "wpnl_qty": rc_wpnl,
                                        "stay_time": rc_stay,
                                        "fast_level": fast_level,
                                        "fast_type": fast_type
                                    })
                                
                                is_fast = any(rc["fast_level"] != "" for rc in run_cards_detail)
                                highest_fast_level = ""
                                if any(rc["fast_level"] == "A" for rc in run_cards_detail): highest_fast_level = "A"
                                elif any(rc["fast_level"] == "B" for rc in run_cards_detail): highest_fast_level = "B"
                                elif any(rc["fast_level"] == "C" for rc in run_cards_detail): highest_fast_level = "C"
                                elif any(rc["fast_level"] == "D" for rc in run_cards_detail): highest_fast_level = "D"

                                customer_stats.append({
                                    "eng_num": str(eng_num),
                                    "category": cust_category,
                                    "run_card_count": len(c_df),
                                    "wpnl_qty": int(wpnl_sum),
                                    "max_stay_time": max_stay,
                                    "max_stay_run_card": max_rc,
                                    "is_fast": is_fast,
                                    "highest_fast_level": highest_fast_level,
                                    "run_cards_detail": run_cards_detail
                                })
                            stations.append({
                                "station_code": str(st_code),
                                "count": len(st_df),
                                "customers": st_df['eng_num'].unique().tolist(),
                                "customer_stats": customer_stats
                            })
                        
                        is_mainline = dept_code in PROCESS_ORDER
                        order = PROCESS_ORDER.index(dept_code) if is_mainline else 999
                        result.append({
                            "city_code": str(dept_code),
                            "city_name": str(dept_code),
                            "lat": info["lat"],
                            "lng": info["lng"],
                            "total_customers": len(dept_df),
                            "is_mainline": is_mainline,
                            "order": order,
                            "stations": stations
                        })
                    
                    result.sort(key=lambda x: x["order"])
                    cached_data = {
                        "cities": result,
                        "last_update": file_mtime,
                        "file_name": os.path.basename(latest_file)
                    }
                    print(f"  [Analyze] Updated cached_data with {len(result)} cities")
                else:
                    print(f"  [Analyze] No change (mtime={file_mtime} matches cache)")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        print(f"  [Sleep] Waiting 60s...")
        time.sleep(60)

Thread(target=analyze_latest_file, daemon=True).start()

@app.get("/api/status")
async def get_status():
    return cached_data

@app.get("/api/customer/{eng_num}")
async def get_customer(eng_num: str, city_code: str = None):
    if global_df is None: return {"error": "Data not ready"}
    try:
        df_query = global_df.copy()
        df_query['eng_num_str'] = df_query['eng_num'].astype(str).str.strip()
        customer_rows = df_query[df_query['eng_num_str'] == eng_num.strip()]
        if city_code:
            customer_rows = customer_rows[customer_rows['make_deptment_code'].astype(str) == city_code]
        if customer_rows.empty: return []
        customer_rows = customer_rows.drop(columns=['eng_num_str'])
        import numpy as np
        customer_rows = customer_rows.replace([np.inf, -np.inf], np.nan).fillna("")
        customer_rows = customer_rows.astype(str)
        return customer_rows.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

if getattr(sys, 'frozen', False):
    static_dir = os.path.join(sys._MEIPASS, "dist")
else:
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wip-monitor-web", "dist")

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    from threading import Timer
    Timer(1.5, lambda: webbrowser.open("http://localhost:8000")).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
