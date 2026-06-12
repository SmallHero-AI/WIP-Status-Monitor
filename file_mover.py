import os
import shutil
import time
import datetime
import sys

try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

# 來源資料夾與目的資料夾設定
SOURCE_DIR = r"U:\PCB_QA\IPQC-1(Yuki管理)\IPQC-1\1-各站資料夾\OE\二次顯影\M8"
TARGET_DIR = r"L:\PE\Circuit Process Team\05.工程資料區\二次乾片自檢Picture"
DEFAULT_INTERVAL = 3600  # 預設 1 小時 (3600 秒)

def log(message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")
    sys.stdout.flush()

def get_unique_target_path(target_dir, filename):
    """
    如果目的地已存在相同檔名的檔案，自動在主檔名後加入 _1, _2 等流水號，以防覆蓋。
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    target_path = os.path.join(target_dir, filename)
    while os.path.exists(target_path):
        new_filename = f"{base}_{counter}{ext}"
        target_path = os.path.join(target_dir, new_filename)
        counter += 1
    return target_path

def move_files():
    log("開始進行資料搬移檢查...")
    
    # 檢查來源資料夾是否存在
    if not os.path.exists(SOURCE_DIR):
        log(f"⚠️ 警告: 找不到來源路徑 '{SOURCE_DIR}'，可能是網路磁碟機未連線。將於下一個週期重新嘗試。")
        return
        
    # 檢查目的資料夾是否存在，不存在則自動建立
    if not os.path.exists(TARGET_DIR):
        try:
            os.makedirs(TARGET_DIR)
            log(f"📁 目的地路徑不存在，已自動建立: '{TARGET_DIR}'")
        except Exception as e:
            log(f"❌ 錯誤: 無法建立目的地路徑: {e}")
            return

    try:
        # 使用遞迴尋找來源資料夾中的檔案並進行搬移 (連同子資料夾一併搬移並保留結構)
        success_count = 0
        total_files = 0
        
        # 遍歷來源路徑
        for root, dirs, files in os.walk(SOURCE_DIR):
            # 計算相對於來源根路徑的相對路徑
            rel_path = os.path.relpath(root, SOURCE_DIR)
            if rel_path == ".":
                target_subdir = TARGET_DIR
            else:
                target_subdir = os.path.join(TARGET_DIR, rel_path)
            
            # 確保目的地對應的子資料夾存在
            if not os.path.exists(target_subdir) and files:
                os.makedirs(target_subdir)
                
            # 搬移該目錄下的所有檔案
            for file in files:
                total_files += 1
                src_file_path = os.path.join(root, file)
                dest_file_path = get_unique_target_path(target_subdir, file)
                
                try:
                    # 執行檔案搬移 (跨磁碟機時自動採用 複製+刪除 模式)
                    shutil.move(src_file_path, dest_file_path)
                    display_rel_src = os.path.join(rel_path, file) if rel_path != "." else file
                    display_rel_dest = os.path.relpath(dest_file_path, TARGET_DIR)
                    log(f"✅ 成功搬移: {display_rel_src} -> {display_rel_dest}")
                    success_count += 1
                except Exception as e:
                    log(f"❌ 搬移檔案 {file} 時發生錯誤: {e}")
                    

                
        if total_files == 0:
            log("ℹ️ 來源路徑目前沒有需要搬移的新檔案或資料夾。")
        else:
            log(f"🎉 本次檢查與搬移完成。成功搬移 {success_count}/{total_files} 個檔案（含資料夾結構）。")
            
    except Exception as e:
        log(f"❌ 讀取來源路徑時發生異常錯誤: {e}")

def input_with_timeout(prompt, timeout=10, default=DEFAULT_INTERVAL):
    if not HAS_MSVCRT:
        # 非 Windows 系統時的 Blocking 回退方案 (在此環境基本上用不到)
        print(prompt)
        val_str = input(f"請輸入自訂秒數（無倒數，直接按 Enter 則為預設值 {default} 秒）：").strip()
        if not val_str:
            return default
        try:
            return int(val_str)
        except ValueError:
            return default

    sys.stdout.write(prompt + "\n")
    sys.stdout.flush()
    
    input_chars = []
    start_time = time.time()
    last_sec = -1
    
    while True:
        elapsed = time.time() - start_time
        remaining = int(timeout - elapsed)
        
        if remaining != last_sec:
            if remaining >= 0:
                # \r 回到行首，重新印出包含倒數的提示字與使用者目前輸入的內容
                sys.stdout.write(f"\r請輸入自訂秒數（倒數 {remaining} 秒，未輸入則自動設定為 {default} 秒）：" + "".join(input_chars))
                sys.stdout.flush()
                last_sec = remaining
        
        if elapsed >= timeout:
            sys.stdout.write(f"\n⏱️ 10秒倒數結束！自動設定為預設一小時 ({default} 秒) 搬移一次。\n")
            sys.stdout.flush()
            return default
        
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            # 按下 Enter
            if ch == '\r' or ch == '\n':
                sys.stdout.write("\n")
                sys.stdout.flush()
                val_str = "".join(input_chars).strip()
                if not val_str:
                    return default
                try:
                    val = int(val_str)
                    if val <= 0:
                        print("⚠️ 秒數必須大於 0。使用預設值。")
                        return default
                    return val
                except ValueError:
                    print("⚠️ 輸入非有效整數。使用預設值。")
                    return default
            # 按下 Backspace 退格鍵
            elif ch == '\b':
                if input_chars:
                    input_chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            # 只允許輸入數字
            elif ch.isdigit():
                input_chars.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
        
        time.sleep(0.05)

def main():
    log("==========================================")
    log("      自動資料搬移排程程式已啟動          ")
    log(f"來源路徑: {SOURCE_DIR}")
    log(f"目的路徑: {TARGET_DIR}")
    log("==========================================")
    
    # 詢問使用者自訂檢查間隔時間
    interval = input_with_timeout("⏱️ 設定搬移等待間隔時間...", timeout=10, default=DEFAULT_INTERVAL)
    
    log(f"📢 已設定檢查頻率為: 每 {interval} 秒執行一次")
    log("==========================================")
    
    # 執行一次檢查
    move_files()
    
    while True:
        log(f"⏱️ 進入等待狀態，下一輪檢查將在 {interval} 秒後執行...")
        # 以 1 秒間隔睡眠，支援隨時按 Ctrl+C 退出
        for _ in range(interval):
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                log("👋 偵測到使用者中止指令，正在結束程式。")
                return
        move_files()

if __name__ == "__main__":
    main()
