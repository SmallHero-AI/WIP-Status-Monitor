"""
專門幼兒觀看 - 低剪輯頻率與人眼視角影片自動化生成工具 主程式入口 (Main CLI Entry)
"""

import os
import sys
import argparse

# 將專案目錄納入 Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_sample_assets import create_sample_assets
from src.script_validator import run_validation, ToddlerScriptValidator
from src.video_renderer import ToddlerVideoRenderer
import json

def main():
    parser = argparse.ArgumentParser(
        description="專門幼兒觀看之低剪輯頻率與真實人眼視角影片自動化生成工具"
    )
    parser.add_argument("--script", type=str, default="config/sample_story.json", help="故事 JSON 腳本路徑")
    parser.add_argument("--output", type=str, default="toddler_sample_video.mp4", help="輸出 MP4 影片檔名")
    parser.add_argument("--render", action="store_true", help="執行高畫質影片合成渲染")
    parser.add_argument("--validate-only", action="store_true", help="僅執行幼兒視覺安全校驗")
    parser.add_argument("--generate-assets", action="store_true", help="生成示範用柔和圖像與音效素材")

    args = parser.parse_args()

    project_root = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_root, args.script) if not os.path.isabs(args.script) else args.script
    output_path = os.path.join(project_root, args.output) if not os.path.isabs(args.output) else args.output

    # 1. 生成預設示範素材
    print("\n[Step 1] 檢查並生成範例素材...")
    create_sample_assets()

    # 2. 腳本安全性校驗
    print("\n[Step 2] 執行幼兒視覺安全與低剪輯頻率規範校驗...")
    is_valid = run_validation(script_path)
    if not is_valid and args.validate_only:
        print("[!] 腳本未通過幼兒視覺安全校驗，請修正後再嘗試。")
        sys.exit(1)

    if args.validate_only:
        print("[OK] 校驗完成。")
        sys.exit(0)

    # 3. 執行渲染
    print("\n[Step 3] 開始執行高流暢度 1080p/60fps 幼兒影片合成渲染...")
    with open(script_path, 'r', encoding='utf-8') as f:
        script_data = json.load(f)

    renderer = ToddlerVideoRenderer(fps=60, width=1920, height=1080)
    renderer.render_story_to_mp4(
        script_data=script_data,
        script_dir=os.path.dirname(script_path),
        output_mp4_path=output_path
    )

    format_output_path = output_path.replace("\\", "/")
    print(f"\n" + "=" * 60)
    print(f"[SUCCESS] 幼兒專用影片生成完成！檔案儲存於:")
    print(f"   file:///{format_output_path}")
    print(f"提示: 您也可以開啟 preview_dashboard.html 隨時預覽動態鏡頭軌跡與轉場效果！")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
