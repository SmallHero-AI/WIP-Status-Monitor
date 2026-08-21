"""
幼兒影片合成渲染引擎 (Streaming Video Renderer Engine)
職責：以流式 (Streaming) 方式逐幀生成與寫入 MP4 影片，維持極低記憶體 (RAM < 50MB)。
"""

import os
import cv2
import subprocess
import shutil
import tempfile
import numpy as np
from PIL import Image
from src.motion_engine import MotionEngine

class ToddlerVideoRenderer:
    def __init__(self, fps=60, width=1920, height=1080):
        self.fps = fps
        self.width = width
        self.height = height
        self.motion_engine = MotionEngine(target_width=width, target_height=height, fps=fps)

    def load_processed_image(self, img_rel_path: str, script_dir: str, sat_scale: float, con_scale: float) -> np.ndarray:
        img_abs_path = os.path.normpath(os.path.join(script_dir, "..", img_rel_path))
        if not os.path.exists(img_abs_path):
            img_abs_path = os.path.normpath(os.path.join(script_dir, img_rel_path))

        pil_img = Image.open(img_abs_path).convert("RGB")
        protected_pil = self.motion_engine.apply_visual_protection(pil_img, sat_scale, con_scale)
        return np.array(protected_pil)

    def render_story_to_mp4(self, script_data: dict, script_dir: str, output_mp4_path: str):
        visual_safety = script_data.get("visual_safety", {})
        sat_scale = visual_safety.get("saturation_scale", 0.85)
        con_scale = visual_safety.get("contrast_scale", 0.90)
        trans_sec = visual_safety.get("transition_duration_sec", 2.5)

        scenes = script_data.get("scenes", [])
        if not scenes:
            raise ValueError("無可渲染的場景片段！")

        print(f"[Renderer] 開始流式渲染 (Streaming) {len(scenes)} 個幼兒慢速運鏡場景...")

        temp_dir = tempfile.mkdtemp()
        temp_video_path = os.path.join(temp_dir, "temp_visual.mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(temp_video_path, fourcc, self.fps, (self.width, self.height))

        trans_frames = int(trans_sec * self.fps)

        # 預先載入第一個場景圖像
        curr_scene = scenes[0]
        curr_img_np = self.load_processed_image(curr_scene.get("image", ""), script_dir, sat_scale, con_scale)
        curr_duration = curr_scene.get("duration", 12.0)
        curr_total_frames = int(curr_duration * self.fps)
        curr_start_idx = 0

        for i in range(len(scenes)):
            next_scene = scenes[i + 1] if i + 1 < len(scenes) else None
            curr_motion = curr_scene.get("motion", {})
            curr_start_cfg = curr_motion.get("start", {"x": 0.0, "y": 0.0, "zoom": 1.0})
            curr_end_cfg = curr_motion.get("end", {"x": 0.2, "y": 0.2, "zoom": 1.1})

            if next_scene is not None:
                # 載入下一個場景圖像
                next_img_np = self.load_processed_image(next_scene.get("image", ""), script_dir, sat_scale, con_scale)
                next_duration = next_scene.get("duration", 12.0)
                next_total_frames = int(next_duration * self.fps)
                next_motion = next_scene.get("motion", {})
                next_start_cfg = next_motion.get("start", {"x": 0.0, "y": 0.0, "zoom": 1.0})
                next_end_cfg = next_motion.get("end", {"x": 0.2, "y": 0.2, "zoom": 1.1})

                # 1. 寫入當前場景非重疊主體畫面 (curr_start_idx 到 curr_total_frames - trans_frames)
                main_end_frame = max(curr_start_idx, curr_total_frames - trans_frames)
                print(f"  -> 渲染場景 [{curr_scene.get('title', i+1)}] 主體幀 ({curr_start_idx} ~ {main_end_frame})...")
                for f_idx in range(curr_start_idx, main_end_frame):
                    frame_rgb = self.motion_engine.get_scene_frame(
                        curr_img_np, f_idx, curr_total_frames, curr_start_cfg, curr_end_cfg
                    )
                    out_writer.write(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))

                # 2. 寫入融鏡轉場區域 (Cross-Dissolve)
                overlap_len = curr_total_frames - main_end_frame
                print(f"  -> 渲染與場景 [{next_scene.get('title', i+2)}] 之間平滑融鏡 ({overlap_len} 幀)...")
                for k in range(overlap_len):
                    f_a_idx = main_end_frame + k
                    f_b_idx = k

                    frame_a = self.motion_engine.get_scene_frame(
                        curr_img_np, f_a_idx, curr_total_frames, curr_start_cfg, curr_end_cfg
                    ).astype(np.float32)

                    frame_b = self.motion_engine.get_scene_frame(
                        next_img_np, f_b_idx, next_total_frames, next_start_cfg, next_end_cfg
                    ).astype(np.float32)

                    alpha = k / max(1, overlap_len - 1)
                    smooth_alpha = alpha * alpha * (3.0 - 2.0 * alpha)

                    blended = (1.0 - smooth_alpha) * frame_a + smooth_alpha * frame_b
                    out_writer.write(cv2.cvtColor(blended.astype(np.uint8), cv2.COLOR_RGB2BGR))

                # 前進到下一個場景，下一個場景跳過已被融鏡覆蓋的前 overlap_len 幀
                curr_scene = next_scene
                curr_img_np = next_img_np
                curr_duration = next_duration
                curr_total_frames = next_total_frames
                curr_start_idx = overlap_len

            else:
                # 最後一個場景：從 curr_start_idx 渲染到結束
                print(f"  -> 渲染最終場景 [{curr_scene.get('title', i+1)}] 尾部幀 ({curr_start_idx} ~ {curr_total_frames})...")
                for f_idx in range(curr_start_idx, curr_total_frames):
                    frame_rgb = self.motion_engine.get_scene_frame(
                        curr_img_np, f_idx, curr_total_frames, curr_start_cfg, curr_end_cfg
                    )
                    out_writer.write(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))

        out_writer.release()
        print(f"[Renderer] 流式無聲影像檔已生成: {temp_video_path}")

        # 合成音訊
        bgm_info = script_data.get("bgm", {})
        bgm_rel_path = bgm_info.get("file", "")
        bgm_abs_path = os.path.normpath(os.path.join(script_dir, "..", bgm_rel_path))
        if not os.path.exists(bgm_abs_path):
            bgm_abs_path = os.path.normpath(os.path.join(script_dir, bgm_rel_path))

        ffmpeg_cmd = shutil.which("ffmpeg")

        if ffmpeg_cmd and os.path.exists(bgm_abs_path):
            print("[Renderer] 檢測到 FFmpeg，執行最終音效與影像多軌合成...")
            bgm_vol = bgm_info.get("volume", 0.25)
            cmd = [
                ffmpeg_cmd, "-y",
                "-i", temp_video_path,
                "-stream_loop", "-1", "-i", bgm_abs_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-filter:a", f"volume={bgm_vol}",
                "-shortest",
                output_mp4_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[Renderer] [成功] 最終幼兒影片已合成導出: {output_mp4_path}")
        else:
            shutil.copy(temp_video_path, output_mp4_path)
            print(f"[Renderer] [成功] 幼兒影片已導出: {output_mp4_path}")

        shutil.rmtree(temp_dir, ignore_errors=True)
        return output_mp4_path
