"""
人眼 Ease-in-out 運鏡軌跡與圖像防過度刺激處理器 (Memory-Optimized Engine)
職責：
1. 計算符合人眼追蹤視覺特性的 Ease-In-Out 漸變運動曲線。
2. 對圖片進行防強光、防過度刺激的彩度與對比度軟化調控。
3. 採用 Generator (yield) 逐幀流式生成，避免幾十 GB 記憶體暴增。
"""

import numpy as np
import cv2
from PIL import Image, ImageEnhance

class MotionEngine:
    def __init__(self, target_width=1920, target_height=1080, fps=60):
        self.target_width = target_width
        self.target_height = target_height
        self.fps = fps

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """
        Cubic Ease-In-Out 曲線公式 (0.0 -> 1.0)
        """
        t = max(0.0, min(1.0, t))
        if t < 0.5:
            return 4.0 * t * t * t
        else:
            p = (2.0 * t - 2.0)
            return 0.5 * p * p * p + 1.0

    def apply_visual_protection(self, image_pil: Image.Image, saturation_scale=0.85, contrast_scale=0.90) -> Image.Image:
        """
        幼兒視覺保護過濾器：彩度與對比度調柔
        """
        enhancer_sat = ImageEnhance.Color(image_pil)
        img_soft = enhancer_sat.enhance(saturation_scale)

        enhancer_con = ImageEnhance.Contrast(img_soft)
        img_soft = enhancer_con.enhance(contrast_scale)

        return img_soft

    def render_motion_frame(self, image_np: np.ndarray, progress: float, start_config: dict, end_config: dict) -> np.ndarray:
        """
        根據進度 progress (0.0 到 1.0)，計算目前畫面幀之視角 Pan & Zoom
        """
        e_t = self.ease_in_out_cubic(progress)

        start_x, start_y, start_z = start_config.get('x', 0.0), start_config.get('y', 0.0), start_config.get('zoom', 1.0)
        end_x, end_y, end_z = end_config.get('x', 0.0), end_config.get('y', 0.0), end_config.get('zoom', 1.0)

        curr_x = start_x + (end_x - start_x) * e_t
        curr_y = start_y + (end_y - start_y) * e_t
        curr_z = start_z + (end_z - start_z) * e_t

        img_h, img_w = image_np.shape[:2]

        crop_w = int(img_w / curr_z)
        crop_h = int(img_h / curr_z)

        max_offset_x = img_w - crop_w
        max_offset_y = img_h - crop_h

        offset_x = int(curr_x * max_offset_x)
        offset_y = int(curr_y * max_offset_y)

        offset_x = max(0, min(offset_x, max_offset_x))
        offset_y = max(0, min(offset_y, max_offset_y))

        cropped = image_np[offset_y:offset_y + crop_h, offset_x:offset_x + crop_w]

        rendered_frame = cv2.resize(cropped, (self.target_width, self.target_height), interpolation=cv2.INTER_CUBIC)
        return rendered_frame

    def get_scene_frame(self, image_np: np.ndarray, frame_idx: int, total_frames: int, start_config: dict, end_config: dict) -> np.ndarray:
        progress = frame_idx / max(1, total_frames - 1)
        return self.render_motion_frame(image_np, progress, start_config, end_config)
