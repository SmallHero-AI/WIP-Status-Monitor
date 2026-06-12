import os
import shutil
import time
import datetime
import sys

# 來源資料夾與目的資料夾設定
SOURCE_DIR = r"U:\PCB_QA\IPQC-1(Yuki管理)\IPQC-1\1-各站資料夾\OE\二次顯影\M8"
TARGET_DIR = r"L:\PE\Circuit Process Team\05.工程資料區\二次乾片自檢Picture"
CHECK_INTERVAL_SECONDS = 3600  # 1 小時 (3600 秒)

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
        # 讀取來源資料夾中所有項目
        items = os.listdir(SOURCE_DIR)
        # 篩選出檔案項目 (排除資料夾)
        files_to_move = [f for f in items if os.path.isfile(os.path.join(SOURCE_DIR, f))]
        
        if not files_to_move:
            log("ℹ️ 來源路徑目前沒有需要搬移的新檔案。")
            return
            
        log(f"🔍 發現 {len(files_to_move)} 個新檔案，準備進行搬移...")
        
        success_count = 0
        for filename in files_to_move:
            src_path = os.path.join(SOURCE_DIR, filename)
            dest_path = get_unique_target_path(TARGET_DIR, filename)
            
            try:
                # shutil.move 會自動處理跨磁碟機的複製與刪除
                shutil.move(src_path, dest_path)
                log(f"✅ 成功搬移: {filename} -> {os.path.basename(dest_path)}")
                success_count += 1
            except Exception as e:
                log(f"❌ 搬移檔案 {filename} 時發生錯誤: {e}")
                
        log(f"🎉 本次檢查與搬移完成。成功搬移 {success_count}/{len(files_to_move)} 個檔案。")
        
    except Exception as e:
        log(f"❌ 讀取來源路徑時發生異常錯誤: {e}")

def main():
    log("==========================================")
    log("      自動資料搬移排程程式已啟動          ")
    log(f"來源路徑: {SOURCE_DIR}")
    log(f"目的路徑: {TARGET_DIR}")
    log(f"檢查頻率: 每 {CHECK_INTERVAL_SECONDS / 60:.0f} 分鐘一次")
    log("==========================================")
    
    # 啟動時立刻執行一次檢查
    move_files()
    
    while True:
        log(f"⏱️ 進入等待狀態，下一輪檢查預計在 1 小時後執行...")
        # 使用 1 秒的間隔睡眠，讓使用者可隨時按 Ctrl+C 中斷關閉程式
        for _ in range(CHECK_INTERVAL_SECONDS):
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                log("👋 偵測到使用者中止指令，正在結束程式。")
                return
        move_files()

if __name__ == "__main__":
    main()
