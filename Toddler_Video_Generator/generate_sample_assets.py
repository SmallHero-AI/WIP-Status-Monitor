"""
輔助腳本：自動生成示範用柔和圖像與背景音效素材 (Pastel Images & Soft BGM)
"""

import os
import math
import wave
import struct
from PIL import Image, ImageDraw, ImageFilter

def create_sample_assets():
    assets_dir = "e:/G-AI-1/Toddler_Video_Generator/sample_assets"
    os.makedirs(assets_dir, exist_ok=True)
    width, height = 1920, 1080

    # 1. Scene 1: Forest (柔和晨光綠意)
    img1 = Image.new("RGB", (width, height), (220, 240, 225))
    draw1 = ImageDraw.Draw(img1)
    # 畫圓形與樹木意象
    draw1.ellipse([100, 100, 500, 500], fill=(255, 250, 210)) # 太陽
    draw1.rectangle([0, 700, width, height], fill=(160, 205, 170)) # 草地
    draw1.polygon([(400, 300), (200, 800), (600, 800)], fill=(120, 175, 135)) # 樹木1
    draw1.polygon([(1100, 250), (850, 850), (1350, 850)], fill=(100, 160, 120)) # 樹木2
    draw1.polygon([(1600, 350), (1400, 800), (1800, 800)], fill=(130, 185, 145)) # 樹木3
    # 模糊高斯處理，使視覺更為圓潤柔和
    img1 = img1.filter(ImageFilter.GaussianBlur(radius=3))
    img1.save(os.path.join(assets_dir, "scene1_forest.png"))

    # 2. Scene 2: Meadow (柔和藍天花園)
    img2 = Image.new("RGB", (width, height), (225, 240, 255))
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([0, 650, width, height], fill=(200, 225, 180)) # 草地
    # 雲朵
    draw2.ellipse([300, 200, 600, 350], fill=(255, 255, 255))
    draw2.ellipse([450, 180, 750, 360], fill=(255, 255, 255))
    draw2.ellipse([1200, 220, 1600, 380], fill=(255, 255, 255))
    # 花朵意象
    for x in [300, 600, 900, 1200, 1500]:
        draw2.ellipse([x, 750, x+80, 830], fill=(255, 200, 210))
        draw2.ellipse([x+25, 775, x+55, 805], fill=(255, 240, 150))
    img2 = img2.filter(ImageFilter.GaussianBlur(radius=3))
    img2.save(os.path.join(assets_dir, "scene2_meadow.png"))

    # 3. Scene 3: Sunset (柔和粉橙黃昏)
    img3 = Image.new("RGB", (width, height), (255, 225, 215))
    draw3 = ImageDraw.Draw(img3)
    draw3.ellipse([800, 450, 1100, 750], fill=(255, 235, 170)) # 黃昏落日
    draw3.rectangle([0, 750, width, height], fill=(210, 165, 175)) # 山丘
    draw3.polygon([(0, 600), (500, 800), (0, 900)], fill=(190, 145, 160))
    draw3.polygon([(1400, 650), (1920, 600), (1920, 900)], fill=(180, 135, 150))
    img3 = img3.filter(ImageFilter.GaussianBlur(radius=3))
    img3.save(os.path.join(assets_dir, "scene3_sunset.png"))

    # 4. Generate Soft Ambient BGM (WAV audio saved as MP3/WAV)
    bgm_path = os.path.join(assets_dir, "background_soft_music.wav")
    sample_rate = 44100
    duration_sec = 40
    n_samples = sample_rate * duration_sec

    with wave.open(bgm_path, 'w') as wav_file:
        wav_file.setnchannels(1) # mono
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)
        
        # 產生安撫頻率的正弦波音符和弦 (432Hz 緩和音階)
        notes = [261.63, 329.63, 392.00, 523.25] # C4, E4, G4, C5
        data = []
        for i in range(n_samples):
            t = i / sample_rate
            # 每 4 秒更換和絃音
            note_idx = int(t / 4) % len(notes)
            freq = notes[note_idx]
            
            # 主音 + 極柔和低八度泛音
            val = 0.5 * math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * (freq/2) * t)
            
            # 淡入淡出包絡線
            envelope = min(1.0, t / 3.0) * min(1.0, (duration_sec - t) / 3.0)
            sample_val = int(val * envelope * 8000) # 低音量
            data.append(struct.pack('<h', sample_val))
            
        wav_file.writeframes(b''.join(data))

    print(f"[OK] 示範素材已成功生成至: {assets_dir}")

if __name__ == "__main__":
    create_sample_assets()
