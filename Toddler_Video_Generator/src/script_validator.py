"""
幼兒視覺安全與低剪輯頻率驗證器 (Toddler Visual Safety Script Validator)
職責：檢查 JSON 故事腳本是否符合幼兒觀看的物理與生理規範。
"""

import os
import json

class ToddlerScriptValidator:
    def __init__(self, min_scene_duration=10.0, min_transition_duration=2.0):
        self.min_scene_duration = min_scene_duration
        self.min_transition_duration = min_transition_duration

    def validate(self, script_path):
        report = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "summary": {}
        }

        if not os.path.exists(script_path):
            report["errors"].append(f"找不到腳本檔案: {script_path}")
            report["is_valid"] = False
            return report

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            report["errors"].append(f"JSON 解析失敗: {str(e)}")
            report["is_valid"] = False
            return report

        # 1. 檢查基本屬性
        title = data.get("title", "未命名故事")
        scenes = data.get("scenes", [])
        visual_safety = data.get("visual_safety", {})

        report["summary"]["title"] = title
        report["summary"]["total_scenes"] = len(scenes)

        if len(scenes) == 0:
            report["errors"].append("腳本中包含 0 個場景！")
            report["is_valid"] = False
            return report

        # 2. 檢查幼兒視覺保護設定
        min_sec = visual_safety.get("min_scene_duration_sec", self.min_scene_duration)
        trans_sec = visual_safety.get("transition_duration_sec", self.min_transition_duration)
        sat_scale = visual_safety.get("saturation_scale", 1.0)

        if sat_scale > 0.95:
            report["warnings"].append(
                f"建議將色彩飽和度 (saturation_scale={sat_scale}) 調至 0.85-0.90，避免高彩度強烈刺激幼兒眼神。"
            )

        # 3. 逐一檢查場景與鏡頭秒數
        total_duration = 0.0
        script_dir = os.path.dirname(script_path)

        for idx, scene in enumerate(scenes):
            scene_id = scene.get("id", f"scene_{idx+1}")
            duration = scene.get("duration", 0.0)
            total_duration += duration

            # 檢查單一鏡頭切換頻率
            if duration < min_sec:
                report["errors"].append(
                    f"[{scene_id}] 鏡頭秒數過短 ({duration}s < 規範最小值 {min_sec}s)。幼兒影片運鏡必須緩慢專注，防止剪輯頻率過高！"
                )
                report["is_valid"] = False
            elif duration < 12.0:
                report["warnings"].append(
                    f"[{scene_id}] 鏡頭秒數為 {duration}s，對於 0-2 歲幼兒建議拉長至 12-15 秒以上。"
                )

            # 檢查運動軌跡 (Motion)
            motion = scene.get("motion", {})
            if motion.get("easing") != "ease_in_out":
                report["warnings"].append(
                    f"[{scene_id}] 建議將運鏡曲線改為 'ease_in_out' 以模擬人眼平緩觀察轉向。"
                )

            # 檢查圖片檔案是否存在 (相對於腳本或專案根目錄)
            img_rel_path = scene.get("image", "")
            img_abs_path = os.path.normpath(os.path.join(script_dir, "..", img_rel_path))
            if not os.path.exists(img_abs_path) and not os.path.exists(img_rel_path):
                report["errors"].append(f"[{scene_id}] 素材圖片檔案不存在: {img_rel_path}")
                report["is_valid"] = False

        report["summary"]["total_video_duration_sec"] = total_duration
        report["summary"]["avg_scene_duration_sec"] = total_duration / len(scenes) if scenes else 0

        return report

def run_validation(script_path):
    validator = ToddlerScriptValidator()
    report = validator.validate(script_path)
    print("=" * 60)
    print(f"幼兒視覺安全腳本校驗報告: {report['summary'].get('title', '')}")
    print("=" * 60)
    print(f"結果: {'[通過 PASS]' if report['is_valid'] else '[未通過 FAIL]'}")
    print(f"總場景數: {report['summary'].get('total_scenes', 0)}")
    print(f"預估影片總長度: {report['summary'].get('total_video_duration_sec', 0):.1f} 秒")
    print(f"平均單鏡頭停留時間: {report['summary'].get('avg_scene_duration_sec', 0):.1f} 秒")

    if report["warnings"]:
        print("\n[黃色警告/優化建議]:")
        for w in report["warnings"]:
            print(f"  - {w}")

    if report["errors"]:
        print("\n[紅色嚴肅違規/錯誤]:")
        for e in report["errors"]:
            print(f"  - {e}")

    print("=" * 60)
    return report["is_valid"]

if __name__ == "__main__":
    import sys
    script = sys.argv[1] if len(sys.argv) > 1 else "e:/G-AI-1/Toddler_Video_Generator/config/sample_story.json"
    run_validation(script)
